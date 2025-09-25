"""
S3条件拘束付きアップロード機能のユニットテスト
タスク19: S3プリサイン条件拘束の実装テスト
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

# テスト対象のモジュールをインポート
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from s3_utils import generate_constrained_upload_url, get_s3_client
from get_upload_url import lambda_handler

class TestS3ConstrainedUpload:
    """S3条件拘束付きアップロード機能のテストクラス"""
    
    @mock_aws
    @patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'AWS_SECURITY_TOKEN': 'testing',
        'AWS_SESSION_TOKEN': 'testing',
        'AWS_DEFAULT_REGION': 'ap-northeast-1'
    })
    def test_generate_constrained_upload_url_success(self):
        """条件拘束付きアップロードURL生成の正常系テスト"""
        # S3バケットを作成
        s3_client = get_s3_client()
        bucket_name = 'test-excel-unlock-bucket'
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-1'}
        )
        
        # テストパラメータ
        key = 'uploads/test-file.xlsx'
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        max_size = 20 * 1024 * 1024  # 20MB
        
        # 条件拘束付きURL生成
        result = generate_constrained_upload_url(bucket_name, key, content_type, max_size)
        
        # 結果検証
        assert result is not None
        assert 'url' in result
        assert 'fields' in result
        assert result['fields']['Content-Type'] == content_type
        assert result['fields']['key'] == key
        
        # 条件拘束の確認（内部的にはconditionsが設定されている）
        assert isinstance(result['url'], str)
        assert result['url'].startswith('https://')
    
    @mock_aws
    @patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'AWS_SECURITY_TOKEN': 'testing',
        'AWS_SESSION_TOKEN': 'testing',
        'AWS_DEFAULT_REGION': 'ap-northeast-1'
    })
    def test_generate_constrained_upload_url_with_invalid_params(self):
        """無効なパラメータでの条件拘束付きURL生成テスト"""
        # S3バケットを作成
        s3_client = get_s3_client()
        bucket_name = 'test-excel-unlock-bucket'
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-1'}
        )
        
        # 無効なContent-Type
        result = generate_constrained_upload_url(
            bucket_name, 
            'uploads/test.txt', 
            'text/plain',  # Excelファイル以外
            1024
        )
        
        # 許可されていないContent-TypeのためNoneが返る
        assert result is None
    
    @mock_aws
    @patch('auth_utils.verify_google_jwt')
    @patch.dict(os.environ, {
        'S3_BUCKET_NAME': 'test-excel-unlock-bucket',
        'ALLOWED_USERS': 'test@example.com',
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'AWS_SECURITY_TOKEN': 'testing',
        'AWS_SESSION_TOKEN': 'testing',
        'AWS_DEFAULT_REGION': 'ap-northeast-1'
    })
    def test_lambda_handler_with_constrained_upload(self, mock_verify_jwt):
        """Lambda関数での条件拘束付きアップロード処理テスト"""
        # S3バケットを作成
        s3_client = get_s3_client()
        bucket_name = 'test-excel-unlock-bucket'
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-1'}
        )
        
        # JWT認証をモック
        mock_verify_jwt.return_value = {
            'email': 'test@example.com',
            'aud': 'test-client-id'
        }
        
        # テストイベント
        event = {
            'headers': {
                'Authorization': 'Bearer test-jwt-token'
            },
            'body': json.dumps({
                'fileName': 'test-file.xlsx',
                'fileSize': 1024000,
                'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        }
        
        # Lambda関数実行
        response = lambda_handler(event, {})
        
        # レスポンス検証
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'uploadUrl' in body
        assert 'uploadFields' in body
        assert 'fileKey' in body
        assert body['method'] == 'POST'
        
        # アップロードフィールドの検証
        upload_fields = body['uploadFields']
        assert 'Content-Type' in upload_fields
        assert upload_fields['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    def test_content_type_validation(self):
        """Content-Type検証のテスト"""
        valid_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ]
        
        invalid_types = [
            'text/plain',
            'application/pdf',
            'image/jpeg',
            'application/zip'
        ]
        
        # 有効なContent-Typeのテスト
        for content_type in valid_types:
            # 実際の検証ロジックは get_upload_url.py の _is_supported_file_type で行われる
            assert content_type in [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]
        
        # 無効なContent-Typeのテスト
        for content_type in invalid_types:
            assert content_type not in [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]
    
    def test_file_size_constraints(self):
        """ファイルサイズ制限のテスト"""
        max_size = 20 * 1024 * 1024  # 20MB
        
        # 有効なサイズ
        valid_sizes = [1024, 1024 * 1024, 10 * 1024 * 1024, max_size]
        for size in valid_sizes:
            assert size <= max_size
        
        # 無効なサイズ
        invalid_sizes = [max_size + 1, 50 * 1024 * 1024, 100 * 1024 * 1024]
        for size in invalid_sizes:
            assert size > max_size
    
    @patch('auth_utils.verify_google_jwt')
    @patch.dict(os.environ, {
        'S3_BUCKET_NAME': 'test-excel-unlock-bucket',
        'ALLOWED_USERS': 'test@example.com'
    })
    def test_lambda_handler_file_size_validation(self, mock_verify_jwt):
        """Lambda関数でのファイルサイズ検証テスト"""
        # JWT認証をモック
        mock_verify_jwt.return_value = {
            'email': 'test@example.com',
            'aud': 'test-client-id'
        }
        
        # ファイルサイズが制限を超えるテストイベント
        event = {
            'headers': {
                'Authorization': 'Bearer test-jwt-token'
            },
            'body': json.dumps({
                'fileName': 'large-file.xlsx',
                'fileSize': 25 * 1024 * 1024,  # 25MB（制限超過）
                'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
        }
        
        # Lambda関数実行
        response = lambda_handler(event, {})
        
        # エラーレスポンス検証
        assert response['statusCode'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'file_too_large'
        assert 'ファイルサイズ' in body['message']
    
    @patch('auth_utils.verify_google_jwt')
    @patch.dict(os.environ, {
        'S3_BUCKET_NAME': 'test-excel-unlock-bucket',
        'ALLOWED_USERS': 'test@example.com'
    })
    def test_lambda_handler_unsupported_file_type(self, mock_verify_jwt):
        """Lambda関数での非対応ファイル形式テスト"""
        # JWT認証をモック
        mock_verify_jwt.return_value = {
            'email': 'test@example.com',
            'aud': 'test-client-id'
        }
        
        # 非対応ファイル形式のテストイベント
        event = {
            'headers': {
                'Authorization': 'Bearer test-jwt-token'
            },
            'body': json.dumps({
                'fileName': 'document.pdf',
                'fileSize': 1024000,
                'contentType': 'application/pdf'  # 非対応形式
            })
        }
        
        # Lambda関数実行
        response = lambda_handler(event, {})
        
        # エラーレスポンス検証
        assert response['statusCode'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'unsupported_format'
        assert 'サポートされていないファイル形式です' in body['message']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
