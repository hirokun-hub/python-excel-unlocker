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
    generate_unique_key,
    sanitize_for_log,
    cleanup_local_file,
    cleanup_s3_object
)
from excel_utils import unlock_excel_file, validate_excel_file, sanitize_password_for_log, sanitize_filename_for_log
from auth_utils import get_allowed_users, validate_user_access, extract_user_from_event, sanitize_email_for_log
from response_utils import create_response, create_error_response, create_success_response, sanitize_error_message_for_log

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

class TestJWTAuth:
    """JWT認証機能のテストケース"""
    
    @patch('auth_utils.requests.get')
    def test_get_google_public_keys_success(self, mock_get):
        """Google公開鍵取得の成功テスト"""
        from auth_utils import get_google_public_keys
        
        # モックレスポンス
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'keys': [
                {
                    'kid': 'test-kid',
                    'n': 'test-n',
                    'e': 'AQAB'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # キャッシュをクリア
        get_google_public_keys.cache_clear()
        
        keys = get_google_public_keys()
        assert 'keys' in keys
        assert len(keys['keys']) == 1
        assert keys['keys'][0]['kid'] == 'test-kid'
    
    @patch('auth_utils.requests.get')
    def test_get_google_public_keys_failure(self, mock_get):
        """Google公開鍵取得の失敗テスト"""
        from auth_utils import get_google_public_keys
        
        # モックでエラーを発生させる
        mock_get.side_effect = Exception("Network error")
        
        # キャッシュをクリア
        get_google_public_keys.cache_clear()
        
        with pytest.raises(Exception):
            get_google_public_keys()
    
    @patch('auth_utils.get_google_public_keys')
    @patch('auth_utils.jwt.decode')
    @patch('auth_utils.jwt.get_unverified_header')
    def test_verify_google_jwt_success(self, mock_get_header, mock_decode, mock_get_keys):
        """JWT検証の成功テスト"""
        from auth_utils import verify_google_jwt
        
        # モックデータ
        mock_get_header.return_value = {'kid': 'test-kid'}
        mock_get_keys.return_value = {
            'keys': [
                {
                    'kid': 'test-kid',
                    'n': 'test-n-value',
                    'e': 'AQAB'
                }
            ]
        }
        mock_decode.return_value = {
            'email': 'user@example.com',
            'iss': 'https://accounts.google.com',
            'aud': 'test-client-id'
        }
        
        with patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test-client-id'}):
            result = verify_google_jwt('test-token')
            
            assert result['email'] == 'user@example.com'
            assert result['iss'] == 'https://accounts.google.com'
    
    @patch('auth_utils.jwt.get_unverified_header')
    def test_verify_google_jwt_missing_kid(self, mock_get_header):
        """JWT検証でkidが見つからない場合のテスト"""
        from auth_utils import verify_google_jwt
        from jwt.exceptions import InvalidTokenError
        
        mock_get_header.return_value = {}  # kidなし
        
        with pytest.raises(InvalidTokenError):
            verify_google_jwt('test-token')
    
    def test_extract_user_from_event_jwt_success(self):
        """JWT認証でのユーザー抽出成功テスト"""
        with patch('auth_utils.verify_google_jwt') as mock_verify:
            mock_verify.return_value = {'email': 'user@example.com'}
            
            event = {
                'headers': {
                    'Authorization': 'Bearer test-jwt-token'
                }
            }
            
            user_email = extract_user_from_event(event)
            assert user_email == 'user@example.com'
            mock_verify.assert_called_once_with('test-jwt-token')
    
    def test_extract_user_from_event_jwt_no_auth_header(self):
        """JWT認証でAuthorizationヘッダーがない場合のテスト"""
        event = {
            'headers': {}
        }
        
        user_email = extract_user_from_event(event)
        assert user_email is None
    
    def test_extract_user_from_event_jwt_invalid_bearer(self):
        """JWT認証で無効なBearerトークンの場合のテスト"""
        event = {
            'headers': {
                'Authorization': 'Invalid token-format'
            }
        }
        
        user_email = extract_user_from_event(event)
        assert user_email is None
    
    def test_extract_user_from_event_jwt_verification_failed(self):
        """JWT検証が失敗した場合のテスト"""
        from jwt.exceptions import InvalidTokenError
        
        with patch('auth_utils.verify_google_jwt') as mock_verify:
            mock_verify.side_effect = InvalidTokenError("Invalid token")
            
            event = {
                'headers': {
                    'Authorization': 'Bearer invalid-jwt-token'
                }
            }
            
            user_email = extract_user_from_event(event)
            assert user_email is None
    
    def test_extract_user_from_event_jwt_no_email(self):
        """JWT検証は成功したがemailがない場合のテスト"""
        with patch('auth_utils.verify_google_jwt') as mock_verify:
            mock_verify.return_value = {'sub': '123456789'}  # emailなし
            
            event = {
                'headers': {
                    'Authorization': 'Bearer test-jwt-token'
                }
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
        # CORS厳格化：デフォルトはlocalhostになる
        assert response['headers']['Access-Control-Allow-Origin'] == 'https://localhost:3000'
        
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
    
    def test_create_auth_error_response_default(self):
        """認証エラーレスポンス作成のテスト（デフォルト）"""
        from response_utils import create_auth_error_response
        
        response = create_auth_error_response()
        
        assert response['statusCode'] == 401
        
        import json
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'authentication_failed'
        assert '認証に失敗しました' in body['message']
        assert '再ログイン' in body['suggestion']
    
    def test_create_auth_error_response_token_expired(self):
        """認証エラーレスポンス作成のテスト（トークン期限切れ）"""
        from response_utils import create_auth_error_response
        
        response = create_auth_error_response("token_expired")
        
        assert response['statusCode'] == 401
        
        import json
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'token_expired'
        assert '有効期限が切れています' in body['message']
    
    def test_create_auth_error_response_unauthorized(self):
        """認証エラーレスポンス作成のテスト（権限なし）"""
        from response_utils import create_auth_error_response
        
        response = create_auth_error_response("unauthorized")
        
        assert response['statusCode'] == 401
        
        import json
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'unauthorized'
        assert '権限がありません' in body['message']
        assert '管理者に' in body['suggestion']

class TestSecurityFeatures:
    """セキュリティ強化機能のテストケース"""
    
    def test_sanitize_for_log(self):
        """S3ログサニタイズのテスト"""
        # 署名付きURLのサニタイズ
        url_with_params = "https://s3.amazonaws.com/bucket/file.xlsx?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&Expires=1234567890&Signature=example"
        sanitized = sanitize_for_log(url_with_params)
        assert "?[REDACTED]" in sanitized
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        
        # 日本語ファイル名のサニタイズ
        japanese_filename = "重要な資料_2024年度.xlsx"
        sanitized = sanitize_for_log(japanese_filename)
        assert "[FILENAME_REDACTED]" in sanitized
        assert "重要な資料" not in sanitized
    
    def test_sanitize_password_for_log(self):
        """パスワードログサニタイズのテスト"""
        password = "secret123"
        sanitized = sanitize_password_for_log(password)
        assert sanitized == "*" * len(password)
        
        empty_password = ""
        sanitized = sanitize_password_for_log(empty_password)
        assert sanitized == "[EMPTY]"
    
    def test_sanitize_filename_for_log(self):
        """ファイル名ログサニタイズのテスト"""
        # 日本語を含むファイル名
        filename = "売上データ_20241201.xlsx"
        sanitized = sanitize_filename_for_log(filename)
        assert "[REDACTED]" in sanitized
        assert "売上データ" not in sanitized
        
        # 数字の連続（ID、日付等）
        filename_with_numbers = "report_12345678.xlsx"
        sanitized = sanitize_filename_for_log(filename_with_numbers)
        assert "[NUMBERS_REDACTED]" in sanitized
        assert "12345678" not in sanitized
    
    def test_sanitize_email_for_log(self):
        """メールアドレスログサニタイズのテスト"""
        email = "user@example.com"
        sanitized = sanitize_email_for_log(email)
        assert sanitized == "u**r@example.com"
        
        short_email = "ab@example.com"
        sanitized = sanitize_email_for_log(short_email)
        assert sanitized == "**@example.com"
        
        invalid_email = "invalid-email"
        sanitized = sanitize_email_for_log(invalid_email)
        assert sanitized == "[INVALID_EMAIL]"
    
    def test_sanitize_error_message_for_log(self):
        """エラーメッセージログサニタイズのテスト"""
        # 一時ファイルパスを含むメッセージ
        message = "Failed to process /tmp/uuid-重要ファイル.xlsx"
        sanitized = sanitize_error_message_for_log(message)
        assert "[TEMP_FILE_REDACTED]" in sanitized
        assert "/tmp/uuid-重要ファイル.xlsx" not in sanitized
        
        # S3パスを含むメッセージ
        message = "Cannot access s3://bucket/uploads/secret-file.xlsx"
        sanitized = sanitize_error_message_for_log(message)
        assert "[S3_PATH_REDACTED]" in sanitized
        assert "s3://bucket/uploads/secret-file.xlsx" not in sanitized
    
    def test_cleanup_local_file(self):
        """ローカルファイル削除のテスト"""
        # テスト用一時ファイル作成
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_path = tmp_file.name
        
        # ファイルが存在することを確認
        assert os.path.exists(tmp_path)
        
        # 削除実行
        result = cleanup_local_file(tmp_path)
        
        # 削除成功とファイルが存在しないことを確認
        assert result is True
        assert not os.path.exists(tmp_path)
    
    def test_cleanup_local_file_nonexistent(self):
        """存在しないファイルの削除テスト"""
        result = cleanup_local_file("/nonexistent/file.txt")
        assert result is True  # 存在しないファイルは成功扱い
    
    @mock_aws
    def test_cleanup_s3_object(self):
        """S3オブジェクト削除のテスト"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')
        s3_client.put_object(Bucket='test-bucket', Key='test-file.txt', Body=b'test content')
        
        with patch('s3_utils.s3_client', s3_client):
            # オブジェクトが存在することを確認
            response = s3_client.list_objects_v2(Bucket='test-bucket')
            assert 'Contents' in response
            
            # 削除実行
            result = cleanup_s3_object('test-bucket', 'test-file.txt')
            
            # 削除成功とオブジェクトが存在しないことを確認
            assert result is True
            response = s3_client.list_objects_v2(Bucket='test-bucket')
            assert 'Contents' not in response
    
    def test_response_security_headers(self):
        """レスポンスセキュリティヘッダーのテスト"""
        response = create_response(200, {'message': 'test'})
        headers = response['headers']
        
        # セキュリティヘッダーの存在確認
        assert 'X-Content-Type-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in headers
        assert headers['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in headers
        assert headers['X-XSS-Protection'] == '1; mode=block'
        assert 'Strict-Transport-Security' in headers
        assert 'max-age=31536000' in headers['Strict-Transport-Security']
        assert 'Content-Security-Policy' in headers
        assert "default-src 'self'" in headers['Content-Security-Policy']

class TestCORSStrictMode:
    """CORS設定厳格化のテストケース"""
    
    def test_get_allowed_origin_single_value(self):
        """単一オリジン設定のテスト"""
        from response_utils import get_allowed_origin
        
        with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://example.com'}):
            origin = get_allowed_origin()
            assert origin == 'https://example.com'
    
    def test_get_allowed_origin_default(self):
        """デフォルトオリジンのテスト"""
        from response_utils import get_allowed_origin
        
        with patch.dict(os.environ, {}, clear=True):
            origin = get_allowed_origin()
            assert origin == 'https://localhost:3000'
    
    def test_get_allowed_origin_with_spaces(self):
        """スペースを含むオリジン設定のテスト"""
        from response_utils import get_allowed_origin
        
        with patch.dict(os.environ, {'ALLOWED_ORIGIN': ' https://example.com '}):
            origin = get_allowed_origin()
            assert origin == 'https://example.com'
    
    def test_cors_strict_response(self):
        """CORS厳格化レスポンスのテスト"""
        with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://secure-app.com'}):
            response = create_response(200, {'message': 'test'})
            headers = response['headers']
            
            # CORS設定の確認
            assert 'Access-Control-Allow-Origin' in headers
            assert headers['Access-Control-Allow-Origin'] == 'https://secure-app.com'
            assert headers['Access-Control-Allow-Methods'] == 'GET,POST,OPTIONS'
            assert headers['Access-Control-Allow-Credentials'] == 'true'
            
            # ワイルドカードが使用されていないことを確認
            assert '*' not in headers['Access-Control-Allow-Origin']
    
    def test_cors_no_wildcard_in_production(self):
        """本番環境でワイルドカードが使用されていないことのテスト"""
        with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://production-app.com', 'ENVIRONMENT': 'production'}):
            response = create_response(200, {'message': 'test'})
            headers = response['headers']
            
            # ワイルドカードの不使用を確認
            assert headers['Access-Control-Allow-Origin'] != '*'
            assert 'https://production-app.com' == headers['Access-Control-Allow-Origin']
    
    def test_wildcard_origin_fallback(self):
        """ワイルドカードオリジンが設定された場合のフォールバックテスト"""
        from response_utils import get_allowed_origin
        
        with patch.dict(os.environ, {'ALLOWED_ORIGIN': '*'}):
            origin = get_allowed_origin()
            # ワイルドカードは拒否され、localhostにフォールバック
            assert origin == 'https://localhost:3000'
    
    def test_production_https_enforcement(self):
        """本番環境でHTTPS強制のテスト"""
        from response_utils import get_allowed_origin
        import pytest
        
        with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'http://insecure-app.com', 'ENVIRONMENT': 'production'}):
            with pytest.raises(ValueError, match="Production environment requires HTTPS origins"):
                get_allowed_origin()