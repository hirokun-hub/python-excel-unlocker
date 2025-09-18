"""
認証チェックの共通ユーティリティ関数
JWT認証対応：Google ID Tokenの検証機能
セキュリティ強化：機密情報のログ除外
"""
import logging
import os
from typing import Dict, Any, Optional
import re
import jwt
import requests
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import json
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

def sanitize_email_for_log(email: str) -> str:
    """
    セキュリティ強化：メールアドレスをログ出力用にサニタイズする
    
    Args:
        email: サニタイズ対象のメールアドレス
    
    Returns:
        サニタイズされたメールアドレス
    """
    if not email:
        return email
    
    # メールアドレスの@より前の部分を部分的にマスク
    if '@' in email:
        local, domain = email.split('@', 1)
        if len(local) > 2:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        else:
            masked_local = '*' * len(local)
        return f"{masked_local}@{domain}"
    else:
        return '[INVALID_EMAIL]'

def get_allowed_users() -> list:
    """
    環境変数から許可されたユーザーリストを取得する
    
    Returns:
        許可されたユーザーのメールアドレスリスト
    """
    allowed_users_str = os.environ.get('ALLOWED_USERS', '')
    if not allowed_users_str:
        logger.warning("ALLOWED_USERS environment variable not set")
        return []
    
    # カンマ区切りの文字列を分割してリストに変換
    allowed_users = [email.strip() for email in allowed_users_str.split(',') if email.strip()]
    logger.info(f"Loaded {len(allowed_users)} allowed users")
    return allowed_users

def validate_user_access(user_email: Optional[str]) -> Dict[str, Any]:
    """
    ユーザーのアクセス権限を検証する
    
    Args:
        user_email: 検証するユーザーのメールアドレス
    
    Returns:
        検証結果の辞書 {authorized: bool, message: str}
    """
    if not user_email:
        return {
            'authorized': False,
            'message': 'User email not provided'
        }
    
    allowed_users = get_allowed_users()
    if not allowed_users:
        # 許可ユーザーリストが空の場合は開発モードとして全て許可
        logger.warning("No allowed users configured - allowing all access (development mode)")
        return {
            'authorized': True,
            'message': 'Development mode - access granted'
        }
    
    # メールアドレスの正規化（小文字変換、空白除去）
    normalized_email = user_email.strip().lower()
    normalized_allowed_users = [email.strip().lower() for email in allowed_users]
    
    # セキュリティ強化：メールアドレスをサニタイズしてログ出力
    sanitized_email = sanitize_email_for_log(user_email)
    
    if normalized_email in normalized_allowed_users:
        logger.info(f"Access granted for user: {sanitized_email}")
        return {
            'authorized': True,
            'message': 'Access granted'
        }
    else:
        logger.warning(f"Access denied for user: {sanitized_email}")
        return {
            'authorized': False,
            'message': 'Access denied - user not authorized'
        }

@lru_cache(maxsize=1)
def get_google_public_keys() -> Dict[str, Any]:
    """
    GoogleのJWT検証用公開鍵を取得する（キャッシュ付き）
    
    Returns:
        Google公開鍵の辞書
    """
    try:
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/certs',
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch Google public keys: {e}")
        raise

def verify_google_jwt(id_token: str) -> Dict[str, Any]:
    """
    Google ID TokenのJWT検証を行う
    
    Args:
        id_token: Google ID Token
    
    Returns:
        検証済みのJWTペイロード
    
    Raises:
        InvalidTokenError: トークンが無効な場合
        ExpiredSignatureError: トークンが期限切れの場合
    """
    try:
        # JWTヘッダーからkidを取得
        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise InvalidTokenError("JWT header missing 'kid'")
        
        # Google公開鍵を取得
        public_keys = get_google_public_keys()
        
        # 対応する公開鍵を検索
        public_key_info = None
        for key_info in public_keys.get('keys', []):
            if key_info.get('kid') == kid:
                public_key_info = key_info
                break
        
        if not public_key_info:
            raise InvalidTokenError(f"Public key not found for kid: {kid}")
        
        # 公開鍵からRSA鍵を構築
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import base64
        
        # JWKからRSA公開鍵を構築
        n = base64.urlsafe_b64decode(public_key_info['n'] + '==')
        e = base64.urlsafe_b64decode(public_key_info['e'] + '==')
        
        n_int = int.from_bytes(n, 'big')
        e_int = int.from_bytes(e, 'big')
        
        public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
        pem_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Google Client IDを環境変数から取得
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
        if not google_client_id:
            raise InvalidTokenError("GOOGLE_CLIENT_ID environment variable not set")
        
        # JWT検証
        decoded_token = jwt.decode(
            id_token,
            pem_public_key,
            algorithms=['RS256'],
            audience=google_client_id,
            issuer='https://accounts.google.com'
        )
        
        logger.info(f"JWT verification successful for user: {sanitize_email_for_log(decoded_token.get('email', ''))}")
        return decoded_token
        
    except ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise
    except InvalidTokenError as e:
        logger.warning(f"JWT token validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}")
        raise InvalidTokenError(f"JWT verification failed: {e}")

def extract_user_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    API Gatewayイベントからユーザー情報を抽出する
    JWT認証: Authorization Bearerヘッダーからユーザー情報を取得
    
    Args:
        event: API Gatewayイベント
    
    Returns:
        ユーザーのメールアドレス、見つからない場合はNone
    """
    headers = event.get('headers', {})
    
    # Authorization Bearerヘッダーを検索
    auth_header = None
    for key, value in headers.items():
        if key.lower() == 'authorization':
            auth_header = value
            break
    
    if not auth_header:
        logger.warning("Authorization header not found in request")
        return None
    
    # Bearer トークンを抽出
    if not auth_header.startswith('Bearer '):
        logger.warning("Authorization header does not contain Bearer token")
        return None
    
    id_token = auth_header[7:]  # "Bearer " を除去
    
    try:
        # JWT検証を実行
        decoded_token = verify_google_jwt(id_token)
        email = decoded_token.get('email')
        
        if not email:
            logger.warning("Email not found in JWT token")
            return None
        
        return email
        
    except (InvalidTokenError, ExpiredSignatureError) as e:
        logger.warning(f"JWT authentication failed: {e}")
        return None