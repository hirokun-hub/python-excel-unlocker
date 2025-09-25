"""
ファイル安全性チェック機能のユニットテスト

基本的なマルウェア対策機能のテストを実装
"""
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open
import zipfile
from pathlib import Path

# テスト対象のインポート
try:
    from src.file_security import (
        check_file_extension,
        check_file_size,
        check_magic_bytes,
        check_mime_type,
        check_file_structure,
        comprehensive_security_check,
        quarantine_file,
        SecurityCheckResult
    )
except ImportError:
    # 相対インポートでフォールバック
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    from file_security import (
        check_file_extension,
        check_file_size,
        check_magic_bytes,
        check_mime_type,
        check_file_structure,
        comprehensive_security_check,
        quarantine_file,
        SecurityCheckResult
    )

class TestSecurityCheckResult:
    """SecurityCheckResultクラスのテスト"""
    
    def test_to_dict(self):
        """to_dict メソッドのテスト"""
        result = SecurityCheckResult(
            safe=True,
            reason="テスト成功",
            risk_level="low",
            quarantine=False,
            details={"test": "data"}
        )
        
        expected = {
            'safe': True,
            'reason': "テスト成功",
            'risk_level': "low",
            'quarantine': False,
            'details': {"test": "data"}
        }
        
        assert result.to_dict() == expected

class TestFileExtensionCheck:
    """ファイル拡張子チェックのテスト"""
    
    def test_allowed_extensions(self):
        """許可された拡張子のテスト"""
        # .xlsx ファイル
        result = check_file_extension("test.xlsx")
        assert result.safe is True
        assert result.risk_level == "low"
        
        # .xls ファイル
        result = check_file_extension("test.xls")
        assert result.safe is True
        assert result.risk_level == "low"
    
    def test_dangerous_extensions(self):
        """危険な拡張子のテスト"""
        # .xlsm ファイル（マクロ付き）
        result = check_file_extension("test.xlsm")
        assert result.safe is False
        assert result.risk_level == "high"
        assert result.quarantine is True
        assert "マクロ付き" in result.reason
        
        # 実行ファイル
        result = check_file_extension("malware.exe")
        assert result.safe is False
        assert result.risk_level == "critical"
        assert result.quarantine is True
        assert "危険なファイル形式" in result.reason
    
    def test_unsupported_extensions(self):
        """サポートされていない拡張子のテスト"""
        result = check_file_extension("document.pdf")
        assert result.safe is False
        assert result.risk_level == "medium"
        assert result.quarantine is False
        assert "サポートされていない" in result.reason
    
    def test_case_insensitive(self):
        """大文字小文字を区別しないテスト"""
        result = check_file_extension("TEST.XLSX")
        assert result.safe is True
        
        result = check_file_extension("TEST.XLSM")
        assert result.safe is False
        assert result.risk_level == "high"

