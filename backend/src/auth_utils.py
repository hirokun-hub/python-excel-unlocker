"""
認証チェックの共通ユーティリティ関数
"""
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

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
    
    if user_email in allowed_users:
        logger.info(f"Access granted for user: {user_email}")
        return {
            'authorized': True,
            'message': 'Access granted'
        }
    else:
        logger.warning(f"Access denied for user: {user_email}")
        return {
            'authorized': False,
            'message': 'Access denied - user not authorized'
        }

def extract_user_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    API Gatewayイベントからユーザー情報を抽出する
    
    Args:
        event: API Gatewayイベント
    
    Returns:
        ユーザーのメールアドレス、見つからない場合はNone
    """
    # 将来的にJWTトークンやAuthorizerから取得する予定
    # 現在は開発段階のため、ヘッダーから取得
    headers = event.get('headers', {})
    
    # 大文字小文字を考慮してヘッダーを検索
    for key, value in headers.items():
        if key.lower() == 'x-user-email':
            return value
    
    # 認証情報が見つからない場合
    logger.warning("User email not found in request headers")
    return None