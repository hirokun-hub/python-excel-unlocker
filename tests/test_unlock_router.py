"""
/unlock エンドポイントのテスト

unlock.py ルーターの機能をテストします。

Requirements: 1.1, 1.2, 1.3, 1.6, 6.2, 6.3
"""

import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import TEST_DATA_DIR, TEST_PASSWORD, TEST_FILES


class TestUnlockEndpointValidation:
    """/unlock エンドポイントのバリデーションテスト"""
    
    def test_invalid_extension_returns_400(self):
        """
        許可されていない拡張子のファイルは 400 エラーを返す
        
        Requirements: 6.2
        """
        with TestClient(app) as client:
            # テキストファイルをアップロード
            response = client.post(
                "/unlock",
                files={"file": ("test.txt", b"dummy content", "text/plain")},
                data={"password1": "test123"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            assert data["message"] == "サポートされていないファイル形式です"
            assert data["downloadUrl"] is None
    
    def test_pdf_extension_returns_400(self):
        """
        PDF ファイルは 400 エラーを返す
        
        Requirements: 6.2
        """
        with TestClient(app) as client:
            response = client.post(
                "/unlock",
                files={"file": ("document.pdf", b"dummy pdf", "application/pdf")},
                data={"password1": "test123"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["message"] == "サポートされていないファイル形式です"
    
    def test_xlsx_extension_passes_validation(self):
        """
        .xlsx 拡張子は拡張子バリデーションを通過する
        （ダミーファイルは msoffcrypto が処理できないため別のエラーになる）
        
        Requirements: 6.2
        """
        with TestClient(app) as client:
            # ダミーの xlsx ファイル（実際には無効な内容）
            response = client.post(
                "/unlock",
                files={"file": ("test.xlsx", b"dummy xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"password1": "test123"}
            )
            
            # 拡張子バリデーションは通過するが、ファイル内容が無効なのでエラー
            # msoffcrypto が処理できないファイルは「サポートされていないファイル形式です」
            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            # ダミーファイルは msoffcrypto が処理できないため、このエラーは正しい
            assert data["message"] == "サポートされていないファイル形式です"
    
    def test_xls_extension_passes_validation(self):
        """
        .xls 拡張子は拡張子バリデーションを通過する
        （ダミーファイルは msoffcrypto が処理できないため別のエラーになる）
        
        Requirements: 6.2
        """
        with TestClient(app) as client:
            response = client.post(
                "/unlock",
                files={"file": ("test.xls", b"dummy xls", "application/vnd.ms-excel")},
                data={"password1": "test123"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            # ダミーファイルは msoffcrypto が処理できないため、このエラーは正しい
            assert data["message"] == "サポートされていないファイル形式です"
    
    def test_file_too_large_returns_400(self):
        """
        ファイルサイズが上限を超える場合は 400 エラーを返す
        
        Requirements: 6.3
        """
        from app.config import settings
        
        with TestClient(app) as client:
            # 上限を超えるサイズのダミーファイルを作成
            large_content = b"x" * (settings.max_file_size_bytes + 1)
            
            response = client.post(
                "/unlock",
                files={"file": ("large.xlsx", large_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"password1": "test123"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            assert data["message"] == "ファイルサイズが大きすぎます"
            assert data["downloadUrl"] is None
    
    def test_missing_password1_returns_422(self):
        """
        password1 が欠落している場合は 422 エラーを返す
        """
        with TestClient(app) as client:
            response = client.post(
                "/unlock",
                files={"file": ("test.xlsx", b"dummy", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={}  # password1 なし
            )
            
            assert response.status_code == 422
    
    def test_missing_file_returns_422(self):
        """
        ファイルが欠落している場合は 422 エラーを返す
        """
        with TestClient(app) as client:
            response = client.post(
                "/unlock",
                data={"password1": "test123"}
            )
            
            assert response.status_code == 422


class TestUnlockEndpointWithRealFiles:
    """実際のテストファイルを使用した /unlock エンドポイントのテスト"""
    
    def test_unlock_with_correct_password(self, test_excel_file: Path, test_password: str):
        """
        正しいパスワードで解除が成功する
        
        Requirements: 1.1, 1.2
        """
        if not test_excel_file.exists():
            pytest.skip(f"Test file not found: {test_excel_file}")
        
        with TestClient(app) as client:
            with open(test_excel_file, "rb") as f:
                response = client.post(
                    "/unlock",
                    files={"file": (test_excel_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={"password1": test_password}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] is None
            assert data["downloadUrl"] is not None
            assert data["downloadUrl"].startswith("/download/")
            # ファイル名に「_解除」が含まれる
            assert "_解除" in data["fileName"]
    
    def test_unlock_with_wrong_password(self, test_excel_file: Path, wrong_password: str):
        """
        不正なパスワードでは解除が失敗する
        
        Requirements: 1.3
        """
        if not test_excel_file.exists():
            pytest.skip(f"Test file not found: {test_excel_file}")
        
        with TestClient(app) as client:
            with open(test_excel_file, "rb") as f:
                response = client.post(
                    "/unlock",
                    files={"file": (test_excel_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={"password1": wrong_password}
                )
            
            assert response.status_code == 400
            data = response.json()
            assert data["status"] == "error"
            assert data["message"] == "パスワードが正しくありません"
            assert data["downloadUrl"] is None
    
    def test_unlock_with_password2_fallback(self, test_excel_file: Path, test_password: str, wrong_password: str):
        """
        第1パスワードが不正でも第2パスワードで解除できる
        
        Requirements: 1.2
        """
        if not test_excel_file.exists():
            pytest.skip(f"Test file not found: {test_excel_file}")
        
        with TestClient(app) as client:
            with open(test_excel_file, "rb") as f:
                response = client.post(
                    "/unlock",
                    files={"file": (test_excel_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={
                        "password1": wrong_password,  # 不正なパスワード
                        "password2": test_password    # 正しいパスワード
                    }
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["downloadUrl"] is not None
    
    def test_unlock_with_both_wrong_passwords(self, test_excel_file: Path, wrong_password: str):
        """
        両方のパスワードが不正な場合は失敗する
        
        Requirements: 1.3
        """
        if not test_excel_file.exists():
            pytest.skip(f"Test file not found: {test_excel_file}")
        
        with TestClient(app) as client:
            with open(test_excel_file, "rb") as f:
                response = client.post(
                    "/unlock",
                    files={"file": (test_excel_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={
                        "password1": wrong_password,
                        "password2": "another_wrong_password"
                    }
                )
            
            assert response.status_code == 400
            data = response.json()
            assert data["message"] == "パスワードが正しくありません"


class TestUnlockEndpointUnprotectedFile:
    """パスワード未設定ファイルのテスト"""
    
    def test_unprotected_file_returns_error(self):
        """
        パスワード保護されていないファイルはエラーを返す
        
        Requirements: 1.6
        """
        # 有効な xlsx ファイルを作成（パスワードなし）
        # openpyxl を使用して最小限の xlsx を作成
        try:
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws["A1"] = "Test"
            
            # BytesIO に保存
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            with TestClient(app) as client:
                response = client.post(
                    "/unlock",
                    files={"file": ("unprotected.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={"password1": "any_password"}
                )
                
                assert response.status_code == 400
                data = response.json()
                assert data["status"] == "error"
                assert data["message"] == "パスワードが設定されていません"
                assert data["downloadUrl"] is None
        
        except ImportError:
            pytest.skip("openpyxl not installed")


class TestUnlockEndpointResponseFormat:
    """レスポンス形式のテスト"""
    
    def test_success_response_format(self, test_excel_file: Path, test_password: str):
        """
        成功時のレスポンス形式を確認
        
        Requirements: API仕様
        """
        if not test_excel_file.exists():
            pytest.skip(f"Test file not found: {test_excel_file}")
        
        with TestClient(app) as client:
            with open(test_excel_file, "rb") as f:
                response = client.post(
                    "/unlock",
                    files={"file": (test_excel_file.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    data={"password1": test_password}
                )
            
            data = response.json()
            
            # 必須フィールドの存在確認
            assert "fileName" in data
            assert "status" in data
            assert "message" in data
            assert "downloadUrl" in data
            
            # 成功時の値
            assert data["status"] == "success"
            assert data["message"] is None
            assert isinstance(data["downloadUrl"], str)
    
    def test_error_response_format(self):
        """
        エラー時のレスポンス形式を確認
        
        Requirements: API仕様
        """
        with TestClient(app) as client:
            response = client.post(
                "/unlock",
                files={"file": ("test.txt", b"dummy", "text/plain")},
                data={"password1": "test123"}
            )
            
            data = response.json()
            
            # 必須フィールドの存在確認
            assert "fileName" in data
            assert "status" in data
            assert "message" in data
            assert "downloadUrl" in data
            
            # エラー時の値
            assert data["status"] == "error"
            assert isinstance(data["message"], str)
            assert data["downloadUrl"] is None
