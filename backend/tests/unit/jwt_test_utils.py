"""
テスト用JWT生成ユーティリティ
JWT認証のテストをサポートするためのヘルパー関数
"""
import jwt
import time
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class JWTTestHelper:
    """テスト用JWT生成・検証ヘルパークラス"""
    
    def __init__(self):
        """RSA鍵ペアを生成してテスト用に保持"""
        # テスト用RSA鍵ペア生成
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # PEM形式に変換
        self.private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        self.public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def generate_test_jwt(
        self,
        email: str = 'test@example.com',
        client_id: str = 'test-client-id',
        exp_minutes: int = 60,
        **extra_claims
    ) -> str:
        """
        テスト用のJWTトークンを生成
        
        Args:
            email: ユーザーのメールアドレス
            client_id: Google Client ID
            exp_minutes: 有効期限（分）
            **extra_claims: 追加のクレーム
        
        Returns:
            生成されたJWTトークン
        """
        now = int(time.time())
        
        payload = {
            'iss': 'https://accounts.google.com',
            'aud': client_id,
            'sub': '1234567890',
            'email': email,
            'email_verified': True,
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
            'iat': now,
            'exp': now + (exp_minutes * 60),
            **extra_claims
        }
        
        # RS256でJWTを生成
        token = jwt.encode(
            payload,
            self.private_pem,
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        return token
    
    def generate_expired_jwt(self, email: str = 'test@example.com') -> str:
        """期限切れのJWTトークンを生成"""
        return self.generate_test_jwt(email=email, exp_minutes=-10)
    
    def generate_invalid_jwt(self) -> str:
        """無効なJWTトークンを生成"""
        return "invalid.jwt.token"
    
    def create_auth_header(self, email: str = 'test@example.com') -> str:
        """Authorization Bearerヘッダー用の文字列を生成"""
        token = self.generate_test_jwt(email=email)
        return f"Bearer {token}"
    
    def create_test_event_with_auth(
        self,
        email: str = 'test@example.com',
        body: Optional[Dict[str, Any]] = None,
        **extra_headers
    ) -> Dict[str, Any]:
        """
        認証ヘッダー付きのテストイベントを生成
        
        Args:
            email: ユーザーのメールアドレス
            body: リクエストボディ
            **extra_headers: 追加のヘッダー
        
        Returns:
            テストイベント辞書
        """
        import json
        
        headers = {
            'Authorization': self.create_auth_header(email),
            'Content-Type': 'application/json',
            **extra_headers
        }
        
        event = {
            'headers': headers,
            'httpMethod': 'POST',
            'path': '/test',
            'queryStringParameters': None,
            'pathParameters': None,
            'requestContext': {
                'requestId': 'test-request-id',
                'stage': 'test'
            }
        }
        
        if body is not None:
            event['body'] = json.dumps(body)
        
        return event


# グローバルインスタンス（テスト間で共有）
jwt_helper = JWTTestHelper()


def create_test_jwt(email: str = 'test@example.com', **kwargs) -> str:
    """テスト用JWT生成の便利関数"""
    return jwt_helper.generate_test_jwt(email=email, **kwargs)


def create_auth_header(email: str = 'test@example.com') -> str:
    """Authorization Bearerヘッダー生成の便利関数"""
    return jwt_helper.create_auth_header(email=email)


def create_test_event(
    email: str = 'test@example.com',
    body: Optional[Dict[str, Any]] = None,
    **extra_headers
) -> Dict[str, Any]:
    """認証付きテストイベント生成の便利関数"""
    return jwt_helper.create_test_event_with_auth(
        email=email,
        body=body,
        **extra_headers
    )


def mock_jwt_verification(email: str = 'test@example.com'):
    """
    JWT検証をモックするためのデコレータ用関数
    
    Args:
        email: モックで返すメールアドレス
    
    Returns:
        モック用の辞書
    """
    return {
        'iss': 'https://accounts.google.com',
        'aud': 'test-client-id',
        'sub': '1234567890',
        'email': email,
        'email_verified': True,
        'name': 'Test User',
        'given_name': 'Test',
        'family_name': 'User',
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600
    }