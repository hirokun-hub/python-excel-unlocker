"""
Excel解除処理Lambda関数
パフォーマンス最適化：コールドスタート対策を実装
"""
import json
import logging
import os
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# コールドスタート対策：グローバルスコープでインポートと初期化
# 必要最小限のインポートで初期化時間を短縮
from s3_utils import download_file_from_s3, upload_file_to_s3, generate_presigned_url, generate_unique_key, cleanup_local_file, cleanup_s3_object
from excel_utils import unlock_excel_file, validate_excel_file, sanitize_filename_for_log
from auth_utils import validate_user_access, extract_user_from_event, verify_google_jwt
from response_utils import create_success_response, create_error_response

# ログ設定（グローバルスコープで初期化、コールドスタート対策）
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger()
logger.setLevel(log_level)

# 定数をグローバルスコープで定義（コールドスタート対策）
# 環境変数は初期化時に一度だけ読み込み
DOWNLOAD_URL_EXPIRATION = 300  # ダウンロード用URL有効期限（300秒）- 統一仕様
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
MAX_PROCESSING_TIME = 900  # 最大処理時間（15分）
MAX_PARALLEL_WORKERS = min(5, os.cpu_count() or 1)  # CPU数に基づく最適化

# コールドスタート対策：ThreadPoolExecutorの再利用
_thread_pool_executor = None

def get_thread_pool_executor():
    """
    ThreadPoolExecutorのシングルトンインスタンスを取得
    コールドスタート対策：プールの再利用でオーバーヘッドを削減
    """
    global _thread_pool_executor
    if _thread_pool_executor is None:
        _thread_pool_executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS)
    return _thread_pool_executor

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
    
    # S3バケット名を取得（グローバル変数を使用）
    if s3_bucket_name is None:
        s3_bucket_name = S3_BUCKET_NAME
    
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

        # ダウンロード用署名付きURLを生成（要件1.4対応、統一仕様を使用）
        from s3_utils import generate_download_url
        download_url = generate_download_url(s3_bucket_name, unlocked_s3_key)
        
        if not download_url:
            return {
                'fileName': unlocked_filename,
                'status': 'error',
                'message': 'ダウンロードURLの生成に失敗しました。再度お試しください。'
            }

        processing_time = time.time() - start_time
        # セキュリティ強化：ファイル名をサニタイズしてログ出力
        sanitized_filename = sanitize_filename_for_log(original_filename)
        logger.info(f"Successfully processed {sanitized_filename} in {processing_time:.2f}s")
        
        # ProcessResult形式で成功結果を返す
        return {
            'fileName': unlocked_filename,
            'status': 'success',
            'downloadUrl': download_url
        }

    except Exception as e:
        sanitized_filename = sanitize_filename_for_log(original_filename)
        logger.exception(f"Unexpected error processing file {sanitized_filename}: {e}")
        return {
            'fileName': unlocked_filename,
            'status': 'error',
            'message': f'予期しないエラーが発生しました: {str(e)}'
        }
    finally:
        # セキュリティ強化：一時ファイルの確実な削除（要件4.3対応）
        if local_file_path:
            cleanup_local_file(local_file_path)
                
        if unlocked_file_path:
            cleanup_local_file(unlocked_file_path)

def process_files_parallel(files_data: List[Dict[str, Any]], passwords: List[str], s3_bucket_name: str) -> List[Dict[str, Any]]:
    """
    複数ファイルを並列処理する（パフォーマンス最適化）
    
    Args:
        files_data: ファイル情報のリスト
        passwords: パスワード候補のリスト
        s3_bucket_name: S3バケット名
    
    Returns:
        ProcessResult形式の処理結果リスト
    """
    results = []
    
    # 並列処理でファイルを処理（再利用可能なExecutorを使用）
    executor = get_thread_pool_executor()
    # 各ファイルの処理タスクを作成
    future_to_file = {}
    for i, file_info in enumerate(files_data):
        s3_key = file_info.get('s3_key')
        original_name = file_info.get('original_name', f'file_{i+1}.xlsx')
        
        if not s3_key:
            # S3キーが無い場合はエラー結果を即座に追加
            base, ext = os.path.splitext(original_name)
            results.append({
                'fileName': f"{base}_unlocked{ext}",
                'status': 'error',
                'message': 'ファイルのS3キーが見つかりません。',
                'index': i  # 元の順序を保持
            })
            continue
        
        # 並列処理タスクを投入
        future = executor.submit(process_single_file, s3_key, passwords, original_name, s3_bucket_name)
        future_to_file[future] = {'index': i, 'original_name': original_name}
    
    # 完了したタスクから結果を収集
    for future in as_completed(future_to_file):
        file_info = future_to_file[future]
        try:
            result = future.result()
            result['index'] = file_info['index']  # 元の順序を保持
            results.append(result)
            logger.info(f"Completed parallel processing: {file_info['original_name']} - {result['status']}")
        except Exception as e:
            logger.exception(f"Parallel processing failed for {file_info['original_name']}: {e}")
            base, ext = os.path.splitext(file_info['original_name'])
            results.append({
                'fileName': f"{base}_unlocked{ext}",
                'status': 'error',
                'message': f'並列処理中にエラーが発生しました: {str(e)}',
                'index': file_info['index']
            })
    
    # 元の順序でソート
    results.sort(key=lambda x: x.get('index', 0))
    
    # indexフィールドを削除（フロントエンドには不要）
    for result in results:
        result.pop('index', None)
    
    return results

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
        # JWT認証チェック（要件3.1, 3.2対応）
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
        
        # 並列処理でファイルを処理（パフォーマンス最適化）
        results = process_files_parallel(files_data, passwords, s3_bucket_name)
        
        # 処理結果サマリーをログ出力（要件6.4対応）
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = len(results) - success_count
        logger.info(f"Parallel processing complete: {success_count} successful, {error_count} failed out of {len(results)} files")
        
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