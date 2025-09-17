"""
unlock Lambda関数のテスト
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

# Import the module under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
from unlock import lambda_handler, process_single_file

class TestUnlockHandler:
    """Excel解除Lambda関数のテストケース"""
    
    def test_lambda_handler_missing_bucket_env(self, lambda_context):
        """S3_BUCKET_NAME環境変数が設定されていない場合のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            event = {'body': '{"fileKey": "test.xlsx", "passwords": ["pass1"]}'}
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'server_configuration_error'
    
    def test_lambda_handler_invalid_json(self, lambda_context):
        """無効なJSONリクエストボディのテスト"""
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('unlock.validate_user_access') as mock_auth:
            
            mock_auth.return_value = {'authorized': True, 'message': 'Access granted'}
            event = {
                'body': 'invalid json',
                'headers': {'X-User-Email': 'test@example.com'}
            }
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'invalid_json'
    
    def test_lambda_handler_missing_parameters(self, lambda_context):
        """必須パラメータが不足している場合のテスト"""
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('unlock.validate_user_access') as mock_auth:
            
            mock_auth.return_value = {'authorized': True, 'message': 'Access granted'}
            event = {
                'body': '{}',
                'headers': {'X-User-Email': 'test@example.com'}
            }
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'missing_parameter'
    
    def test_lambda_handler_single_file_missing_filekey(self, lambda_context):
        """単一ファイル処理でfileKeyが不足している場合のテスト"""
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('unlock.validate_user_access') as mock_auth:
            
            mock_auth.return_value = {'authorized': True, 'message': 'Access granted'}
            event = {
                'body': '{"passwords": ["pass1"]}',
                'headers': {'X-User-Email': 'test@example.com'}
            }
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'missing_parameter'
    
    @mock_aws
    @patch('unlock.unlock_excel_file')
    def test_lambda_handler_single_file_success(self, mock_unlock, lambda_context, sample_excel_file):
        """単一ファイル処理の成功テスト"""
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='uploads/test.xlsx',
            Body=sample_excel_file
        )
        
        # unlock_excel_fileをモック
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(sample_excel_file)
            unlocked_path = tmp_file.name
        
        mock_unlock.return_value = {
            'success': True,
            'unlocked_file_path': unlocked_path,
            'password_used': 'testpass'
        }
        
        try:
            with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
                 patch('s3_utils.s3_client', s3_client), \
                 patch('unlock.validate_user_access') as mock_auth:
                
                mock_auth.return_value = {'authorized': True, 'message': 'Access granted'}
                event = {
                    'body': json.dumps({
                        'fileKey': 'uploads/test.xlsx',
                        'passwords': ['testpass'],
                        'fileName': 'test.xlsx'
                    }),
                    'headers': {'X-User-Email': 'test@example.com'}
                }
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'results' in body
                assert len(body['results']) == 1
                result = body['results'][0]
                assert result['status'] == 'success'
                assert 'downloadUrl' in result
                assert 'fileName' in result
        finally:
            if os.path.exists(unlocked_path):
                os.remove(unlocked_path)
    
    @mock_aws
    def test_lambda_handler_multiple_files_success(self, lambda_context, sample_excel_file):
        """複数ファイル処理の成功テスト"""
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='uploads/test1.xlsx',
            Body=sample_excel_file
        )
        s3_client.put_object(
            Bucket='test-bucket',
            Key='uploads/test2.xlsx',
            Body=sample_excel_file
        )
        
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('s3_utils.s3_client', s3_client), \
             patch('unlock.unlock_excel_file') as mock_unlock, \
             patch('unlock.validate_user_access') as mock_auth:
            
            # unlock_excel_fileをモック - 各呼び出しで新しいファイルを作成
            def create_unlocked_file(*args, **kwargs):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(sample_excel_file)
                    return {
                        'success': True,
                        'unlocked_file_path': tmp_file.name,
                        'password_used': 'testpass'
                    }
            
            mock_unlock.side_effect = create_unlocked_file
            
            try:
                mock_auth.return_value = {'authorized': True, 'message': 'Access granted'}
                event = {
                    'body': json.dumps({
                        'files': [
                            {
                                's3_key': 'uploads/test1.xlsx',
                                'original_name': 'test1.xlsx'
                            },
                            {
                                's3_key': 'uploads/test2.xlsx',
                                'original_name': 'test2.xlsx'
                            }
                        ],
                        'passwords': ['testpass']
                    }),
                    'headers': {'X-User-Email': 'test@example.com'}
                }
                response = lambda_handler(event, lambda_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'results' in body
                assert len(body['results']) == 2
                
                for result in body['results']:
                    assert result['status'] == 'success'
                    assert 'downloadUrl' in result
            finally:
                # Cleanup any remaining temporary files
                pass
    
    def test_lambda_handler_access_denied(self, lambda_context):
        """アクセス拒否のテスト"""
        with patch.dict(os.environ, {
            'S3_BUCKET_NAME': 'test-bucket',
            'ALLOWED_USERS': 'allowed@example.com'
        }, clear=False):
            event = {
                'headers': {'X-User-Email': 'denied@example.com'},
                'body': json.dumps({
                    'fileKey': 'test.xlsx',
                    'passwords': ['pass1']
                })
            }
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 403
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'access_denied'

class TestProcessSingleFile:
    """単一ファイル処理のテストケース"""
    
    @mock_aws
    def test_process_single_file_download_failure(self):
        """ダウンロード失敗のテスト"""
        # S3セットアップ（ファイルなし）
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('s3_utils.s3_client', s3_client):
            
            result = process_single_file(
                'nonexistent/test.xlsx',
                ['testpass'],
                'test.xlsx'
            )
            
            assert result['status'] == 'error'
            assert result['fileName'] == 'test_unlocked.xlsx'
            assert 'ダウンロードに失敗' in result['message']
    
    @mock_aws
    @patch('unlock.unlock_excel_file')
    def test_process_single_file_unlock_failure(self, mock_unlock, sample_excel_file):
        """解除失敗のテスト"""
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='uploads/test.xlsx',
            Body=sample_excel_file
        )
        
        # unlock_excel_fileをモック（失敗）
        mock_unlock.return_value = {
            'success': False,
            'message': 'All provided passwords failed to unlock the file.'
        }
        
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('s3_utils.s3_client', s3_client):
            
            result = process_single_file(
                'uploads/test.xlsx',
                ['wrongpass'],
                'test.xlsx'
            )
            
            assert result['status'] == 'error'
            assert result['fileName'] == 'test_unlocked.xlsx'
            assert 'パスワードでは解除できませんでした' in result['message']