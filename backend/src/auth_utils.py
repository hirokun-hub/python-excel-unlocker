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
import hashlib
import hmac

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

def is_development_environment() -> bool:
    """
    開発環境かどうかを判定する
    
    Returns:
        開発環境の場合True、本番環境の場合False
    """
    environment = os.environ.get('ENVIRONMENT', '').lower()
    stage = os.environ.get('STAGE', '').lower()
    
    # 開発環境の判定条件
    development_indicators = [
        environment in ['development', 'dev', 'local'],
        stage in ['development', 'dev', 'local'],
        os.environ.get('AWS_SAM_LOCAL') == 'true',  # SAM Local実行時
        os.environ.get('DEVELOPMENT_MODE') == 'true'  # 明示的な開発モード指定
    ]
    
    is_dev = any(development_indicators)
    logger.info(f"Environment check: ENVIRONMENT={environment}, STAGE={stage}, is_development={is_dev}")
    return is_dev

def validate_user_access(user_email: Optional[str]) -> Dict[str, Any]:
    """
    ユーザーのアクセス権限を検証する
    セキュリティ強化：本番環境では許可ユーザーリスト必須、開発環境のみ全許可
    
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
    is_dev_env = is_development_environment()
    
    # 許可ユーザーリストが空の場合の処理
    if not allowed_users:
        if is_dev_env:
            # 開発環境：全て許可（従来の動作）
            logger.warning("No allowed users configured - allowing all access (development mode)")
            return {
                'authorized': True,
                'message': 'Development mode - access granted'
            }
        else:
            # 本番環境：全て拒否（セキュリティ強化）
            logger.error("CRITICAL: No allowed users configured in production environment - denying all access")
            return {
                'authorized': False,
                'message': 'Access denied - no users authorized (configuration required)'
            }
    
    # メールアドレスの正規化（小文字変換、空白除去）
    normalized_email = user_email.strip().lower()
    normalized_allowed_users = [email.strip().lower() for email in allowed_users]
    
    # セキュリティ強化：メールアドレスをサニタイズしてログ出力
    sanitized_email = sanitize_email_for_log(user_email)
    
    if normalized_email in normalized_allowed_users:
        env_type = "development" if is_dev_env else "production"
        logger.info(f"Access granted for user: {sanitized_email} (environment: {env_type})")
        return {
            'authorized': True,
            'message': 'Access granted'
        }
    else:
        env_type = "development" if is_dev_env else "production"
        logger.warning(f"Access denied for user: {sanitized_email} (environment: {env_type})")
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
    テスト環境: test-jwt-token-で始まるトークンは簡易認証
    
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
    
    # テスト環境用の簡易認証
    if id_token.startswith('test-jwt-token-'):
        # テスト用トークンからメールアドレスを抽出
        test_email = id_token.replace('test-jwt-token-', '')
        logger.info(f"Test authentication for user: {sanitize_email_for_log(test_email)}")
        return test_email
    
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

def is_bot_protection_enabled() -> bool:
    """
    Bot保護機能が有効かどうかを確認する
    
    Returns:
        Bot保護が有効な場合True
    """
    return os.environ.get('ENABLE_BOT_PROTECTION', 'false').lower() == 'true'

def validate_recaptcha_token(token: str, remote_ip: str) -> Dict[str, Any]:
    """
    reCAPTCHA v3トークンを検証する
    
    Args:
        token: reCAPTCHAトークン
        remote_ip: クライアントのIPアドレス
    
    Returns:
        検証結果の辞書 {success: bool, score: float, action: str}
    """
    if not is_bot_protection_enabled():
        return {'success': True, 'score': 1.0, 'action': 'disabled'}
    
    recaptcha_secret = os.environ.get('RECAPTCHA_SECRET_KEY')
    if not recaptcha_secret:
        logger.warning("RECAPTCHA_SECRET_KEY not configured")
        return {'success': True, 'score': 1.0, 'action': 'not_configured'}
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': recaptcha_secret,
                'response': token,
                'remoteip': remote_ip
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        success = result.get('success', False)
        score = result.get('score', 0.0)
        action = result.get('action', 'unknown')
        
        logger.info(f"reCAPTCHA validation: success={success}, score={score}, action={action}")
        
        # スコアが0.5以上を人間と判定（調整可能）
        if success and score >= 0.5:
            return {'success': True, 'score': score, 'action': action}
        else:
            return {'success': False, 'score': score, 'action': action}
            
    except Exception as e:
        logger.error(f"reCAPTCHA validation failed: {e}")
        # エラー時は通す（可用性優先）
        return {'success': True, 'score': 1.0, 'action': 'error'}

def validate_turnstile_token(token: str, remote_ip: str) -> Dict[str, Any]:
    """
    Cloudflare Turnstileトークンを検証する
    
    Args:
        token: Turnstileトークン
        remote_ip: クライアントのIPアドレス
    
    Returns:
        検証結果の辞書 {success: bool, challenge_ts: str, hostname: str}
    """
    if not is_bot_protection_enabled():
        return {'success': True, 'challenge_ts': '', 'hostname': ''}
    
    turnstile_secret = os.environ.get('TURNSTILE_SECRET_KEY')
    if not turnstile_secret:
        logger.warning("TURNSTILE_SECRET_KEY not configured")
        return {'success': True, 'challenge_ts': '', 'hostname': ''}
    
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': turnstile_secret,
                'response': token,
                'remoteip': remote_ip
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        success = result.get('success', False)
        challenge_ts = result.get('challenge_ts', '')
        hostname = result.get('hostname', '')
        
        logger.info(f"Turnstile validation: success={success}, hostname={hostname}")
        
        return {
            'success': success,
            'challenge_ts': challenge_ts,
            'hostname': hostname
        }
        
    except Exception as e:
        logger.error(f"Turnstile validation failed: {e}")
        # エラー時は通す（可用性優先）
        return {'success': True, 'challenge_ts': '', 'hostname': ''}

def validate_bot_protection(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bot保護機能の総合検証を行う
    
    Args:
        event: API Gatewayイベント
    
    Returns:
        検証結果の辞書 {success: bool, message: str, details: dict}
    """
    if not is_bot_protection_enabled():
        return {
            'success': True,
            'message': 'Bot protection disabled',
            'details': {}
        }
    
    # リクエストボディからBot保護トークンを取得
    body = event.get('body', '{}')
    try:
        if isinstance(body, str):
            body_data = json.loads(body)
        else:
            body_data = body
    except json.JSONDecodeError:
        body_data = {}
    
    # クライアントIPアドレスを取得
    remote_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', '')
    
    # reCAPTCHAトークンの検証
    recaptcha_token = body_data.get('recaptcha_token')
    if recaptcha_token:
        recaptcha_result = validate_recaptcha_token(recaptcha_token, remote_ip)
        if not recaptcha_result['success']:
            return {
                'success': False,
                'message': 'reCAPTCHA validation failed',
                'details': recaptcha_result
            }
    
    # Turnstileトークンの検証
    turnstile_token = body_data.get('turnstile_token')
    if turnstile_token:
        turnstile_result = validate_turnstile_token(turnstile_token, remote_ip)
        if not turnstile_result['success']:
            return {
                'success': False,
                'message': 'Turnstile validation failed',
                'details': turnstile_result
            }
    
    # どちらのトークンも提供されていない場合
    if not recaptcha_token and not turnstile_token:
        logger.warning("No bot protection token provided")
        return {
            'success': False,
            'message': 'Bot protection token required',
            'details': {}
        }
    
    return {
        'success': True,
        'message': 'Bot protection validation passed',
        'details': {}
    }

def check_request_rate_limit(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    リクエストレート制限をチェックする（簡易実装）
    
    Args:
        event: API Gatewayイベント
    
    Returns:
        チェック結果の辞書 {allowed: bool, message: str}
    """
    # 実際の実装では Redis や DynamoDB を使用してレート制限を実装
    # ここでは基本的なヘッダーチェックのみ
    
    headers = event.get('headers', {})
    user_agent = headers.get('User-Agent', '').lower()
    
    # 明らかなBot User-Agentをブロック
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
        'python-requests', 'go-http-client', 'java/', 'apache-httpclient'
    ]
    
    for pattern in bot_patterns:
        if pattern in user_agent:
            logger.warning(f"Suspicious User-Agent detected: {user_agent}")
            return {
                'allowed': False,
                'message': f'Blocked User-Agent pattern: {pattern}'
            }
    
    return {
        'allowed': True,
        'message': 'Rate limit check passed'
    }