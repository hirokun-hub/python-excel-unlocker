"""
/download エンドポイントのテスト

download.py ルーターの機能をテストします。

Requirements: API仕様（/download/{file_id}）、ダウンロードURLの有効期限
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestDownloadEndpoint:
    """/download/{file_id} エンドポイントのテスト"""
    
    def test_download_nonexistent_file_returns_404(self):
        """
        存在しない file_id でダウンロードすると 404 が返ることを確認
        
        Requirements: API仕様（/download/{file_id}）
        """
        with TestClient(app) as client:
            response = client.get("/download/nonexistent-file-id")
            
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "Not Found"
            assert data["message"] == "ファイルが見つかりません"
    
    def test_download_valid_file_returns_content(self):
        """
        有効な file_id でダウンロードするとファイル内容が返ることを確認
        
        Requirements: API仕様（/download/{file_id}）
        """
        with TestClient(app) as client:
            # テスト用ファイルを保存
            storage_service = app.state.storage_service
            test_content = b"test file content for download"
            test_filename = "test_download.xlsx"
            
            file_like = io.BytesIO(test_content)
            file_id, _ = storage_service.save(file_like, test_filename)
            
            # ダウンロード
            response = client.get(f"/download/{file_id}")
            
            assert response.status_code == 200
            assert response.content == test_content
            
            # Content-Disposition ヘッダーを確認
            content_disposition = response.headers.get("content-disposition")
            assert content_disposition is not None
            assert "attachment" in content_disposition
            assert "test_download.xlsx" in content_disposition
    
    def test_download_deletes_file_after_success(self):
        """
        ダウンロード成功後にファイルが削除されることを確認
        
        Requirements: ダウンロードURLの有効期限
        """
        with TestClient(app) as client:
            # テスト用ファイルを保存
            storage_service = app.state.storage_service
            test_content = b"test file content to be deleted"
            test_filename = "test_delete_after_download.xlsx"
            
            file_like = io.BytesIO(test_content)
            file_id, _ = storage_service.save(file_like, test_filename)
            
            # 1回目のダウンロード（成功）
            response1 = client.get(f"/download/{file_id}")
            assert response1.status_code == 200
            
            # 2回目のダウンロード（ファイルは削除済みなので 404）
            response2 = client.get(f"/download/{file_id}")
            assert response2.status_code == 404
    
    def test_download_japanese_filename(self):
        """
        日本語ファイル名が正しくエンコードされることを確認
        
        Requirements: API仕様（/download/{file_id}）
        """
        with TestClient(app) as client:
            # 日本語ファイル名でテスト用ファイルを保存
            storage_service = app.state.storage_service
            test_content = b"japanese filename test"
            test_filename = "テスト_解除.xlsx"
            
            file_like = io.BytesIO(test_content)
            file_id, _ = storage_service.save(file_like, test_filename)
            
            # ダウンロード
            response = client.get(f"/download/{file_id}")
            
            assert response.status_code == 200
            
            # Content-Disposition ヘッダーに UTF-8 エンコードされたファイル名が含まれる
            content_disposition = response.headers.get("content-disposition")
            assert content_disposition is not None
            assert "UTF-8''" in content_disposition
    
    def test_download_expired_file_returns_404(self):
        """
        期限切れの file_id でダウンロードすると 404 が返ることを確認
        
        Requirements: ダウンロードURLの有効期限
        """
        with TestClient(app) as client:
            from datetime import datetime, timedelta
            
            # テスト用ファイルを保存
            storage_service = app.state.storage_service
            test_content = b"expired file content"
            test_filename = "test_expired.xlsx"
            
            file_like = io.BytesIO(test_content)
            file_id, _ = storage_service.save(file_like, test_filename)
            
            # ファイルエントリの作成日時を過去に設定（期限切れにする）
            entry = storage_service._file_registry.get(file_id)
            if entry:
                # 有効期限を超えた時間に設定
                entry.created_at = datetime.now() - timedelta(
                    seconds=storage_service.expiry_seconds + 10
                )
            
            # ダウンロード（期限切れなので 404）
            response = client.get(f"/download/{file_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "Not Found"
            assert data["message"] == "ファイルが見つかりません"
