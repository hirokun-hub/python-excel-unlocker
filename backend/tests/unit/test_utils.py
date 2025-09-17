"""
共通ユーティリティ関数のテスト
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

# Import the modules under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
from s3_utils import (
    generate_presigned_url,
    download_file_from_s3,
    upload_file_to_s3,
    generate_unique_key
)
from excel_utils import unlock_excel_file, validate_excel_file
from auth_utils import get_allowed_users, validate_user_access, extract_user_from_event
from response_utils import create_response, create_error_response, create_success_response

class TestS3Utils:
    """S3ユーティリティ関数のテストケース"""
    
    @mock_aws
    def test_generate_presigned_url_success(self):
        """署名付きURL生成の成功テスト"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('s3_utils.s3_client', s3_client):
            url = generate_presigned_url('test-bucket', 'test-key', 'get_object', 3600)
            
            assert url is not None
            assert 'test-bucket' in url
            assert 'test-key' in url
    
    @mock_aws
    def test_download_file_from_s3_success(self, sample_excel_file):
        """S3ファイルダウンロードの成功テスト"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='test-file.xlsx',
            Body=sample_excel_file
        )
        
        with patch('s3_utils.s3_client', s3_client):
            local_path = download_file_from_s3('test-bucket', 'test-file.xlsx')
            
            assert local_path is not None
            assert os.path.exists(local_path)
            assert local_path.startswith('/tmp/')
            
            # クリーンアップ
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
    
    @mock_aws
    def test_upload_file_to_s3_success(self, sample_excel_file):
        """S3ファイルアップロードの成功テスト"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(sample_excel_file)
            tmp_path = tmp_file.name
        
        try:
            with patch('s3_utils.s3_client', s3_client):
                result = upload_file_to_s3(tmp_path, 'test-bucket', 'uploaded-file.xlsx')
                
                assert result is True
                
                # アップロードされたファイルを確認
                response = s3_client.get_object(Bucket='test-bucket', Key='uploaded-file.xlsx')
                assert response['Body'].read() == sample_excel_file
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_generate_unique_key(self):
        """ユニークキー生成のテスト"""
        key1 = generate_unique_key('uploads', 'test.xlsx')
        key2 = generate_unique_key('uploads', 'test.xlsx')
        
        assert key1 != key2
        assert key1.startswith('uploads/')
        assert key1.endswith('.xlsx')
        assert key2.startswith('uploads/')
        assert key2.endswith('.xlsx')

class TestExcelUtils:
    """Excelユーティリティ関数のテストケース"""
    
    def test_validate_excel_file_success(self, sample_excel_file):
        """Excelファイル検証の成功テスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(sample_excel_file)
            tmp_path = tmp_file.name
        
        try:
            result = validate_excel_file(tmp_path)
            
            assert result['valid'] is True
            assert result['file_type'] == '.xlsx'
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_validate_excel_file_unsupported_format(self):
        """サポートされていないファイル形式のテスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(b'This is not an Excel file')
            tmp_path = tmp_file.name
        
        try:
            result = validate_excel_file(tmp_path)
            
            assert result['valid'] is False
            assert result['file_type'] == '.txt'
            assert 'Unsupported file format' in result['message']
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_validate_excel_file_not_exists(self):
        """存在しないファイルのテスト"""
        result = validate_excel_file('/nonexistent/file.xlsx')
        
        assert result['valid'] is False
        assert result['file_type'] is None
        assert 'File does not exist' in result['message']
    
    def test_unlock_excel_file_success(self, sample_excel_file):
        """Excel解除の成功テスト（パスワードなしファイル）"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(sample_excel_file)
            tmp_path = tmp_file.name
        
        try:
            result = unlock_excel_file(tmp_path, [''])
            
            assert result['success'] is True
            assert 'unlocked_file_path' in result
            assert os.path.exists(result['unlocked_file_path'])
            
            # クリーンアップ
            if 'unlocked_file_path' in result and os.path.exists(result['unlocked_file_path']):
                os.remove(result['unlocked_file_path'])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

class TestAuthUtils:
    """認証ユーティリティ関数のテストケース"""
    
    def test_get_allowed_users_empty(self):
        """許可ユーザーリストが空の場合のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            users = get_allowed_users()
            assert users == []
    
    def test_get_allowed_users_single(self):
        """単一ユーザーのテスト"""
        with patch.dict(os.environ, {'ALLOWED_USERS': 'user@example.com'}):
            users = get_allowed_users()
            assert users == ['user@example.com']
    
    def test_get_allowed_users_multiple(self):
        """複数ユーザーのテスト"""
        with patch.dict(os.environ, {'ALLOWED_USERS': 'user1@example.com,user2@example.com'}):
            users = get_allowed_users()
            assert users == ['user1@example.com', 'user2@example.com']
    
    def test_validate_user_access_no_email(self):
        """メールアドレスなしのテスト"""
        result = validate_user_access(None)
        assert result['authorized'] is False
        assert 'not provided' in result['message']
    
    def test_validate_user_access_development_mode(self):
        """開発モード（許可ユーザーリストなし）のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_user_access('any@example.com')
            assert result['authorized'] is True
            assert 'Development mode' in result['message']
    
    def test_validate_user_access_authorized(self):
        """認証済みユーザーのテスト"""
        with patch.dict(os.environ, {'ALLOWED_USERS': 'user@example.com'}):
            result = validate_user_access('user@example.com')
            assert result['authorized'] is True
    
    def test_validate_user_access_denied(self):
        """アクセス拒否のテスト"""
        with patch.dict(os.environ, {'ALLOWED_USERS': 'allowed@example.com'}):
            result = validate_user_access('denied@example.com')
            assert result['authorized'] is False
            assert 'Access denied' in result['message']
    
    def test_extract_user_from_event_success(self):
        """イベントからユーザー抽出の成功テスト"""
        event = {
            'headers': {
                'X-User-Email': 'user@example.com'
            }
        }
        user_email = extract_user_from_event(event)
        assert user_email == 'user@example.com'
    
    def test_extract_user_from_event_case_insensitive(self):
        """大文字小文字を考慮しないヘッダー検索のテスト"""
        event = {
            'headers': {
                'x-user-email': 'user@example.com'
            }
        }
        user_email = extract_user_from_event(event)
        assert user_email == 'user@example.com'
    
    def test_extract_user_from_event_not_found(self):
        """ユーザー情報が見つからない場合のテスト"""
        event = {
            'headers': {}
        }
        user_email = extract_user_from_event(event)
        assert user_email is None

class TestResponseUtils:
    """レスポンスユーティリティ関数のテストケース"""
    
    def test_create_response(self):
        """基本レスポンス作成のテスト"""
        response = create_response(200, {'message': 'success'})
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        import json
        body = json.loads(response['body'])
        assert body == {'message': 'success'}
    
    def test_create_error_response(self):
        """エラーレスポンス作成のテスト"""
        response = create_error_response(400, 'invalid_input', 'Invalid input provided', 'Please check your input')
        
        assert response['statusCode'] == 400
        
        import json
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'invalid_input'
        assert body['message'] == 'Invalid input provided'
        assert body['suggestion'] == 'Please check your input'
    
    def test_create_success_response(self):
        """成功レスポンス作成のテスト"""
        data = {'result': 'processed', 'count': 5}
        response = create_success_response(data)
        
        assert response['statusCode'] == 200
        
        import json
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['result'] == 'processed'
        assert body['count'] == 5