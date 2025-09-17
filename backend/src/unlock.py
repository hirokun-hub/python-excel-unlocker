"""
Excel解除処理Lambda関数
"""
import json
import logging
import os
import time
from typing import Dict, Any, List

from s3_utils import download_file_from_s3, upload_file_to_s3, generate_presigned_url, generate_unique_key
from excel_utils import unlock_excel_file, validate_excel_file
from auth_utils import validate_user_access, extract_user_from_event
from response_utils import create_success_response, create_error_response

# ログ設定
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger()
logger.setLevel(log_level)

# 定数
DOWNLOAD_URL_EXPIRATION = 300  # ダウンロード用URL有効期限（300秒）

def process_single_file(s3_key: str, passwords: List[str], original_filename: str, s3_bucket_name: str = None) -> Dict[str, Any]:
    """
    単一のファイルをダウンロード、ロック解除、アップロード、結果返却まで行う
    フロントエンドが期待するProcessResult形式で結果を返す
    
    Args:
        s3_key: S3オブジェクトキー
        passwords: 試行するパスワードのリスト
        original_filename: 元のファイル名
        s3_bucket_name: S3バケット名（省略時は環境変数から取得）
    
    Returns:
        ProcessResult形式の処理結果辞書
        {fileName: str, status: 'success'|'error', message?: str, downloadUrl?: str}
    """
    local_file_path = None
    unlocked_file_path = None
    start_time = time.time()
    
    # S3バケット名を取得
    if s3_bucket_name is None:
        s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    
    # 解除済みファイル名を事前に決定（要件1.1対応）
    base, ext = os.path.splitext(original_filename)
    unlocked_filename = f"{base}_unlocked{ext}"
    
    try:
        # S3からファイルをダウンロード
        local_file_path = download_file_from_s3(s3_bucket_name, s3_key)
        if not local_file_path:
            return {
                'fileName': unlocked_filename,
                'status': 'error',
                'message': 'ファイルのダウンロードに失敗しました。再度アップロードしてお試しください。'
            }

        # ファイル形式の検証
        validation_result = validate_excel_file(local_file_path)
        if not validation_result['valid']:
            return {
                'fileName': unlocked_filename,
                'status': 'error',
                'message': f'サポートされていないファイル形式です。.xlsx または .xls ファイルを選択してください。'
            }

        # パスワード解除の実行（要件1.1, 1.2対応）
        unlock_result = unlock_excel_file(local_file_path, passwords)

        if not unlock_result['success']:
            # 要件1.3: 明確な失敗理由を表示
            if 'password' in unlock_result['message'].lower():
                message = '入力されたパスワードでは解除できませんでした。別のパスワード候補をお試しください。'
            else:
                message = 'ファイルの解除に失敗しました。ファイルが破損している可能性があります。'
            
            return {
                'fileName': unlocked_filename,
                'status': 'error',
                'message': message
            }

        unlocked_file_path = unlock_result['unlocked_file_path']
        
        # 解除済みファイルをS3にアップロード
        unlocked_s3_key = generate_unique_key('unlocked', unlocked_filename)

        if not upload_file_to_s3(unlocked_file_path, s3_bucket_name, unlocked_s3_key):
            return {
                'fileName': unlocked_filename,
                'status': 'error',
                'message': '解除済みファイルのアップロードに失敗しました。再度お試しください。'
            }

        # ダウンロード用署名付きURLを生成（要件1.4対応）
        download_url = generate_presigned_url(
            s3_bucket_name, 
            unlocked_s3_key, 
            'get_object', 
            DOWNLOAD_URL_EXPIRATION
        )
        
        if not download_url:
            return {
                'fileName': unlocked_filename,
                'status': 'error',
                'message': 'ダウンロードURLの生成に失敗しました。再度お試しください。'
            }

        processing_time = time.time() - start_time
        logger.info(f"Successfully processed {original_filename} in {processing_time:.2f}s using password: {'*' * len(unlock_result.get('password_used', ''))}")
        
        # ProcessResult形式で成功結果を返す
        return {
            'fileName': unlocked_filename,
            'status': 'success',
            'downloadUrl': download_url
        }

    except Exception as e:
        logger.exception(f"Unexpected error processing file {original_filename}: {e}")
        return {
            'fileName': unlocked_filename,
            'status': 'error',
            'message': f'予期しないエラーが発生しました: {str(e)}'
        }
    finally:
        # 一時ファイルのクリーンアップ（要件4.3対応）
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
                logger.info(f"Cleaned up local file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up local file {local_file_path}: {e}")
                
        if unlocked_file_path and os.path.exists(unlocked_file_path):
            try:
                os.remove(unlocked_file_path)
                logger.info(f"Cleaned up unlocked file: {unlocked_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up unlocked file {unlocked_file_path}: {e}")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Excel解除処理のメインハンドラ
    フロントエンドが期待する形式でリクエストを処理し、ProcessResult[]形式でレスポンスを返す
    
    Args:
        event: API Gatewayイベント
        context: Lambda実行コンテキスト
    
    Returns:
        API Gateway形式のレスポンス
    """
    logger.info("## START: unlock lambda_handler")
    logger.debug(f"Received event: {json.dumps(event, default=str)}")

    # 環境変数チェック
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    if not s3_bucket_name:
        logger.critical("S3_BUCKET_NAME environment variable is not set.")
        return create_error_response(
            500, 
            'server_configuration_error', 
            'サーバー設定エラーが発生しました。'
        )

    try:
        # 認証チェック（要件3.1, 3.2対応）
        user_email = extract_user_from_event(event)
        auth_result = validate_user_access(user_email)
        
        if not auth_result['authorized']:
            return create_error_response(
                403,
                'access_denied',
                'アクセスが拒否されました。管理者にお問い合わせください。'
            )

        # リクエストボディの解析
        body = json.loads(event.get('body', '{}'))
        
        # フロントエンドが期待する形式: { files: UnlockFile[], passwords: string[] }
        files_data = body.get('files', [])
        passwords = body.get('passwords', [])
        
        # 後方互換性: 単一ファイル処理（旧形式）
        if 'fileKey' in body:
            file_key = body.get('fileKey')
            file_passwords = body.get('passwords', [])
            original_filename = body.get('fileName', 'unknown.xlsx')
            
            if not file_key:
                return create_error_response(
                    400,
                    'missing_parameter',
                    'fileKeyが必要です。'
                )
            
            result = process_single_file(file_key, file_passwords, original_filename, s3_bucket_name)
            
            # 単一ファイルの場合も配列形式で返す（統一性のため）
            return create_success_response({'results': [result]})
        
        # 複数ファイル処理（要件6.1対応）
        if not files_data:
            return create_error_response(
                400,
                'missing_parameter',
                'ファイル情報が必要です。filesパラメータを指定してください。'
            )

        if not passwords:
            return create_error_response(
                400,
                'missing_parameter',
                '少なくとも1つのパスワードを指定してください。'
            )

        logger.info(f"Processing {len(files_data)} files with {len(passwords)} password candidates")
        
        results = []
        for i, file_info in enumerate(files_data):
            s3_key = file_info.get('s3_key')
            original_name = file_info.get('original_name', f'file_{i+1}.xlsx')

            if not s3_key:
                # 要件6.3: 一部ファイルが失敗しても他は正常処理
                base, ext = os.path.splitext(original_name)
                results.append({
                    'fileName': f"{base}_unlocked{ext}",
                    'status': 'error',
                    'message': 'ファイルのS3キーが見つかりません。'
                })
                continue
            
            # 各ファイルを個別に処理（要件6.1, 6.2対応）
            result = process_single_file(s3_key, passwords, original_name, s3_bucket_name)
            results.append(result)
            
            # 進捗ログ出力（要件6.2対応）
            logger.info(f"Processed file {i+1}/{len(files_data)}: {original_name} - {result['status']}")
        
        # 処理結果サマリーをログ出力（要件6.4対応）
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = len(results) - success_count
        logger.info(f"Processing complete: {success_count} successful, {error_count} failed out of {len(results)} files")
        
        # ProcessResult[]形式でレスポンス返却
        return create_success_response({'results': results})

    except json.JSONDecodeError:
        logger.exception("Failed to decode JSON from request body.")
        return create_error_response(
            400,
            'invalid_json',
            'リクエストのJSON形式が無効です。'
        )
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return create_error_response(
            500,
            'internal_server_error',
            f'予期しないエラーが発生しました: {str(e)}'
        )
    finally:
        logger.info("## END: unlock lambda_handler")