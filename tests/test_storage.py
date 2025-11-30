"""
StorageService のユニットテスト

LocalStorageService の基本機能をテストします。

Requirements: 1.4, 6.1, ダウンロードURLの有効期限
"""

import io
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.services.storage_service import (
    LocalStorageService,
    StorageService,
    FileEntry,
)


class TestLocalStorageService:
    """LocalStorageService のテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def storage(self, temp_dir):
        """テスト用 LocalStorageService インスタンスを作成"""
        return LocalStorageService(base_dir=temp_dir, expiry_seconds=300)
    
    @pytest.fixture
    def sample_file_content(self):
        """テスト用ファイル内容"""
        return b"Hello, Excel Unlocker!"
    
    @pytest.fixture
    def sample_file(self, sample_file_content):
        """テスト用ファイルライクオブジェクト"""
        return io.BytesIO(sample_file_content)
    
    def test_save_returns_file_id_and_path(self, storage, sample_file):
        """save() が file_id と file_path を返すことを確認"""
        file_id, file_path = storage.save(sample_file, "test.xlsx")
        
        assert file_id is not None
        assert len(file_id) == 36  # UUID形式
        assert file_path is not None
        assert os.path.exists(file_path)
    
    def test_save_creates_file_with_content(
        self, storage, sample_file, sample_file_content
    ):
        """save() がファイルを正しい内容で作成することを確認"""
        file_id, file_path = storage.save(sample_file, "test.xlsx")
        
        with open(file_path, "rb") as f:
            content = f.read()
        
        assert content == sample_file_content
    
    def test_save_registers_file_in_registry(self, storage, sample_file):
        """save() がファイルをレジストリに登録することを確認"""
        file_id, _ = storage.save(sample_file, "test.xlsx")
        
        assert file_id in storage._file_registry
        entry = storage._file_registry[file_id]
        assert entry.original_filename == "test.xlsx"
    
    def test_get_path_returns_path_for_valid_file(self, storage, sample_file):
        """get_path() が有効なファイルのパスを返すことを確認"""
        file_id, expected_path = storage.save(sample_file, "test.xlsx")
        
        actual_path = storage.get_path(file_id)
        
        assert actual_path == expected_path
    
    def test_get_path_returns_none_for_invalid_file_id(self, storage):
        """get_path() が無効な file_id に対して None を返すことを確認"""
        result = storage.get_path("invalid-file-id")
        
        assert result is None
    
    def test_load_returns_file_content(
        self, storage, sample_file, sample_file_content
    ):
        """load() がファイル内容を返すことを確認"""
        file_id, _ = storage.save(sample_file, "test.xlsx")
        
        content = storage.load(file_id)
        
        assert content == sample_file_content
    
    def test_load_returns_none_for_invalid_file_id(self, storage):
        """load() が無効な file_id に対して None を返すことを確認"""
        result = storage.load("invalid-file-id")
        
        assert result is None
    
    def test_delete_removes_file(self, storage, sample_file):
        """delete() がファイルを削除することを確認"""
        file_id, file_path = storage.save(sample_file, "test.xlsx")
        
        result = storage.delete(file_id)
        
        assert result is True
        assert not os.path.exists(file_path)
        assert file_id not in storage._file_registry
    
    def test_delete_returns_false_for_invalid_file_id(self, storage):
        """delete() が無効な file_id に対して False を返すことを確認"""
        result = storage.delete("invalid-file-id")
        
        assert result is False
    
    def test_generate_download_url_format(self, storage, sample_file):
        """generate_download_url() が正しい形式の URL を返すことを確認"""
        file_id, _ = storage.save(sample_file, "test.xlsx")
        
        url = storage.generate_download_url(file_id)
        
        assert url == f"/download/{file_id}"
    
    def test_get_filename_returns_original_filename(self, storage, sample_file):
        """get_filename() が元のファイル名を返すことを確認"""
        file_id, _ = storage.save(sample_file, "original_name.xlsx")
        
        filename = storage.get_filename(file_id)
        
        assert filename == "original_name.xlsx"
    
    def test_get_filename_returns_none_for_invalid_file_id(self, storage):
        """get_filename() が無効な file_id に対して None を返すことを確認"""
        result = storage.get_filename("invalid-file-id")
        
        assert result is None
    
    def test_is_expired_returns_false_for_fresh_file(self, storage, sample_file):
        """is_expired() が新しいファイルに対して False を返すことを確認"""
        file_id, _ = storage.save(sample_file, "test.xlsx")
        
        result = storage.is_expired(file_id)
        
        assert result is False
    
    def test_is_expired_returns_true_for_expired_file(self, temp_dir, sample_file):
        """is_expired() が期限切れファイルに対して True を返すことを確認"""
        # 有効期限を1秒に設定
        storage = LocalStorageService(base_dir=temp_dir, expiry_seconds=1)
        file_id, _ = storage.save(sample_file, "test.xlsx")
        
        # 2秒待機して期限切れにする
        time.sleep(2)
        
        result = storage.is_expired(file_id)
        
        assert result is True
    
    def test_is_expired_returns_true_for_invalid_file_id(self, storage):
        """is_expired() が無効な file_id に対して True を返すことを確認"""
        result = storage.is_expired("invalid-file-id")
        
        assert result is True
    
    def test_get_path_returns_none_for_expired_file(self, temp_dir, sample_file):
        """get_path() が期限切れファイルに対して None を返すことを確認"""
        storage = LocalStorageService(base_dir=temp_dir, expiry_seconds=1)
        file_id, _ = storage.save(sample_file, "test.xlsx")
        
        time.sleep(2)
        
        result = storage.get_path(file_id)
        
        assert result is None
    
    def test_sanitize_filename_removes_path_separators(self, storage, sample_file):
        """ファイル名からパス区切り文字が除去されることを確認"""
        file_id, file_path = storage.save(sample_file, "path/to/file.xlsx")
        
        # パス区切り文字がアンダースコアに置換されている
        assert "path_to_file.xlsx" in file_path
    
    def test_save_handles_large_file_in_chunks(self, storage):
        """save() が大きなファイルをチャンク単位で処理することを確認"""
        # 3MB のテストデータを作成
        large_content = b"x" * (3 * 1024 * 1024)
        large_file = io.BytesIO(large_content)
        
        file_id, file_path = storage.save(large_file, "large.xlsx")
        
        # ファイルが正しく保存されていることを確認
        with open(file_path, "rb") as f:
            saved_content = f.read()
        
        assert saved_content == large_content
    
    def test_cleanup_expired_removes_old_files(self, temp_dir):
        """期限切れファイルが自動削除されることを確認"""
        storage = LocalStorageService(base_dir=temp_dir, expiry_seconds=1)
        
        # ファイルを保存
        file1 = io.BytesIO(b"file1")
        file_id1, file_path1 = storage.save(file1, "file1.xlsx")
        
        # 期限切れを待つ
        time.sleep(2)
        
        # 新しいファイルを保存（クリーンアップがトリガーされる）
        file2 = io.BytesIO(b"file2")
        file_id2, _ = storage.save(file2, "file2.xlsx")
        
        # 古いファイルが削除されていることを確認
        assert file_id1 not in storage._file_registry
        assert not os.path.exists(file_path1)
        
        # 新しいファイルは存在することを確認
        assert file_id2 in storage._file_registry


class TestStorageServiceAbstract:
    """StorageService 抽象クラスのテスト"""
    
    def test_storage_service_is_abstract(self):
        """StorageService が抽象クラスであることを確認"""
        with pytest.raises(TypeError):
            StorageService()
    
    def test_local_storage_service_is_subclass(self):
        """LocalStorageService が StorageService のサブクラスであることを確認"""
        assert issubclass(LocalStorageService, StorageService)


class TestFileEntry:
    """FileEntry データクラスのテスト"""
    
    def test_file_entry_creation(self):
        """FileEntry が正しく作成されることを確認"""
        entry = FileEntry(
            file_id="test-id",
            file_path="/tmp/test.xlsx",
            original_filename="test.xlsx"
        )
        
        assert entry.file_id == "test-id"
        assert entry.file_path == "/tmp/test.xlsx"
        assert entry.original_filename == "test.xlsx"
        assert entry.downloaded is False
        assert isinstance(entry.created_at, datetime)
