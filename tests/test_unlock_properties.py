"""
UnlockService のプロパティベーステスト

hypothesis を使用して、パスワード解除機能の正当性を検証します。

**Feature: docker-excel-unlocker**
**Validates: Requirements 1.1, 1.2, 1.3, 1.6**
"""

import io
import os
import tempfile
from pathlib import Path
from typing import Optional

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from app.services.storage_service import LocalStorageService
from app.services.unlock_service import UnlockService, ErrorMessages
from tests.conftest import TEST_DATA_DIR, TEST_PASSWORD, TEST_FILES


# ASCII 文字のみを使用するストラテジー（ファイルシステム互換性のため）
ASCII_TEXT = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        whitelist_characters='_-',
        max_codepoint=127  # ASCII のみ
    ),
    min_size=1,
    max_size=20
)


# =============================================================================
# テストデータとヘルパー
# =============================================================================

def get_encrypted_test_files() -> list[Path]:
    """利用可能な暗号化テストファイルのリストを取得"""
    return [TEST_DATA_DIR / f for f in TEST_FILES if (TEST_DATA_DIR / f).exists()]


def create_unencrypted_xlsx() -> bytes:
    """
    パスワード保護されていない最小限の xlsx ファイルを生成
    
    xlsx は実際には ZIP 形式なので、最小限の構造を持つ ZIP を作成
    """
    import zipfile
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 最小限の xlsx 構造
        # [Content_Types].xml
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
</Types>'''
        zf.writestr('[Content_Types].xml', content_types)
        
        # _rels/.rels
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels)
        
        # xl/workbook.xml
        workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets>
</workbook>'''
        zf.writestr('xl/workbook.xml', workbook)
        
        # xl/_rels/workbook.xml.rels
        wb_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''
        zf.writestr('xl/_rels/workbook.xml.rels', wb_rels)
        
        # xl/worksheets/sheet1.xml
        sheet = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData/>
