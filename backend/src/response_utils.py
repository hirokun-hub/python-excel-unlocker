"""
API Gateway レスポンス生成の共通ユーティリティ関数
"""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def create_response(status_code: int, body: Dict[str, Any], additional_headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    API Gateway用のレスポンスを生成する
    セキュリティ強化：セキュリティヘッダーの追加
    
    Args:
        status_code: HTTPステータスコード
        body: レスポンスボディ
        additional_headers: 追加のHTTPヘッダー
    
    Returns:
        API Gateway形式のレスポンス
    """
    headers = {
        'Content-Type': 'application/json',
        # セキュリティ強化：CORS設定の最適化
        'Access-Control-Allow-Origin': 'https://localhost:3000,https://localhost:3001,https://*.vercel.app',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-User-Email',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Credentials': 'true',
        # セキュリティ強化：セキュリティヘッダーの追加
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://*.amazonaws.com"
    }
    
    if additional_headers:
        headers.update(additional_headers)
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, ensure_ascii=False)
    }

def create_error_response(status_code: int, error_code: str, message: str, suggestion: str = None) -> Dict[str, Any]:
    """
    エラーレスポンスを生成する
    セキュリティ強化：機密情報のログ除外
    
    Args:
        status_code: HTTPステータスコード
        error_code: エラーコード
        message: エラーメッセージ
        suggestion: 解決方法の提案
    
    Returns:
        エラーレスポンス
    """
    error_body = {
        'success': False,
        'error': error_code,
        'message': message
    }
    
    if suggestion:
        error_body['suggestion'] = suggestion
    
    # セキュリティ強化：エラーメッセージから機密情報を除外してログ出力
    sanitized_message = sanitize_error_message_for_log(message)
    logger.error(f"Error response: {error_code} - {sanitized_message}")
    return create_response(status_code, error_body)

def sanitize_error_message_for_log(message: str) -> str:
    """
    セキュリティ強化：エラーメッセージをログ出力用にサニタイズする
    
    Args:
        message: サニタイズ対象のエラーメッセージ
    
    Returns:
        サニタイズされたエラーメッセージ
    """
    if not message:
        return message
    
    import re
    # ファイルパスを除去
    sanitized = re.sub(r'/tmp/[^/\s]+', '[TEMP_FILE_REDACTED]', message)
    # S3キーを除去
    sanitized = re.sub(r's3://[^/\s]+/[^\s]+', '[S3_PATH_REDACTED]', sanitized)
    # 日本語ファイル名を除去
    sanitized = re.sub(r'[一-龯ぁ-んァ-ヶー]+', '[FILENAME_REDACTED]', sanitized)
    
    return sanitized

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    成功レスポンスを生成する
    
    Args:
        data: レスポンスデータ
    
    Returns:
        成功レスポンス
    """
    success_body = {
        'success': True,
        **data
    }
    
    return create_response(200, success_body)