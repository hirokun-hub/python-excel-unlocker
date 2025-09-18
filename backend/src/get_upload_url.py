"""
署名付きURL生成Lambda関数

S3アップロード用の署名付きURLを生成し、フロントエンドに返却する。
要件4.1, 4.2に対応：セキュアなファイル転送とアクセス制御
パフォーマンス最適化：コールドスタート対策を実装
"""
import json
import logging
import os
from typing import Dict, Any

# コールドスタート対策：グローバルスコープでインポートと初期化
# 必要最小限のインポートで初期化時間を短縮
from auth_utils import extract_user_from_event, validate_user_access
from response_utils import create_success_response, create_error_response
from s3_utils import generate_presigned_url, generate_unique_key

# ログ設定（グローバルスコープで初期化、コールドスタート対策）
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(getattr(logging, log_level))

# 定数をグローバルスコープで定義（コールドスタート対策）
# 環境変数は初期化時に一度だけ読み込み
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
SUPPORTED_EXTENSIONS = frozenset(['.xlsx', '.xls'])  # frozensetで高速化
SUPPORTED_MIME_TYPES = frozenset([
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel'  # .xls
])

# 署名付きURL有効期限統一仕様（パフォーマンス最適化）
UPLOAD_URL_EXPIRES_IN = 60  # アップロード用署名付きURLの有効期限（秒）- 統一仕様

# コールドスタート対策：事前計算された値をキャッシュ
_EXTENSION_CACHE = {}  # ファイル拡張子キャッシュ

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
        
        # JWT認証チェック
        user_email = extract_user_from_event(event)
        if not user_email:
            from response_utils import create_auth_error_response
            return create_auth_error_response("authentication_failed")
        
        auth_result = validate_user_access(user_email)
        if not auth_result['authorized']:
            from response_utils import create_auth_error_response
            return create_auth_error_response("unauthorized")
        
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
        
        # ファイル形式の検証（最適化済み関数を使用）
        if not _is_supported_file_type(file_name, content_type):
            return create_error_response(
                status_code=400,
                error_code='unsupported_format',
                message='サポートされていないファイル形式です',
                suggestion='.xlsx または .xls ファイルを選択してください'
            )
        
        # ファイルサイズの検証（グローバル定数を使用）
        if file_size and file_size > MAX_FILE_SIZE:
            return create_error_response(
                status_code=400,
                error_code='file_too_large',
                message='ファイルサイズが制限を超えています',
                suggestion='20MB以下のファイルを選択してください'
            )
        
        # S3バケット名の確認（グローバル変数を使用）
        if not S3_BUCKET_NAME:
            logger.error("S3_BUCKET_NAME environment variable not set")
            return create_error_response(
                status_code=500,
                error_code='configuration_error',
                message='サーバー設定エラーが発生しました',
                suggestion='しばらく待ってから再度お試しください'
            )
        
        # ユニークなS3キーを生成
        file_key = generate_unique_key('uploads', file_name)
        
        # 署名付きURLを生成（統一仕様を使用）
        from s3_utils import generate_upload_url
        upload_url = generate_upload_url(S3_BUCKET_NAME, file_key)
        
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
    サポートされているファイル形式かどうかを判定する（パフォーマンス最適化済み）
    
    Args:
        file_name: ファイル名
        content_type: MIMEタイプ
    
    Returns:
        サポートされている場合True
    """
    # キャッシュを使用してファイル拡張子の計算を高速化
    if file_name in _EXTENSION_CACHE:
        file_extension = _EXTENSION_CACHE[file_name]
    else:
        file_extension = os.path.splitext(file_name.lower())[1]
        # キャッシュサイズ制限（メモリリーク防止）
        if len(_EXTENSION_CACHE) < 100:
            _EXTENSION_CACHE[file_name] = file_extension
    
    # frozensetによる高速な判定
    if file_extension in SUPPORTED_EXTENSIONS:
        return True
    
    # MIMEタイプによる判定（補助的、frozensetで高速化）
    if content_type and content_type in SUPPORTED_MIME_TYPES:
        return True
    
    return False