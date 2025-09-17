"""
署名付きURL生成Lambda関数

S3アップロード用の署名付きURLを生成し、フロントエンドに返却する。
要件4.1, 4.2に対応：セキュアなファイル転送とアクセス制御
"""
import json
import logging
import os
from typing import Dict, Any

from auth_utils import extract_user_from_event, validate_user_access
from response_utils import create_success_response, create_error_response
from s3_utils import generate_presigned_url, generate_unique_key

# ログ設定
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(getattr(logging, log_level))

# 定数
UPLOAD_URL_EXPIRES_IN = 60  # アップロード用署名付きURLの有効期限（秒）

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    署名付きURL生成のメインハンドラー
    
    Args:
        event: API Gatewayイベント
        context: Lambda実行コンテキスト
    
    Returns:
        API Gateway形式のレスポンス
    """
    try:
        logger.info("Starting presigned URL generation")
        
        # 認証チェック
        user_email = extract_user_from_event(event)
        auth_result = validate_user_access(user_email)
        
        if not auth_result['authorized']:
            return create_error_response(
                status_code=403,
                error_code='access_denied',
                message='アクセスが拒否されました',
                suggestion='管理者にアカウントの登録を依頼してください'
            )
        
        # リクエストボディの解析
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return create_error_response(
                status_code=400,
                error_code='invalid_json',
                message='リクエストボディのJSON形式が正しくありません',
                suggestion='正しいJSON形式でリクエストを送信してください'
            )
        
        # 必須パラメータの検証
        file_name = body.get('fileName')
        file_size = body.get('fileSize')
        content_type = body.get('contentType')
        
        if not file_name:
            return create_error_response(
                status_code=400,
                error_code='missing_filename',
                message='ファイル名が指定されていません',
                suggestion='fileNameパラメータを指定してください'
            )
        
        # ファイル形式の検証
        if not _is_supported_file_type(file_name, content_type):
            return create_error_response(
                status_code=400,
                error_code='unsupported_format',
                message='サポートされていないファイル形式です',
                suggestion='.xlsx または .xls ファイルを選択してください'
            )
        
        # ファイルサイズの検証（20MB制限）
        max_file_size = 20 * 1024 * 1024  # 20MB
        if file_size and file_size > max_file_size:
            return create_error_response(
                status_code=400,
                error_code='file_too_large',
                message='ファイルサイズが制限を超えています',
                suggestion='20MB以下のファイルを選択してください'
            )
        
        # S3バケット名の確認
        s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not s3_bucket_name:
            logger.error("S3_BUCKET_NAME environment variable not set")
            return create_error_response(
                status_code=500,
                error_code='configuration_error',
                message='サーバー設定エラーが発生しました',
                suggestion='しばらく待ってから再度お試しください'
            )
        
        # ユニークなS3キーを生成
        file_key = generate_unique_key('uploads', file_name)
        
        # 署名付きURLを生成
        upload_url = generate_presigned_url(
            bucket=s3_bucket_name,
            key=file_key,
            client_method='put_object',
            expires_in=UPLOAD_URL_EXPIRES_IN
        )
        
        if not upload_url:
            return create_error_response(
                status_code=500,
                error_code='url_generation_failed',
                message='署名付きURLの生成に失敗しました',
                suggestion='しばらく待ってから再度お試しください'
            )
        
        # 成功レスポンスを返却
        response_data = {
            'uploadUrl': upload_url,
            'fileKey': file_key,
            'expiresIn': UPLOAD_URL_EXPIRES_IN
        }
        
        logger.info(f"Successfully generated presigned URL for file: {file_name}")
        return create_success_response(response_data)
        
    except Exception as e:
        logger.exception(f"Unexpected error in presigned URL generation: {e}")
        return create_error_response(
            status_code=500,
            error_code='internal_error',
            message='予期しないエラーが発生しました',
            suggestion='しばらく待ってから再度お試しください'
        )

def _is_supported_file_type(file_name: str, content_type: str = None) -> bool:
    """
    サポートされているファイル形式かどうかを判定する
    
    Args:
        file_name: ファイル名
        content_type: MIMEタイプ
    
    Returns:
        サポートされている場合True
    """
    # ファイル拡張子による判定
    supported_extensions = ['.xlsx', '.xls']
    file_extension = os.path.splitext(file_name.lower())[1]
    
    if file_extension in supported_extensions:
        return True
    
    # MIMEタイプによる判定（補助的）
    if content_type:
        supported_mime_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel'  # .xls
        ]
        if content_type in supported_mime_types:
            return True
    
    return False