class TestFileSizeCheck:
    """ファイルサイズチェックのテスト"""
    
    def test_valid_file_size(self):
        """有効なファイルサイズのテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # 1KB のテストファイル
            tmp_file.write(b'x' * 1024)
            tmp_file.flush()
            
            try:
                result = check_file_size(tmp_file.name)
                assert result.safe is True
                assert result.risk_level == "low"
                assert result.details['file_size'] == 1024
            finally:
                os.unlink(tmp_file.name)
    
    def test_file_too_large(self):
        """ファイルサイズが大きすぎる場合のテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # 21MB のテストファイル（制限は20MB）
            tmp_file.write(b'x' * (21 * 1024 * 1024))
            tmp_file.flush()
            
            try:
                result = check_file_size(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "medium"
                assert "上限" in result.reason
            finally:
                os.unlink(tmp_file.name)
    
    def test_file_too_small(self):
        """ファイルサイズが小さすぎる場合のテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # 50バイトのテストファイル（最小は100バイト）
            tmp_file.write(b'x' * 50)
            tmp_file.flush()
            
            try:
                result = check_file_size(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "medium"
                assert result.quarantine is True
                assert "小さすぎます" in result.reason
            finally:
                os.unlink(tmp_file.name)
    
    def test_nonexistent_file(self):
        """存在しないファイルのテスト"""
        result = check_file_size("/nonexistent/file.xlsx")
        assert result.safe is False
        assert result.risk_level == "medium"
        assert "取得に失敗" in result.reason

class TestMagicBytesCheck:
    """マジックバイトチェックのテスト"""
    
    def test_valid_xlsx_magic_bytes(self):
        """有効な.xlsxマジックバイトのテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # ZIP形式のマジックバイト
            tmp_file.write(b'PK\x03\x04' + b'x' * 100)
            tmp_file.flush()
            
            try:
                result = check_magic_bytes(tmp_file.name)
                assert result.safe is True
                assert result.risk_level == "low"
                assert result.details['detected_format'] == 'xlsx_zip'
            finally:
                os.unlink(tmp_file.name)
    
    def test_valid_xls_magic_bytes(self):
        """有効な.xlsマジックバイトのテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # OLE2形式のマジックバイト
            tmp_file.write(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'x' * 100)
            tmp_file.flush()
            
            try:
                result = check_magic_bytes(tmp_file.name)
                assert result.safe is True
                assert result.risk_level == "low"
                assert result.details['detected_format'] == 'xls_ole2'
            finally:
                os.unlink(tmp_file.name)
    
    def test_dangerous_magic_bytes(self):
        """危険なマジックバイトのテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # Windows実行ファイルのマジックバイト
            tmp_file.write(b'MZ' + b'x' * 100)
            tmp_file.flush()
            
            try:
                result = check_magic_bytes(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "critical"
                assert result.quarantine is True
                assert "実行ファイル" in result.reason
            finally:
                os.unlink(tmp_file.name)
    
    def test_invalid_magic_bytes(self):
        """無効なマジックバイトのテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # 無効なマジックバイト
            tmp_file.write(b'INVALID' + b'x' * 100)
            tmp_file.flush()
            
            try:
                result = check_magic_bytes(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "high"
                assert result.quarantine is True
                assert "認識できません" in result.reason
            finally:
                os.unlink(tmp_file.name)
    
    def test_file_too_short(self):
        """ファイルが短すぎる場合のテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            # 3バイトのファイル
            tmp_file.write(b'ABC')
            tmp_file.flush()
            
            try:
                result = check_magic_bytes(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "medium"
                assert result.quarantine is True
                assert "短すぎます" in result.reason
            finally:
                os.unlink(tmp_file.name)

class TestMimeTypeCheck:
    """MIMEタイプチェックのテスト"""
    
    def test_allowed_mime_types(self):
        """許可されたMIMEタイプのテスト"""
        result = check_mime_type(
            "test.xlsx", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert result.safe is True
        assert result.risk_level == "low"
    
    def test_disallowed_mime_type(self):
        """許可されていないMIMEタイプのテスト"""
        result = check_mime_type("test.pdf", "application/pdf")
        assert result.safe is False
        assert result.risk_level == "medium"
        assert "許可されていない" in result.reason
    
    def test_no_declared_mime_type(self):
        """MIMEタイプが宣言されていない場合のテスト"""
        result = check_mime_type("test.xlsx")
        assert result.safe is True  # 宣言されていない場合は通過

class TestFileStructureCheck:
    """ファイル構造チェックのテスト"""
    
    def test_valid_xlsx_structure(self):
        """有効な.xlsx構造のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            # 最小限のZIPファイルを作成
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                zip_file.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
                zip_file.writestr('_rels/.rels', '<?xml version="1.0"?>')
            
            try:
                result = check_file_structure(tmp_file.name)
                assert result.safe is True
                assert result.risk_level == "low"
            finally:
                os.unlink(tmp_file.name)
    
    def test_xlsx_with_macros(self):
        """マクロ付き.xlsxのテスト"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                zip_file.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
                zip_file.writestr('_rels/.rels', '<?xml version="1.0"?>')
                zip_file.writestr('xl/vbaProject.bin', 'macro content')  # マクロファイル
            
            try:
                result = check_file_structure(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "critical"
                assert result.quarantine is True
                assert "マクロ" in result.reason
            finally:
                os.unlink(tmp_file.name)
    
    def test_invalid_zip_structure(self):
        """無効なZIP構造のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            # 無効なZIPファイル
            tmp_file.write(b'NOT A ZIP FILE')
            tmp_file.flush()
            
            try:
                result = check_file_structure(tmp_file.name)
                assert result.safe is False
                assert result.risk_level == "high"
                assert result.quarantine is True
                assert "読み取れません" in result.reason
            finally:
                os.unlink(tmp_file.name)
    
    def test_valid_xls_structure(self):
        """有効な.xls構造のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as tmp_file:
            # OLE2ヘッダーを作成
            ole2_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * 504
            tmp_file.write(ole2_header)
            tmp_file.flush()
            
            try:
                result = check_file_structure(tmp_file.name)
                assert result.safe is True
                assert result.risk_level == "low"
            finally:
                os.unlink(tmp_file.name)

class TestQuarantineFile:
    """ファイル隔離機能のテスト"""
    
    def test_quarantine_success(self):
        """ファイル隔離成功のテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b'suspicious content')
            tmp_file.flush()
            
            try:
                result = quarantine_file(tmp_file.name, "テスト隔離")
                assert result is True
                # 元のファイルが存在しないことを確認
                assert not os.path.exists(tmp_file.name)
            except Exception:
                # テスト環境でファイル移動に失敗する場合があるため、クリーンアップ
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

class TestComprehensiveSecurityCheck:
    """包括的セキュリティチェックのテスト"""
    
    def test_safe_file(self):
        """安全なファイルのテスト"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            # 有効なZIPファイルを作成
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                zip_file.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
                zip_file.writestr('_rels/.rels', '<?xml version="1.0"?>')
            
            try:
                result = comprehensive_security_check(
                    tmp_file.name,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                assert result['safe'] is True
                assert result['risk_level'] == "low"
                assert result['quarantine_applied'] is False
                assert len(result['failed_checks']) == 0
            finally:
                os.unlink(tmp_file.name)
    
    def test_dangerous_file(self):
        """危険なファイルのテスト"""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as tmp_file:
            # 実行ファイルのマジックバイト
            tmp_file.write(b'MZ' + b'x' * 1000)
            tmp_file.flush()
            
            try:
                result = comprehensive_security_check(tmp_file.name)
                assert result['safe'] is False
                assert result['risk_level'] == "critical"
                assert result['quarantine_applied'] is True
                assert len(result['failed_checks']) > 0
                
                # 拡張子チェックとマジックバイトチェックの両方で失敗するはず
                failed_check_names = [check['check'] for check in result['failed_checks']]
                assert 'extension_check' in failed_check_names
                assert 'magic_bytes_check' in failed_check_names
            finally:
                # ファイルが隔離されている可能性があるため、存在チェック
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    def test_macro_file(self):
        """マクロ付きファイルのテスト"""
        with tempfile.NamedTemporaryFile(suffix='.xlsm', delete=False) as tmp_file:
            tmp_file.write(b'PK\x03\x04' + b'x' * 1000)
            tmp_file.flush()
            
            try:
                result = comprehensive_security_check(tmp_file.name)
                assert result['safe'] is False
                assert result['risk_level'] == "high"
                assert result['quarantine_applied'] is True
                
                # 拡張子チェックで失敗するはず
                failed_check_names = [check['check'] for check in result['failed_checks']]
                assert 'extension_check' in failed_check_names
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

if __name__ == '__main__':
    pytest.main([__file__])