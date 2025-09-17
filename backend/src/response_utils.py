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
    
    Args:
        status_code: HTTPステータスコード
        body: レスポンスボディ
        additional_headers: 追加のHTTPヘッダー
    
    Returns:
        API Gateway形式のレスポンス
    """
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # 開発用に許可
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-User-Email',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
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
    
    logger.error(f"Error response: {error_code} - {message}")
    return create_response(status_code, error_body)

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