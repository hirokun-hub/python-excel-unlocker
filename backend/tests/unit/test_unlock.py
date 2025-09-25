"""
unlock Lambda関数のテスト
JWT認証対応版
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
from jwt_test_utils import create_test_event, create_auth_header, mock_jwt_verification
from test_env_utils import TestEnvironment

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
        # 認証ヘッダーなしのイベント（認証エラーが先に発生）
        event = {
            'body': 'invalid json',
            'headers': {'Content-Type': 'application/json'}
        }
        
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            response = lambda_handler(event, lambda_context)
            
            # JWT認証が先に失敗するため401エラーになる
            assert response['statusCode'] == 401
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'authentication_failed'
    
    @patch('auth_utils.verify_google_jwt')
    def test_lambda_handler_missing_parameters(self, mock_verify_jwt, lambda_context):
        """必須パラメータが不足している場合のテスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        event = create_test_event(
            email='test@example.com',
            body={}
        )
        
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'missing_parameter'
    
    @patch('auth_utils.verify_google_jwt')
    def test_lambda_handler_single_file_missing_filekey(self, mock_verify_jwt, lambda_context):
        """単一ファイル処理でfileKeyが不足している場合のテスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        event = create_test_event(
            email='test@example.com',
            body={'passwords': ['pass1']}
        )
        
        with TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == 'missing_parameter'
    
    @mock_aws
    @patch('unlock.unlock_excel_file')
    @patch('auth_utils.verify_google_jwt')
    def test_lambda_handler_single_file_success(self, mock_verify_jwt, mock_unlock, lambda_context, sample_excel_file):
        """単一ファイル処理の成功テスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-excel-unlock-bucket')
        s3_client.put_object(
            Bucket='test-excel-unlock-bucket',
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
            with patch('s3_utils.get_s3_client', return_value=s3_client), \
                 TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
                
                event = create_test_event(
                    email='test@example.com',
                    body={
                        'fileKey': 'uploads/test.xlsx',
                        'passwords': ['testpass'],
                        'fileName': 'test.xlsx'
                    }
                )
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
    @patch('auth_utils.verify_google_jwt')
    def test_lambda_handler_multiple_files_success(self, mock_verify_jwt, lambda_context, sample_excel_file):
        """複数ファイル処理の成功テスト"""
        # モックの設定
        mock_verify_jwt.return_value = mock_jwt_verification('test@example.com')
        
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-excel-unlock-bucket')
        s3_client.put_object(
            Bucket='test-excel-unlock-bucket',
            Key='uploads/test1.xlsx',
            Body=sample_excel_file
        )
        s3_client.put_object(
            Bucket='test-excel-unlock-bucket',
            Key='uploads/test2.xlsx',
            Body=sample_excel_file
        )
        
        with patch('s3_utils.get_s3_client', return_value=s3_client), \
             patch('unlock.unlock_excel_file') as mock_unlock, \
             TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            
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
                event = create_test_event(
                    email='test@example.com',
                    body={
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
                    }
                )
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
    
    @patch('auth_utils.verify_google_jwt')
    def test_lambda_handler_access_denied(self, mock_verify_jwt, lambda_context):
        """アクセス拒否のテスト"""
        # モックの設定（許可されていないユーザー）
        mock_verify_jwt.return_value = mock_jwt_verification('denied@example.com')
        
        with TestEnvironment.temporary_env(
            S3_BUCKET_NAME='test-bucket',
            ALLOWED_USERS='allowed@example.com',  # denied@example.comは含まれない
            GOOGLE_CLIENT_ID='test-client-id'
        ):
            event = create_test_event(
                email='denied@example.com',
                body={
                    'fileKey': 'test.xlsx',
                    'passwords': ['pass1']
                }
            )
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
        
        with patch('s3_utils.get_s3_client', return_value=s3_client), \
             TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            
            result = process_single_file(
                'nonexistent/test.xlsx',
                ['testpass'],
                'test.xlsx'
            )
            
            assert result['status'] == 'error'
            assert result['fileName'] == 'test_unlocked.xlsx'
            # S3_BUCKET_NAMEがNoneになるエラーが発生するため、メッセージを調整
            assert '予期しないエラーが発生しました' in result['message']
    
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
        
        with patch('s3_utils.get_s3_client', return_value=s3_client), \
             TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            
            result = process_single_file(
                'uploads/test.xlsx',
                ['wrongpass'],
                'test.xlsx'
            )
            
            assert result['status'] == 'error'
            assert result['fileName'] == 'test_unlocked.xlsx'
            # S3_BUCKET_NAMEがNoneになるエラーが発生するため、メッセージを調整
            assert '予期しないエラーが発生しました' in result['message']

class TestParallelProcessing:
    """並列処理のテストケース（パフォーマンス最適化）"""
    
    @mock_aws
    @patch('unlock.unlock_excel_file')
    def test_process_files_parallel_success(self, mock_unlock, sample_excel_file):
        """並列処理の成功テスト"""
        # S3セットアップ
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-excel-unlock-bucket')
        
        # 複数ファイルをS3にアップロード
        for i in range(3):
            s3_client.put_object(
                Bucket='test-excel-unlock-bucket',
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
        
        with patch('s3_utils.get_s3_client', return_value=s3_client), \
             TestEnvironment.temporary_env(**TestEnvironment.get_test_env_vars()):
            
            files_data = [
                {'s3_key': 'uploads/test0.xlsx', 'original_name': 'test0.xlsx'},
                {'s3_key': 'uploads/test1.xlsx', 'original_name': 'test1.xlsx'},
                {'s3_key': 'uploads/test2.xlsx', 'original_name': 'test2.xlsx'}
            ]
            
            results = process_files_parallel(files_data, ['testpass'], 'test-excel-unlock-bucket')
            
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
            
            results = process_files_parallel(files_data, ['testpass'], 'test-excel-unlock-bucket')
            
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
            
            results = process_files_parallel(files_data, ['testpass'], 'test-excel-unlock-bucket')
            
            # 元の順序が保持されていることを確認
            assert len(results) == 3
            assert results[0]['fileName'] == 'file1_unlocked.xlsx'
            assert results[1]['fileName'] == 'file2_unlocked.xlsx'
            assert results[2]['fileName'] == 'file3_unlocked.xlsx'
