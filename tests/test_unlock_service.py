"""
UnlockService のテスト

テストデータ（data/）内の実際のパスワード保護された Excel ファイルを使用して
パスワード解除機能を検証します。

Requirements: 1.1, 1.2, 1.3, 1.6, 1.7
"""

import io
import os
import tempfile
from pathlib import Path

import pytest

from app.services.storage_service import LocalStorageService
from app.services.unlock_service import UnlockService, ErrorMessages
from tests.conftest import TEST_DATA_DIR, TEST_PASSWORD, TEST_FILES


class TestUnlockService:
    """UnlockService のテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def storage(self, temp_dir):
        """テスト用 LocalStorageService を作成"""
        return LocalStorageService(base_dir=temp_dir, expiry_seconds=300)
    
    @pytest.fixture
    def unlock_service(self, storage):
        """テスト用 UnlockService を作成"""
        return UnlockService(storage=storage)
    
    def test_unlock_with_correct_password(self, storage, unlock_service):
        """
        正しいパスワードで解除できることを確認
        Requirements: 1.1, 1.2
        """
        # テストファイルを読み込んで保存
        test_file_path = TEST_DATA_DIR / TEST_FILES[0]
        if not test_file_path.exists():
            pytest.skip(f"テストファイルが存在しません: {test_file_path}")
        
        with open(test_file_path, "rb") as f:
            file_id, _ = storage.save(f, TEST_FILES[0])
        
        # パスワード解除を実行
        result = unlock_service.unlock(file_id, TEST_PASSWORD)
        
        # 検証
        assert result["success"] is True
        assert result["unlocked_file_id"] is not None
        assert result["message"] is None
        assert result["original_filename"] == TEST_FILES[0]
        assert "_解除" in result["unlocked_filename"]
    
    def test_unlock_with_wrong_password(self, storage, unlock_service):
        """
        不正なパスワードでエラーメッセージが返ることを確認
        Requirements: 1.3
        """
        test_file_path = TEST_DATA_DIR / TEST_FILES[0]
        if not test_file_path.exists():
            pytest.skip(f"テストファイルが存在しません: {test_file_path}")
        
        with open(test_file_path, "rb") as f:
            file_id, _ = storage.save(f, TEST_FILES[0])
        
        # 不正なパスワードで解除を試行
        result = unlock_service.unlock(file_id, "wrong_password")
        
        # 検証
        assert result["success"] is False
        assert result["unlocked_file_id"] is None
        assert result["message"] == ErrorMessages.PASSWORD_INCORRECT
    
    def test_unlock_with_second_password(self, storage, unlock_service):
        """
        第2パスワードで解除できることを確認
        Requirements: 1.2
        """
        test_file_path = TEST_DATA_DIR / TEST_FILES[0]
        if not test_file_path.exists():
            pytest.skip(f"テストファイルが存在しません: {test_file_path}")
        
        with open(test_file_path, "rb") as f:
            file_id, _ = storage.save(f, TEST_FILES[0])
        
        # 第1パスワードは不正、第2パスワードが正しい
        result = unlock_service.unlock(file_id, "wrong", TEST_PASSWORD)
        
        # 検証
        assert result["success"] is True
        assert result["unlocked_file_id"] is not None
    
    def test_unlock_file_not_found(self, unlock_service):
        """
        存在しないファイルIDでエラーが返ることを確認
        """
        result = unlock_service.unlock("nonexistent-file-id", TEST_PASSWORD)
        
        assert result["success"] is False
        assert result["message"] == ErrorMessages.FILE_NOT_FOUND


class TestGenerateUnlockedFilename:
    """ファイル名変更ロジックのテスト"""
    
    @pytest.fixture
    def unlock_service(self):
        """StorageService なしで UnlockService を作成（ファイル名生成のみテスト）"""
        # storage は None でも _generate_unlocked_filename は動作する
        return UnlockService(storage=None)
    
    def test_filename_with_extension(self, unlock_service):
        """
        拡張子ありのファイル名変換
        Requirements: 1.7
        """
        assert unlock_service._generate_unlocked_filename("sample.xlsx") == "sample_解除.xlsx"
    
    def test_filename_without_extension(self, unlock_service):
        """
        拡張子なしのファイル名変換
        Requirements: 1.7
        """
        assert unlock_service._generate_unlocked_filename("sample") == "sample_解除"
    
    def test_filename_with_multiple_dots(self, unlock_service):
        """
        複数ドットを含むファイル名変換
        Requirements: 1.7
        """
        assert unlock_service._generate_unlocked_filename("sample.backup.xlsx") == "sample.backup_解除.xlsx"
    
    def test_filename_empty(self, unlock_service):
        """
        空のファイル名変換
        """
        assert unlock_service._generate_unlocked_filename("") == "_解除"
    
    def test_filename_hidden_file(self, unlock_service):
        """
        隠しファイル（ドットで始まる）の変換
        """
        assert unlock_service._generate_unlocked_filename(".hidden") == ".hidden_解除"
    
    def test_filename_japanese(self, unlock_service):
        """
        日本語ファイル名の変換
        Requirements: 1.7
        """
        original = "確定【20251031】【SB】【NPS評価】.xlsx"
        expected = "確定【20251031】【SB】【NPS評価】_解除.xlsx"
        assert unlock_service._generate_unlocked_filename(original) == expected
