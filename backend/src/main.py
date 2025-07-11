import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

# ログ設定
# ログレベルは環境変数や設定ファイルから取得できるようにすると、環境ごとに変更できて便利
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger()
logger.setLevel(log_level)

# S3クライアントの初期化
s3_client = boto3.client('s3')


def download_file_from_s3(bucket, key):
    """
    S3からファイルをダウンロードし、一時ファイルとして保存する

    Args:
        bucket (str): S3バケット名
        key (str): S3オブジェクトキー

    Returns:
        str: ダウンロードされたファイルのローカルパス。失敗した場合はNone。
    """
    try:
        # Lambdaの書き込み可能な一時ディレクトリ
        local_path = f"/tmp/{os.path.basename(key)}"
        logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
        s3_client.download_file(bucket, key, local_path)
        logger.info("Download successful.")
        return local_path
    except ClientError as e:
        logger.exception(f"Failed to download file from S3: {e}")
        return None

def unlock_excel_file(file_path, passwords):
    """
    msoffcrypto-toolを使ってExcelファイルのパスワード解除を試みる

    Args:
        file_path (str): パスワード付きExcelファイルのローカルパス
        passwords (list): パスワード候補のリスト

    Returns:
        dict: 処理結果。成功時は解除済みファイルパスなどを含む。
    """
    logger.info(f"Attempting to unlock {file_path}")
    import msoffcrypto

    try:
        with open(file_path, "rb") as f_in:
            for password in passwords:
                f_in.seek(0)  # 各試行の前にファイルの先頭に戻る
                office_file = msoffcrypto.OfficeFile(f_in)
                try:
                    logger.info(f"Trying password: {'*' * len(password)}")
                    office_file.load_key(password=password)
                    
                    unlocked_path = f"/tmp/unlocked_{os.path.basename(file_path)}"
                    logger.info(f"Password correct. Decrypting to {unlocked_path}")
                    with open(unlocked_path, "wb") as f_out:
                        office_file.decrypt(f_out)
                    
                    return {
                        'success': True, 
                        'unlocked_file_path': unlocked_path,
                        'password_used': password
                    }
                except msoffcrypto.exceptions.InvalidKeyError:
                    logger.warning("Invalid password, trying next one.")
                    continue # パスワードが違う場合は次のパスワードを試す
    except Exception as e:
        logger.exception(f"An error occurred during decryption: {e}")
        return {'success': False, 'message': f"An unexpected error occurred: {str(e)}"}

    logger.error("All passwords failed.")
    return {'success': False, 'message': 'All provided passwords failed to unlock the file.'}

def upload_file_to_s3(local_path, bucket, key):
    """
    ローカルファイルをS3にアップロードする

    Args:
        local_path (str): アップロードするファイルのローカルパス
        bucket (str): アップロード先のS3バケット名
        key (str): アップロード先のS3オブジェクトキー

    Returns:
        bool: アップロードが成功したかどうか
    """
    try:
        logger.info(f"Uploading {local_path} to s3://{bucket}/{key}")
        s3_client.upload_file(local_path, bucket, key)
        logger.info("Upload successful.")
        return True
    except ClientError as e:
        logger.exception(f"Failed to upload file to S3: {e}")
        return False
    except FileNotFoundError:
        logger.exception(f"The file {local_path} was not found.")
        return False

def create_response(status_code, body):
    """API Gateway用のレスポンスを生成する"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # CORS設定（開発用に一旦許可）
        },
        'body': json.dumps(body)
    }

def lambda_handler(event, context):
    """
    AWS Lambda関数のメインハンドラ

    Args:
        event (dict): API Gatewayなどから渡されるイベントデータ
        context (object): Lambdaの実行コンテキスト

    Returns:
        dict: API Gatewayに返すレスポンス
    """
    logger.info("## START: lambda_handler")
    logger.debug(f"Received event: {json.dumps(event)}")

    try:
        # API Gatewayからのリクエストボディを取得・解析
        body = json.loads(event.get('body', '{}'))
        if not body:
            logger.warning("Request body is empty.")
            return create_response(400, {'error': 'Request body is missing.'})

        # 必要なパラメータを取得
        s3_bucket = body.get('s3_bucket')
        s3_key = body.get('s3_key')
        password_1 = body.get('password_1')
        password_2 = body.get('password_2')

        # パラメータの存在チェック
        if not all([s3_bucket, s3_key, password_1, password_2]):
            logger.error("Missing required parameters.")
            return create_response(400, {'error': 'Missing required parameters: s3_bucket, s3_key, password_1, password_2'})
        
        logger.info(f"Processing file: s3://{s3_bucket}/{s3_key}")

        # --- ここから先の処理は今後のステップで実装 ---

        local_file_path = None
        unlocked_file_path = None
        try:
            # 1. S3からファイルをダウンロードする
            local_file_path = download_file_from_s3(s3_bucket, s3_key)
            if not local_file_path:
                return create_response(500, {'error': 'Failed to download file from S3.'})

            # 2. パスワード解除を試みる
            passwords = [password_1, password_2]
            unlock_result = unlock_excel_file(local_file_path, passwords)

            # 3. 結果に応じた処理
            if unlock_result['success']:
                unlocked_file_path = unlock_result['unlocked_file_path']
                unlocked_s3_key = f"unlocked/{os.path.basename(s3_key)}"
                
                # 3a. 解除済みファイルをS3にアップロード
                if upload_file_to_s3(unlocked_file_path, s3_bucket, unlocked_s3_key):
                    response_body = {
                        'message': 'File unlocked and uploaded successfully!',
                        'unlocked_file': {
                            's3_bucket': s3_bucket,
                            's3_key': unlocked_s3_key
                        }
                    }
                    response = create_response(200, response_body)
                else:
                    response = create_response(500, {'error': 'Failed to upload unlocked file to S3.'})
            else:
                # 3b. 解除失敗レスポンス
                response = create_response(400, {'error': unlock_result['message']})

        finally:
            # 4. 一時ファイルをクリーンアップ
            if local_file_path and os.path.exists(local_file_path):
                os.remove(local_file_path)
                logger.info(f"Cleaned up temporary file: {local_file_path}")
            if unlocked_file_path and os.path.exists(unlocked_file_path):
                os.remove(unlocked_file_path)
                logger.info(f"Cleaned up temporary file: {unlocked_file_path}")

    except json.JSONDecodeError:
        logger.exception("Failed to decode JSON from request body.")
        return create_response(400, {'error': 'Invalid JSON format in request body.'})
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return create_response(500, {'error': 'An internal server error occurred.'})

    logger.info("## END: lambda_handler")
    return response
