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
from auth_utils import (
    extract_user_from_event, validate_user_access, verify_google_jwt,
    validate_bot_protection, check_request_rate_limit
)
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
        
        # レート制限チェック（Bot対策）
        rate_limit_result = check_request_rate_limit(event)
        if not rate_limit_result['allowed']:
            return create_error_response(
                status_code=429,
                error_code='rate_limit_exceeded',
                message='リクエスト頻度が高すぎます',
                suggestion='しばらく待ってから再度お試しください'
            )
        
        # Bot保護チェック
        bot_protection_result = validate_bot_protection(event)
        if not bot_protection_result['success']:
            return create_error_response(
                status_code=403,
                error_code='bot_protection_failed',
                message=bot_protection_result['message'],
                suggestion='ブラウザから正常にアクセスしてください'
            )
        
        # JWT認証チェック
        user_email = extract_user_from_event(event)
        if not user_email:
            return create_error_response(
                status_code=401,
                error_code='authentication_failed',
                message='認証に失敗しました',
                suggestion='ログインしてから再度お試しください'
            )
        
        auth_result = validate_user_access(user_email)
        if not auth_result['authorized']:
            return create_error_response(
                status_code=403,
                error_code='access_denied',
                message='このサービスへのアクセス権限がありません',
                suggestion='管理者にお問い合わせください'
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
        
        # ファイル形式の検証（セキュリティ強化版）
        security_check = _perform_upload_security_check(file_name, content_type, file_size)
        if not security_check['safe']:
            return create_error_response(
                status_code=400,
                error_code=security_check.get('error_code', 'security_check_failed'),
                message=security_check['message'],
                suggestion=security_check.get('suggestion', 'セキュリティ要件を満たすファイルを選択してください')
            )
        
        # ファイルサイズの検証（グローバル定数を使用）
        if file_size and file_size > MAX_FILE_SIZE:
            return create_error_response(
                status_code=400,
                error_code='file_too_large',
                message='ファイルサイズが制限を超えています',
                suggestion='20MB以下のファイルを選択してください'
            )
        
        # S3バケット名の確認（テスト対応のため関数内で取得）
        bucket_name = os.environ.get('S3_BUCKET_NAME') or S3_BUCKET_NAME
        if not bucket_name:
            logger.error("S3_BUCKET_NAME environment variable not set")
            return create_error_response(
                status_code=500,
                error_code='configuration_error',
                message='サーバー設定エラーが発生しました',
                suggestion='しばらく待ってから再度お試しください'
            )
        
        # ユニークなS3キーを生成
        file_key = generate_unique_key('uploads', file_name)
        
        # 署名付きURLを生成（条件拘束付き）
        from s3_utils import generate_constrained_upload_url
        upload_data = generate_constrained_upload_url(
            bucket=bucket_name, 
            key=file_key,
            content_type=content_type or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            max_size=file_size or MAX_FILE_SIZE
        )
        
        if not upload_data:
            return create_error_response(
                status_code=500,
                error_code='url_generation_failed',
                message='署名付きURLの生成に失敗しました',
                suggestion='しばらく待ってから再度お試しください'
            )
        
        # 成功レスポンスを返却（POSTデータ形式）
        response_data = {
            'uploadUrl': upload_data['url'],
            'uploadFields': upload_data['fields'],
            'fileKey': file_key,
            'expiresIn': UPLOAD_URL_EXPIRES_IN,
            'method': 'POST'  # フロントエンドにPOSTメソッドを指示
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

def _perform_upload_security_check(file_name: str, content_type: str = None, file_size: int = None) -> Dict[str, Any]:
    """
    アップロード時のセキュリティチェック（事前検証）
    
    Args:
        file_name: ファイル名
        content_type: MIMEタイプ
        file_size: ファイルサイズ
    
    Returns:
        Dict[str, Any]: セキュリティチェック結果
    """
    from file_security import (
        check_file_extension, check_file_size, check_mime_type,
        DANGEROUS_EXTENSIONS, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES
    )
    
    # ファイル拡張子の事前チェック
    file_ext = os.path.splitext(file_name.lower())[1]
    
    # 危険な拡張子のチェック（最優先）
    if file_ext in DANGEROUS_EXTENSIONS:
        if file_ext == '.xlsm':
            return {
                'safe': False,
                'error_code': 'macro_file_rejected',
                'message': 'マクロ付きExcelファイル（.xlsm）は処理できません',
                'suggestion': '.xlsx または .xls ファイルを選択してください'
            }
        else:
            return {
                'safe': False,
                'error_code': 'dangerous_file_type',
                'message': f'危険なファイル形式（{file_ext}）が検出されました',
                'suggestion': '.xlsx または .xls ファイルのみアップロード可能です'
            }
    
    # 許可された拡張子のチェック
    if file_ext not in ALLOWED_EXTENSIONS:
        return {
            'safe': False,
            'error_code': 'unsupported_format',
            'message': f'サポートされていないファイル形式です（{file_ext}）',
            'suggestion': '.xlsx または .xls ファイルを選択してください'
        }
    
    # ファイルサイズの事前チェック
    if file_size:
        if file_size > MAX_FILE_SIZE:
            return {
                'safe': False,
                'error_code': 'file_too_large',
                'message': f'ファイルサイズ（{file_size:,} bytes）が上限（{MAX_FILE_SIZE:,} bytes）を超えています',
                'suggestion': '20MB以下のファイルを選択してください'
            }
        
        if file_size < 100:  # 最小サイズチェック
            return {
                'safe': False,
                'error_code': 'file_too_small',
                'message': 'ファイルサイズが小さすぎます',
                'suggestion': '有効なExcelファイルを選択してください'
            }
    
    # MIMEタイプの事前チェック
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        return {
            'safe': False,
            'error_code': 'invalid_mime_type',
            'message': f'許可されていないMIMEタイプです: {content_type}',
            'suggestion': 'Excelファイル（.xlsx/.xls）を選択してください'
        }
    
    return {
        'safe': True,
        'message': 'アップロード前セキュリティチェック通過'
    }

def _is_supported_file_type(file_name: str, content_type: str = None) -> bool:
    """
    サポートされているファイル形式かどうかを判定する（後方互換性のため保持）
    
    Args:
        file_name: ファイル名
        content_type: MIMEタイプ
    
    Returns:
        サポートされている場合True
    """
    security_check = _perform_upload_security_check(file_name, content_type)
    return security_check['safe']