</worksheet>'''
        zf.writestr('xl/worksheets/sheet1.xml', sheet)
    
    buffer.seek(0)
    return buffer.read()


# =============================================================================
# Property 1: パスワード解除の成功条件
# =============================================================================

class TestProperty1PasswordUnlockSuccess:
    """
    **Feature: docker-excel-unlocker, Property 1: パスワード解除の成功条件**
    
    *For any* 暗号化された Excel ファイルと正しいパスワードを含むパスワードリストに対して、
    解除処理は成功し、downloadUrl を含むレスポンスを返す
    
    **Validates: Requirements 1.1, 1.2**
    """
    
    @settings(max_examples=100)
    @given(
        file_index=st.integers(min_value=0, max_value=len(TEST_FILES) - 1),
        use_second_password=st.booleans(),
        wrong_password_prefix=ASCII_TEXT
    )
    def test_unlock_succeeds_with_correct_password(
        self,
        file_index: int,
        use_second_password: bool,
        wrong_password_prefix: str
    ):
        """
        **Feature: docker-excel-unlocker, Property 1: パスワード解除の成功条件**
        
        正しいパスワードがリストに含まれていれば、解除は成功する。
        - 第1パスワードが正しい場合
        - 第2パスワードが正しい場合（第1が不正でも）
        
        **Validates: Requirements 1.1, 1.2**
        """
        # テストファイルの存在確認
        test_files = get_encrypted_test_files()
        assume(len(test_files) > 0)
        assume(file_index < len(test_files))
        
        test_file_path = test_files[file_index]
        
        # 一時ディレクトリで実行（各テストケースで独立）
        with tempfile.TemporaryDirectory() as temp_dir:
            # Storage と UnlockService を作成
            storage = LocalStorageService(base_dir=temp_dir, expiry_seconds=300)
            unlock_service = UnlockService(storage=storage)
        
            # テストファイルを保存
            with open(test_file_path, "rb") as f:
                file_id, _ = storage.save(f, test_file_path.name)
            
            # パスワードの設定
            if use_second_password:
                # 第1パスワードは不正、第2パスワードが正しい
                # wrong_password_prefix が TEST_PASSWORD と同じにならないようにする
                wrong_pw = f"{wrong_password_prefix}_wrong"
                assume(wrong_pw != TEST_PASSWORD)
                password1 = wrong_pw
                password2 = TEST_PASSWORD
            else:
                # 第1パスワードが正しい
                password1 = TEST_PASSWORD
                password2 = None
            
            # 解除を実行
            result = unlock_service.unlock(file_id, password1, password2)
            
            # プロパティの検証: 正しいパスワードがあれば成功する
            assert result["success"] is True, \
                f"正しいパスワードで解除に失敗: {result['message']}"
            assert result["unlocked_file_id"] is not None, \
                "解除成功時は unlocked_file_id が返される"
            assert result["message"] is None, \
                "解除成功時は message は None"
            assert "_解除" in result["unlocked_filename"], \
                "解除後のファイル名には '_解除' が含まれる"


# =============================================================================
# Property 2: パスワード不正時のエラーメッセージ
# =============================================================================

class TestProperty2IncorrectPasswordError:
    """
    **Feature: docker-excel-unlocker, Property 2: パスワード不正時のエラーメッセージ**
    
    *For any* 暗号化された Excel ファイルと不正なパスワードのみを含むリストに対して、
    解除処理は「パスワードが正しくありません」というエラーメッセージを返す
    
    **Validates: Requirements 1.3**
    """
    
    @settings(max_examples=100)
    @given(
        file_index=st.integers(min_value=0, max_value=len(TEST_FILES) - 1),
        wrong_password1=ASCII_TEXT,
        wrong_password2=st.one_of(st.none(), ASCII_TEXT)
    )
    def test_unlock_fails_with_wrong_password(
        self,
        file_index: int,
        wrong_password1: str,
        wrong_password2: Optional[str]
    ):
        """
        **Feature: docker-excel-unlocker, Property 2: パスワード不正時のエラーメッセージ**
        
        不正なパスワードのみの場合、「パスワードが正しくありません」エラーを返す。
        
        **Validates: Requirements 1.3**
        """
        # テストファイルの存在確認
        test_files = get_encrypted_test_files()
        assume(len(test_files) > 0)
        assume(file_index < len(test_files))
        
        # 正しいパスワードと一致しないことを確認
        assume(wrong_password1 != TEST_PASSWORD)
        assume(wrong_password2 is None or wrong_password2 != TEST_PASSWORD)
        
        test_file_path = test_files[file_index]
        
        # 一時ディレクトリで実行
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalStorageService(base_dir=temp_dir, expiry_seconds=300)
            unlock_service = UnlockService(storage=storage)
            
            # テストファイルを保存
            with open(test_file_path, "rb") as f:
                file_id, _ = storage.save(f, test_file_path.name)
            
            # 不正なパスワードで解除を試行
            result = unlock_service.unlock(file_id, wrong_password1, wrong_password2)
            
            # プロパティの検証: 不正なパスワードでは失敗し、特定のエラーメッセージを返す
            assert result["success"] is False, \
                "不正なパスワードでは解除に失敗する"
            assert result["unlocked_file_id"] is None, \
                "解除失敗時は unlocked_file_id は None"
            assert result["message"] == ErrorMessages.PASSWORD_INCORRECT, \
                f"エラーメッセージは '{ErrorMessages.PASSWORD_INCORRECT}' であるべき、実際: '{result['message']}'"


# =============================================================================
# Property 5: パスワード未設定ファイルのエラー
# =============================================================================

class TestProperty5UnencryptedFileError:
    """
    **Feature: docker-excel-unlocker, Property 5: パスワード未設定ファイルのエラー**
    
    *For any* パスワード保護されていない Excel ファイルに対して、
    解除処理は「パスワードが設定されていません」というエラーメッセージを返す
    
    **Validates: Requirements 1.6**
    """
    
    @settings(max_examples=100)
    @given(
        password1=ASCII_TEXT,
        password2=st.one_of(st.none(), ASCII_TEXT),
        filename=ASCII_TEXT.map(lambda x: f"{x}.xlsx")
    )
    def test_unlock_fails_for_unencrypted_file(
        self,
        password1: str,
        password2: Optional[str],
        filename: str
    ):
        """
        **Feature: docker-excel-unlocker, Property 5: パスワード未設定ファイルのエラー**
        
        パスワード保護されていないファイルでは「パスワードが設定されていません」エラーを返す。
        
        **Validates: Requirements 1.6**
        """
        # 一時ディレクトリで実行
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalStorageService(base_dir=temp_dir, expiry_seconds=300)
            unlock_service = UnlockService(storage=storage)
            
            # パスワード保護されていない xlsx ファイルを作成
            unencrypted_data = create_unencrypted_xlsx()
            file_buffer = io.BytesIO(unencrypted_data)
            
            # ファイルを保存
            file_id, _ = storage.save(file_buffer, filename)
            
            # 解除を試行
            result = unlock_service.unlock(file_id, password1, password2)
            
            # プロパティの検証: パスワード未設定ファイルでは特定のエラーメッセージを返す
            assert result["success"] is False, \
                "パスワード未設定ファイルでは解除に失敗する"
            assert result["unlocked_file_id"] is None, \
                "解除失敗時は unlocked_file_id は None"
            assert result["message"] == ErrorMessages.PASSWORD_NOT_SET, \
                f"エラーメッセージは '{ErrorMessages.PASSWORD_NOT_SET}' であるべき、実際: '{result['message']}'"


# =============================================================================
# Property 6: ファイル名変更規則
# =============================================================================

class TestProperty6FilenameTransformation:
    """
    **Feature: docker-excel-unlocker, Property 6: ファイル名変更規則**
    
    *For any* 解除成功したファイルに対して、出力ファイル名は 
    `{元ファイル名}_解除.{拡張子}` の形式になる（拡張子なしの場合は `{元ファイル名}_解除`）
    
    **Validates: Requirements 1.7**
    """
    
    # ファイル名に使用可能な文字（ファイルシステム互換）
    # パス区切り文字やNULLを除外
    FILENAME_CHARS = st.text(
        alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P', 'S'),
            blacklist_characters='/\\:*?"<>|\x00',
            max_codepoint=65535
        ),
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip() != '' and not x.startswith('.'))
    
    # 拡張子のストラテジー（一般的な拡張子形式）
    EXTENSION = st.one_of(
        st.just(''),  # 拡張子なし
        st.sampled_from(['.xlsx', '.xls', '.txt', '.csv', '.doc', '.pdf']),
        st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N'), max_codepoint=127),
            min_size=1,
            max_size=5
        ).map(lambda x: f'.{x}')
    )
    
    @settings(max_examples=100)
    @given(
        base_name=FILENAME_CHARS,
        extension=EXTENSION
    )
    def test_filename_transformation_adds_suffix(
        self,
        base_name: str,
        extension: str
    ):
        """
        **Feature: docker-excel-unlocker, Property 6: ファイル名変更規則**
        
        任意のファイル名に対して、変換後のファイル名には必ず「_解除」が含まれる。
        
        **Validates: Requirements 1.7**
        """
        # UnlockService を作成（storage は不要）
        unlock_service = UnlockService(storage=None)
        
        # 元のファイル名を構築
        original_filename = f"{base_name}{extension}"
        
        # ファイル名変換を実行
        result = unlock_service._generate_unlocked_filename(original_filename)
        
        # プロパティの検証: 変換後のファイル名には「_解除」が含まれる
        assert "_解除" in result, \
            f"変換後のファイル名には '_解除' が含まれるべき: '{original_filename}' -> '{result}'"
    
    @settings(max_examples=100)
    @given(
        base_name=FILENAME_CHARS,
        extension=st.sampled_from(['.xlsx', '.xls', '.txt', '.csv', '.doc', '.pdf'])
    )
    def test_filename_transformation_preserves_extension(
        self,
        base_name: str,
        extension: str
    ):
        """
        **Feature: docker-excel-unlocker, Property 6: ファイル名変更規則**
        
        拡張子付きファイルの場合、変換後も同じ拡張子が保持される。
        
        **Validates: Requirements 1.7**
        """
        unlock_service = UnlockService(storage=None)
        
        original_filename = f"{base_name}{extension}"
        result = unlock_service._generate_unlocked_filename(original_filename)
        
        # プロパティの検証: 拡張子が保持される
        assert result.endswith(extension), \
            f"拡張子 '{extension}' が保持されるべき: '{original_filename}' -> '{result}'"
    
    @settings(max_examples=100)
    @given(
        base_name=FILENAME_CHARS
    )
    def test_filename_transformation_without_extension(
        self,
        base_name: str
    ):
        """
        **Feature: docker-excel-unlocker, Property 6: ファイル名変更規則**
        
        拡張子なしファイルの場合、`{元ファイル名}_解除` の形式になる。
        
        **Validates: Requirements 1.7**
        """
        # ドットを含まないファイル名のみをテスト
        assume('.' not in base_name)
        
        unlock_service = UnlockService(storage=None)
        
        result = unlock_service._generate_unlocked_filename(base_name)
        
        # プロパティの検証: 拡張子なしの場合は末尾が「_解除」
        expected = f"{base_name}_解除"
        assert result == expected, \
            f"拡張子なしファイルは '{expected}' になるべき、実際: '{result}'"
    
    @settings(max_examples=100)
    @given(
        base_name=FILENAME_CHARS,
        middle_part=FILENAME_CHARS,
        extension=st.sampled_from(['.xlsx', '.xls', '.txt'])
    )
    def test_filename_transformation_with_multiple_dots(
        self,
        base_name: str,
        middle_part: str,
        extension: str
    ):
        """
        **Feature: docker-excel-unlocker, Property 6: ファイル名変更規則**
        
        複数ドットを含むファイル名の場合、最後の拡張子のみが保持される。
        例: sample.backup.xlsx -> sample.backup_解除.xlsx
        
        **Validates: Requirements 1.7**
        """
        # middle_part にドットが含まれないことを確認
        assume('.' not in middle_part)
        
        unlock_service = UnlockService(storage=None)
        
        # 複数ドットを含むファイル名
        original_filename = f"{base_name}.{middle_part}{extension}"
        result = unlock_service._generate_unlocked_filename(original_filename)
        
        # プロパティの検証
        # 1. 「_解除」が含まれる
        assert "_解除" in result, \
            f"変換後のファイル名には '_解除' が含まれるべき: '{original_filename}' -> '{result}'"
        
        # 2. 拡張子が保持される
        assert result.endswith(extension), \
            f"拡張子 '{extension}' が保持されるべき: '{original_filename}' -> '{result}'"
        
        # 3. 「_解除」は拡張子の直前に挿入される
        expected = f"{base_name}.{middle_part}_解除{extension}"
        assert result == expected, \
            f"期待値: '{expected}'、実際: '{result}'"

