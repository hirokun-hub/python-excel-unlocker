import pytest
import json
import os
from unittest.mock import patch, MagicMock
from moto import mock_s3
import boto3

# Import the module under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
from main import (
    lambda_handler,
    create_response,
    generate_presigned_url,
    download_file_from_s3,
    upload_file_to_s3,
    unlock_excel_file,
    process_single_file
)

class TestLambdaHandler:
    """Test cases for the main Lambda handler function"""
    
    def test_create_response(self):
        """Test response creation utility function"""
        response = create_response(200, {'message': 'success'})
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert json.loads(response['body']) == {'message': 'success'}
    
    def test_lambda_handler_missing_bucket_env(self, lambda_context):
        """Test Lambda handler when S3_BUCKET_NAME is not set"""
        with patch.dict(os.environ, {}, clear=True):
            event = {'body': '{}'}
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
    
    def test_lambda_handler_invalid_json(self, lambda_context):
        """Test Lambda handler with invalid JSON in request body"""
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}):
            event = {'body': 'invalid json'}
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'error' in body
    
    def test_lambda_handler_missing_files(self, lambda_context):
        """Test Lambda handler when files list is missing"""
        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'}):
            event = {'body': '{}'}
            response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'error' in body

class TestS3Operations:
    """Test cases for S3 operations"""
    
    @mock_s3
    def test_generate_presigned_url(self):
        """Test presigned URL generation"""
        # Setup
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        # Test
        url = generate_presigned_url('test-bucket', 'test-key', 'get_object', 3600)
        
        assert url is not None
        assert 'test-bucket' in url
        assert 'test-key' in url
    
    @mock_s3
    def test_download_file_from_s3(self, sample_excel_file):
        """Test downloading file from S3"""
        # Setup
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='test-file.xlsx',
            Body=sample_excel_file
        )
        
        # Test
        with patch('src.main.s3_client', s3_client):
            local_path = download_file_from_s3('test-bucket', 'test-file.xlsx')
            
            assert local_path is not None
            assert os.path.exists(local_path)
            assert local_path.startswith('/tmp/')
            
            # Cleanup
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
    
    @mock_s3
    def test_upload_file_to_s3(self, sample_excel_file):
        """Test uploading file to S3"""
        # Setup
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(sample_excel_file)
            tmp_path = tmp_file.name
        
        try:
            # Test
            with patch('src.main.s3_client', s3_client):
                result = upload_file_to_s3(tmp_path, 'test-bucket', 'uploaded-file.xlsx')
                
                assert result is True
                
                # Verify file was uploaded
                response = s3_client.get_object(Bucket='test-bucket', Key='uploaded-file.xlsx')
                assert response['Body'].read() == sample_excel_file
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

class TestExcelOperations:
    """Test cases for Excel file operations"""
    
    def test_unlock_excel_file_success(self, sample_excel_file):
        """Test successful Excel file unlocking"""
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(sample_excel_file)
            tmp_path = tmp_file.name
        
        try:
            # Test with empty password (unprotected file)
            result = unlock_excel_file(tmp_path, [''])
            
            assert result['success'] is True
            assert 'unlocked_file_path' in result
            assert os.path.exists(result['unlocked_file_path'])
            
            # Cleanup
            if 'unlocked_file_path' in result and os.path.exists(result['unlocked_file_path']):
                os.remove(result['unlocked_file_path'])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_unlock_excel_file_wrong_password(self, sample_excel_file):
        """Test Excel file unlocking with wrong password"""
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(sample_excel_file)
            tmp_path = tmp_file.name
        
        try:
            # Test with wrong passwords
            result = unlock_excel_file(tmp_path, ['wrongpass1', 'wrongpass2'])
            
            assert result['success'] is False
            assert 'message' in result
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_unlock_excel_file_invalid_file(self):
        """Test Excel file unlocking with invalid file"""
        # Create temporary text file (not Excel)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(b'This is not an Excel file')
            tmp_path = tmp_file.name
        
        try:
            result = unlock_excel_file(tmp_path, ['password'])
            
            assert result['success'] is False
            assert 'message' in result
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

class TestProcessSingleFile:
    """Test cases for single file processing"""
    
    @mock_s3
    @patch('src.main.unlock_excel_file')
    def test_process_single_file_success(self, mock_unlock, sample_excel_file):
        """Test successful single file processing"""
        # Setup S3
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(
            Bucket='test-bucket',
            Key='input/test.xlsx',
            Body=sample_excel_file
        )
        
        # Mock unlock function
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(sample_excel_file)
            unlocked_path = tmp_file.name
        
        mock_unlock.return_value = {
            'success': True,
            'unlocked_file_path': unlocked_path,
            'password_used': 'testpass'
        }
        
        try:
            with patch('src.main.s3_client', s3_client), \
                 patch('src.main.S3_BUCKET_NAME', 'test-bucket'):
                
                result = process_single_file(
                    'input/test.xlsx',
                    ['testpass'],
                    'test.xlsx'
                )
                
                assert result['status'] == 'success'
                assert result['original_filename'] == 'test.xlsx'
                assert 'download_url' in result
        finally:
            if os.path.exists(unlocked_path):
                os.remove(unlocked_path)
    
    @mock_s3
    def test_process_single_file_download_failure(self):
        """Test single file processing when download fails"""
        # Setup S3 without the file
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        
        with patch('src.main.s3_client', s3_client), \
             patch('src.main.S3_BUCKET_NAME', 'test-bucket'):
            
            result = process_single_file(
                'nonexistent/test.xlsx',
                ['testpass'],
                'test.xlsx'
            )
            
            assert result['status'] == 'error'
            assert result['original_filename'] == 'test.xlsx'
            assert 'message' in result