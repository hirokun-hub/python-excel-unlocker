import json
import logging
import os
import uuid
import boto3
from botocore.exceptions import ClientError

# ログ設定
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger()
logger.setLevel(log_level)

# S3クライアントと環境変数の初期化
s3_client = boto3.client('s3')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
SIGNED_URL_EXPIRATION = 300  # URLの有効期限（秒）

def generate_presigned_url(bucket, key, http_method):
    """S3の署名付きURLを生成する"""
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=f'{http_method}_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=SIGNED_URL_EXPIRATION
        )
        logger.info(f"Generated presigned URL for {http_method.upper()}: {key}")
        return url
    except ClientError as e:
        logger.exception(f"Failed to generate presigned URL: {e}")
        return None

def download_file_from_s3(bucket, key):
    """S3からファイルをダウンロードし、一時ファイルとして保存する"""
    try:
        local_path = f"/tmp/{os.path.basename(key)}"
        logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
        s3_client.download_file(bucket, key, local_path)
        logger.info("Download successful.")
        return local_path
    except ClientError as e:
        logger.exception(f"Failed to download file from S3: {e}")
        return None

def unlock_excel_file(file_path, passwords):
    """msoffcrypto-toolを使ってExcelファイルのパスワード解除を試みる"""
    logger.info(f"Attempting to unlock {file_path}")
    # msoffcrypto-toolはLambdaのレイヤーに含めるか、デプロイパッケージに含める必要がある
    import msoffcrypto

    try:
        with open(file_path, "rb") as f_in:
            for password in passwords:
                if not password: continue # 空のパスワードはスキップ
                f_in.seek(0)
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
                    continue
    except Exception as e:
        logger.exception(f"An error occurred during decryption: {e}")
        return {'success': False, 'message': f"An unexpected error occurred: {str(e)}"}

    logger.error("All passwords failed.")
    return {'success': False, 'message': 'All provided passwords failed to unlock the file.'}

def upload_file_to_s3(local_path, bucket, key):
    """ローカルファイルをS3にアップロードする"""
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
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def handle_generate_upload_url(body):
    """アップロード用URLの発行リクエストを処理する"""
    file_name = body.get('file_name')
    if not file_name:
        return create_response(400, {'error': 'Missing required parameter: file_name'})

    # ユニークなS3キーを生成
    upload_key = f"uploads/{uuid.uuid4()}/{file_name}"
    
    upload_url = generate_presigned_url(S3_BUCKET_NAME, upload_key, 'put')
    if upload_url:
        return create_response(200, {'upload_url': upload_url, 's3_key': upload_key})
    else:
        return create_response(500, {'error': 'Failed to generate upload URL.'})

def handle_process_file(body):
    """ファイル処理リクエストを処理する"""
    s3_key = body.get('s3_key')
    password_1 = body.get('password_1')
    password_2 = body.get('password_2')

    if not all([s3_key, password_1, password_2]):
        return create_response(400, {'error': 'Missing required parameters: s3_key, password_1, password_2'})

    local_file_path = None
    unlocked_file_path = None
    try:
        local_file_path = download_file_from_s3(S3_BUCKET_NAME, s3_key)
        if not local_file_path:
            return create_response(500, {'error': 'Failed to download file from S3.'})

        passwords = [password_1, password_2]
        unlock_result = unlock_excel_file(local_file_path, passwords)

        if unlock_result['success']:
            unlocked_file_path = unlock_result['unlocked_file_path']
            unlocked_s3_key = f"unlocked/{os.path.basename(s3_key)}"
            
            if upload_file_to_s3(unlocked_file_path, S3_BUCKET_NAME, unlocked_s3_key):
                download_url = generate_presigned_url(S3_BUCKET_NAME, unlocked_s3_key, 'get')
                if download_url:
                    response_body = {
                        'message': 'File unlocked successfully!',
                        'download_url': download_url
                    }
                    response = create_response(200, response_body)
                else:
                    response = create_response(500, {'error': 'Failed to generate download URL.'})
            else:
                response = create_response(500, {'error': 'Failed to upload unlocked file to S3.'})
        else:
            response = create_response(400, {'error': unlock_result['message']})

    finally:
        if local_file_path and os.path.exists(local_file_path):
            os.remove(local_file_path)
        if unlocked_file_path and os.path.exists(unlocked_file_path):
            os.remove(unlocked_file_path)
    
    return response

def lambda_handler(event, context):
    """AWS Lambda関数のメインハンドラ"""
    logger.info("## START: lambda_handler")
    logger.debug(f"Received event: {json.dumps(event)}")

    if not S3_BUCKET_NAME:
        logger.critical("S3_BUCKET_NAME environment variable is not set.")
        return create_response(500, {'error': 'Server configuration error.'})

    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')

        if action == 'generate-upload-url':
            response = handle_generate_upload_url(body)
        elif action == 'process-file':
            response = handle_process_file(body)
        else:
            logger.warning(f"Invalid or missing action: {action}")
            response = create_response(400, {'error': 'Invalid or missing action parameter.'})

    except json.JSONDecodeError:
        logger.exception("Failed to decode JSON from request body.")
        return create_response(400, {'error': 'Invalid JSON format in request body.'})
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return create_response(500, {'error': 'An internal server error occurred.'})

    logger.info("## END: lambda_handler")
    return response
