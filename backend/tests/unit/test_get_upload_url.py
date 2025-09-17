"""
get_upload_url.py のユニットテスト
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポート
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from get_upload_url import lambda_handler, _is_supported_file_type

class TestGetUploadUrl:
    """署名付きURL生成Lambda関数のテストクラス"""
    
    @pytest.fixture(autouse=True)
    def setup_env(self):
        """各テストメソッドの前に実行される設定"""
        # 環境変数を設定
        original_env = {}
        test_env = {
            'S3_BUCKET_NAME': 'test-bucket',
            'ALLOWED_USERS': 'test@example.com,user@test.com',
            'LOG_LEVEL': 'INFO'
        }
        
        # 既存の環境変数を保存
        for key in test_env:
            if key in os.environ:
                original_env[key] = os.environ[key]
        
        # テスト用環境変数を設定
        os.environ.update(test_env)
        
        yield
        
        # 環境変数を復元
        for key in test_env:
            if key in original_env:
                os.environ[key] = original_env[key]
            elif key in os.environ:
                del os.environ[key]
    
    @patch('get_upload_url.generate_presigned_url')
    @patch('get_upload_url.validate_user_access')
    @patch('get_upload_url.extract_user_from_event')
    def test_successful_url_generation(self, mock_extract_user, mock_validate_access, mock_generate_url):
        """正常な署名付きURL生成のテスト"""
        # モックの設定
        mock_extract_user.return_value = 'test@example.com'
        mock_validate_access.return_value = {'authorized': True, 'message': 'Access granted'}
        mock_generate_url.return_value = 'https://test-bucket.s3.amazonaws.com/uploads/test-file.xlsx?signature=...'
        
        # テストイベント
        event = {
            'headers': {'x-user-email': 'test@example.com'},
            'body': json.dumps({
                'fileName': 'test-file.xlsx',
                'fileSize': 1024000,
                'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        }
        
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
        mock_extract_user.assert_called_once_with(event)
        mock_validate_access.assert_called_once_with('test@example.com')
        mock_generate_url.assert_called_once()
    
    @patch('get_upload_url.extract_user_from_event')
    @patch('get_upload_url.validate_user_access')
    def test_access_denied(self, mock_validate_access, mock_extract_user):
        """アクセス拒否のテスト"""
        # モックの設定
        mock_extract_user.return_value = 'unauthorized@example.com'
        mock_validate_access.return_value = {'authorized': False, 'message': 'Access denied'}
        
        # テストイベント
        event = {
            'headers': {'x-user-email': 'unauthorized@example.com'},
            'body': json.dumps({
                'fileName': 'test-file.xlsx',
                'fileSize': 1024000
            })
        }
        
        # 関数実行
        result = lambda_handler(event, {})
        
        # 結果検証
        assert result['statusCode'] == 403
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'access_denied'
    
    def test_invalid_json_body(self):
        """不正なJSONボディのテスト"""
        event = {
            'headers': {'x-user-email': 'test@example.com'},
            'body': 'invalid json'
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'invalid_json'
    
    @patch('get_upload_url.validate_user_access')
    @patch('get_upload_url.extract_user_from_event')
    def test_missing_filename(self, mock_extract_user, mock_validate_access):
        """ファイル名未指定のテスト"""
        # モックの設定
        mock_extract_user.return_value = 'test@example.com'
        mock_validate_access.return_value = {'authorized': True, 'message': 'Access granted'}
        
        event = {
            'headers': {'x-user-email': 'test@example.com'},
            'body': json.dumps({
                'fileSize': 1024000
                # fileName が未指定
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'missing_filename'
    
    @patch('get_upload_url.validate_user_access')
    @patch('get_upload_url.extract_user_from_event')
    def test_unsupported_file_type(self, mock_extract_user, mock_validate_access):
        """サポートされていないファイル形式のテスト"""
        # モックの設定
        mock_extract_user.return_value = 'test@example.com'
        mock_validate_access.return_value = {'authorized': True, 'message': 'Access granted'}
        
        event = {
            'headers': {'x-user-email': 'test@example.com'},
            'body': json.dumps({
                'fileName': 'test-file.pdf',  # PDFファイル（サポート外）
                'fileSize': 1024000
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'unsupported_format'
    
    @patch('get_upload_url.validate_user_access')
    @patch('get_upload_url.extract_user_from_event')
    def test_file_too_large(self, mock_extract_user, mock_validate_access):
        """ファイルサイズ制限超過のテスト"""
        # モックの設定
        mock_extract_user.return_value = 'test@example.com'
        mock_validate_access.return_value = {'authorized': True, 'message': 'Access granted'}
        
        event = {
            'headers': {'x-user-email': 'test@example.com'},
            'body': json.dumps({
                'fileName': 'large-file.xlsx',
                'fileSize': 25 * 1024 * 1024  # 25MB（制限の20MBを超過）
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'file_too_large'
    
    @patch('get_upload_url.generate_presigned_url')
    @patch('get_upload_url.validate_user_access')
    @patch('get_upload_url.extract_user_from_event')
    def test_url_generation_failure(self, mock_extract_user, mock_validate_access, mock_generate_url):
        """署名付きURL生成失敗のテスト"""
        # モックの設定
        mock_extract_user.return_value = 'test@example.com'
        mock_validate_access.return_value = {'authorized': True, 'message': 'Access granted'}
        mock_generate_url.return_value = None  # URL生成失敗
        
        event = {
            'headers': {'x-user-email': 'test@example.com'},
            'body': json.dumps({
                'fileName': 'test-file.xlsx',
                'fileSize': 1024000
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error'] == 'url_generation_failed'

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