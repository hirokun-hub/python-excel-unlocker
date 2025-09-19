"""
get_upload_url.py のユニットテスト
JWT認証対応版
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポート
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from get_upload_url import lambda_handler, _is_supported_file_type
from jwt_test_utils import create_test_event, create_auth_header, mock_jwt_verification
from test_env_utils import TestEnvironment

class TestGetUploadUrl:
    """署名付きURL生成Lambda関数のテストクラス"""
    
    # setup_envフィクスチャを削除し、各テストメソッドで個別に環境変数を設定
    
    @patch('get_upload_url.S3_BUCKET_NAME', 'test-excel-unlock-bucket')
    @patch('s3_utils.generate_presigned_url')
    @patch('auth_utils.verify_google_jwt')
    def test_successful_url_generation(self, mock_verify_jwt, mock_generate_url):
        """正常な署名付きURL生成のテスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        mock_generate_url.return_value = 'https://test-bucket.s3.amazonaws.com/uploads/test-file.xlsx?signature=...'
        
        # 環境変数設定
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            # テストイベント（JWT認証ヘッダー付き）
            event = create_test_event(
                email='test@example.com',
                body={
                    'fileName': 'test-file.xlsx',
                    'fileSize': 1024000,
                    'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
            )
            
            # 関数実行
            result = lambda_handler(event, {})
            
            # 結果検証
            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['success'] is True
            assert 'uploadUrl' in body
            assert 'fileKey' in body
            assert 'expiresIn' in body
            assert body['expiresIn'] == 60
            
            # モック呼び出し検証
            mock_verify_jwt.assert_called_once()
            mock_generate_url.assert_called_once()
    
    @patch('get_upload_url.S3_BUCKET_NAME', 'test-excel-unlock-bucket')
    @patch('auth_utils.verify_google_jwt')
    def test_access_denied(self, mock_verify_jwt):
        """アクセス拒否のテスト"""
        # モックの設定（許可されていないユーザー）
        mock_verify_jwt.return_value = mock_jwt_verification('unauthorized@example.com')
        
        # 許可されていないユーザーのみを設定
        with TestEnvironment.temporary_env(
            S3_BUCKET_NAME='test-excel-unlock-bucket',
            ALLOWED_USERS='allowed@example.com',  # unauthorized@example.comは含まれない
            GOOGLE_CLIENT_ID='test-client-id.apps.googleusercontent.com',
            LOG_LEVEL='INFO',
            AWS_DEFAULT_REGION='ap-northeast-1'
        ):
            # テストイベント
            event = create_test_event(
                email='unauthorized@example.com',
                body={
                    'fileName': 'test-file.xlsx',
                    'fileSize': 1024000
                }
            )
            
            # 関数実行
            result = lambda_handler(event, {})
            
            # 結果検証
            assert result['statusCode'] == 403
            body = json.loads(result['body'])
            assert body['success'] is False
            assert body['error'] == 'access_denied'
    
    def test_invalid_json_body(self):
        """不正なJSONボディのテスト"""
        # 認証ヘッダーなしのイベント（認証エラーが先に発生）
        event = {
            'headers': {'Content-Type': 'application/json'},
            'body': 'invalid json'
        }
        
        result = lambda_handler(event, {})
        
        # JWT認証が先に失敗するため401エラーになる
        assert result['statusCode'] == 401
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'authentication_failed'
    
    @patch('get_upload_url.S3_BUCKET_NAME', 'test-excel-unlock-bucket')
    @patch('auth_utils.verify_google_jwt')
    def test_missing_filename(self, mock_verify_jwt):
        """ファイル名未指定のテスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            event = create_test_event(
                email='test@example.com',
                body={
                    'fileSize': 1024000
                    # fileName が未指定
                }
            )
            
            result = lambda_handler(event, {})
            
            assert result['statusCode'] == 400
            body = json.loads(result['body'])
            assert body['success'] is False
            assert body['error'] == 'missing_filename'
    
    @patch('get_upload_url.S3_BUCKET_NAME', 'test-excel-unlock-bucket')
    @patch('auth_utils.verify_google_jwt')
    def test_unsupported_file_type(self, mock_verify_jwt):
        """サポートされていないファイル形式のテスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            event = create_test_event(
                email='test@example.com',
                body={
                    'fileName': 'test-file.pdf',  # PDFファイル（サポート外）
                    'fileSize': 1024000
                }
            )
            
            result = lambda_handler(event, {})
            
            assert result['statusCode'] == 400
            body = json.loads(result['body'])
            assert body['success'] is False
            assert body['error'] == 'unsupported_format'
    
    @patch('get_upload_url.S3_BUCKET_NAME', 'test-excel-unlock-bucket')
    @patch('auth_utils.verify_google_jwt')
    def test_file_too_large(self, mock_verify_jwt):
        """ファイルサイズ制限超過のテスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            event = create_test_event(
                email='test@example.com',
                body={
                    'fileName': 'large-file.xlsx',
                    'fileSize': 25 * 1024 * 1024  # 25MB（制限の20MBを超過）
                }
            )
            
            result = lambda_handler(event, {})
            
            assert result['statusCode'] == 400
            body = json.loads(result['body'])
            assert body['success'] is False
            assert body['error'] == 'file_too_large'
    
    @patch('auth_utils.verify_google_jwt')
    def test_url_generation_failure(self, mock_verify_jwt):
        """署名付きURL生成失敗のテスト（環境変数未設定）"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        # S3_BUCKET_NAME環境変数を削除してテスト（S3_BUCKET_NAMEはグローバル変数なのでNoneのまま）
        with TestEnvironment.temporary_env(
            ALLOWED_USERS='test@example.com', 
            GOOGLE_CLIENT_ID='test-client-id.apps.googleusercontent.com'
        ):
            event = create_test_event(
                email='test@example.com',
                body={
                    'fileName': 'test-file.xlsx',
                    'fileSize': 1024000
                }
            )
            
            result = lambda_handler(event, {})
            
            assert result['statusCode'] == 500
            body = json.loads(result['body'])
            assert body['success'] is False
            assert body['error'] == 'configuration_error'

class TestFileSupportValidation:
    """ファイル形式サポート判定のテストクラス"""
    
    def test_supported_xlsx_file(self):
        """xlsxファイルのサポート判定テスト"""
        assert _is_supported_file_type('test.xlsx') is True
        assert _is_supported_file_type('TEST.XLSX') is True  # 大文字小文字
    
    def test_supported_xls_file(self):
        """xlsファイルのサポート判定テスト"""
        assert _is_supported_file_type('test.xls') is True
        assert _is_supported_file_type('TEST.XLS') is True  # 大文字小文字
    
    def test_unsupported_file_types(self):
        """サポートされていないファイル形式のテスト"""
        assert _is_supported_file_type('test.pdf') is False
        assert _is_supported_file_type('test.docx') is False
        assert _is_supported_file_type('test.txt') is False
        assert _is_supported_file_type('test') is False  # 拡張子なし
    
    def test_mime_type_validation(self):
        """MIMEタイプによる判定テスト"""
        # 正しいMIMEタイプ
        assert _is_supported_file_type(
            'test.xlsx', 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ) is True
        
        assert _is_supported_file_type(
            'test.xls', 
            'application/vnd.ms-excel'
        ) is True
        
        # 間違ったMIMEタイプ
        assert _is_supported_file_type('test.pdf', 'application/pdf') is False