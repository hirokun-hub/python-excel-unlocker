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
from unlock import lambda_handler, process_single_file, process_files_parallel

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

class TestParallelProcessing:
    """並列処理のテストケース（パフォーマンス最適化）"""
    
    @mock_aws
    @patch('unlock.unlock_excel_file')
    def test_process_files_parallel_success(self, mock_unlock, sample_excel_file):
        """並列処理の成功テスト"""
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        # 複数ファイルをS3にアップロード
        for i in range(3):
            s3_client.put_object(
                Bucket='test-bucket',
                Key=f'uploads/test{i}.xlsx',
                Body=sample_excel_file
            )
        
        # unlock_excel_fileをモック
        def create_unlocked_file(*args, **kwargs):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(sample_excel_file)
                return {
                    'success': True,
                    'unlocked_file_path': tmp_file.name,
                    'password_used': 'testpass'
                }
        
        mock_unlock.side_effect = create_unlocked_file
        
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}, clear=False), \
             patch('s3_utils.s3_client', s3_client):
            
            files_data = [
                {'s3_key': 'uploads/test0.xlsx', 'original_name': 'test0.xlsx'},
                {'s3_key': 'uploads/test1.xlsx', 'original_name': 'test1.xlsx'},
                {'s3_key': 'uploads/test2.xlsx', 'original_name': 'test2.xlsx'}
            ]
            
            results = process_files_parallel(files_data, ['testpass'], 'test-bucket')
            
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result['status'] == 'success'
                assert result['fileName'] == f'test{i}_unlocked.xlsx'
                assert 'downloadUrl' in result
    
    def test_process_files_parallel_mixed_results(self):
        """並列処理での混合結果テスト（成功・失敗混在）"""
        files_data = [
            {'s3_key': 'uploads/valid.xlsx', 'original_name': 'valid.xlsx'},
            {'original_name': 'missing_key.xlsx'},  # s3_keyなし
            {'s3_key': 'uploads/another.xlsx', 'original_name': 'another.xlsx'}
        ]
        
        with patch('unlock.process_single_file') as mock_process:
            # 最初と3番目のファイルは成功、2番目は即座にエラー
            mock_process.side_effect = [
                {'fileName': 'valid_unlocked.xlsx', 'status': 'success', 'downloadUrl': 'http://example.com/valid'},
                {'fileName': 'another_unlocked.xlsx', 'status': 'success', 'downloadUrl': 'http://example.com/another'}
            ]
            
            results = process_files_parallel(files_data, ['testpass'], 'test-bucket')
            
            assert len(results) == 3
            assert results[0]['status'] == 'success'
            assert results[1]['status'] == 'error'
            assert 'S3キーが見つかりません' in results[1]['message']
            assert results[2]['status'] == 'success'
    
    def test_process_files_parallel_maintains_order(self):
        """並列処理で元の順序が保持されることのテスト"""
        files_data = [
            {'s3_key': 'uploads/file1.xlsx', 'original_name': 'file1.xlsx'},
            {'s3_key': 'uploads/file2.xlsx', 'original_name': 'file2.xlsx'},
            {'s3_key': 'uploads/file3.xlsx', 'original_name': 'file3.xlsx'}
        ]
        
        with patch('unlock.process_single_file') as mock_process:
            # 処理時間をシミュレート（逆順で完了）
            def slow_process(s3_key, passwords, original_name, bucket):
                import time
                if 'file1' in original_name:
                    time.sleep(0.3)  # 最も遅い
                elif 'file2' in original_name:
                    time.sleep(0.2)  # 中間
                else:
                    time.sleep(0.1)  # 最も早い
                
                return {
                    'fileName': f"{original_name.split('.')[0]}_unlocked.xlsx",
                    'status': 'success',
                    'downloadUrl': f'http://example.com/{original_name}'
                }
            
            mock_process.side_effect = slow_process
            
            results = process_files_parallel(files_data, ['testpass'], 'test-bucket')
            
            # 元の順序が保持されていることを確認
            assert len(results) == 3
            assert results[0]['fileName'] == 'file1_unlocked.xlsx'
            assert results[1]['fileName'] == 'file2_unlocked.xlsx'
            assert results[2]['fileName'] == 'file3_unlocked.xlsx'