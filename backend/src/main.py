import json
import logging
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

# ログ設定
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger()
logger.setLevel(log_level)

# S3クライアントと環境変数の初期化
AWS_REGION = os.environ.get('AWS_REGION')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
SIGNED_URL_EXPIRATION = 3600  # URLの有効期限を1時間に設定

# S3クライアントをリージョンと署名バージョンを明示して初期化
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
)

def create_response(status_code, body):
    """API Gateway用のレスポンスを生成する"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # 開発用に許可
        },
        'body': json.dumps(body, ensure_ascii=False)
    }

def generate_presigned_url(bucket, key, client_method, expires_in):
    """S3の署名付きURLを生成する"""
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in
        )
        logger.info(f"Generated presigned URL for {client_method.upper()}: {key}")
        return url
    except ClientError as e:
        logger.exception(f"Failed to generate presigned URL: {e}")
        return None

def download_file_from_s3(bucket, key):
    """S3からファイルをダウンロードし、一時ファイルとして保存する"""
    try:
        local_path = f"/tmp/{uuid.uuid4()}-{os.path.basename(key)}"
        logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
        s3_client.download_file(bucket, key, local_path)
        logger.info("Download successful.")
        return local_path
    except ClientError as e:
        logger.exception(f"Failed to download file from S3: {e}")
        return None

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

def unlock_excel_file(file_path, passwords):
    """msoffcrypto-toolを使ってExcelファイルのパスワード解除を試みる"""
    logger.info(f"Attempting to unlock {file_path}")
    import msoffcrypto

    try:
        with open(file_path, "rb") as f_in:
            for password in passwords:
                if not password: continue
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

def process_single_file(s3_key, passwords, original_filename):
    """単一のファイルをダウンロード、ロック解除、アップロード、結果返却まで行う"""
    local_file_path = None
    unlocked_file_path = None
    try:
        local_file_path = download_file_from_s3(S3_BUCKET_NAME, s3_key)
        if not local_file_path:
            return {
                'original_filename': original_filename,
                'status': 'error',
                'message': 'Failed to download file from S3.'
            }

        unlock_result = unlock_excel_file(local_file_path, passwords)

        if not unlock_result['success']:
            return {
                'original_filename': original_filename,
                'status': 'error',
                'message': unlock_result['message']
            }

        unlocked_file_path = unlock_result['unlocked_file_path']
        base, ext = os.path.splitext(original_filename)
        unlocked_s3_key = f"unlocked/{uuid.uuid4()}-{base}_unlocked{ext}"

        if not upload_file_to_s3(unlocked_file_path, S3_BUCKET_NAME, unlocked_s3_key):
            return {
                'original_filename': original_filename,
                'status': 'error',
                'message': 'Failed to upload unlocked file to S3.'
            }

        download_url = generate_presigned_url(S3_BUCKET_NAME, unlocked_s3_key, 'get_object', SIGNED_URL_EXPIRATION)
        if not download_url:
            return {
                'original_filename': original_filename,
                'status': 'error',
                'message': 'Failed to generate download URL for unlocked file.'
            }

        return {
            'original_filename': original_filename,
            'status': 'success',
            'download_url': download_url,
            'password_used': unlock_result.get('password_used')
        }

    finally:
        if local_file_path and os.path.exists(local_file_path):
            os.remove(local_file_path)
        if unlocked_file_path and os.path.exists(unlocked_file_path):
            os.remove(unlocked_file_path)

def lambda_handler(event, context):
    """AWS Lambda関数のメインハンドラ。API Gatewayからのリクエストを処理する。"""
    logger.info("## START: lambda_handler")
    logger.debug(f"Received event: {json.dumps(event)}")

    if not S3_BUCKET_NAME:
        logger.critical("S3_BUCKET_NAME environment variable is not set.")
        return create_response(500, {'error': 'Server configuration error.'})

    try:
        body = json.loads(event.get('body', '{}'))
        files_data = body.get('files', [])
        if not files_data:
            return create_response(400, {'error': 'Request body must contain a "files" list.'})

        results = []
        for file_info in files_data:
            s3_key = file_info.get('s3_key')
            passwords = file_info.get('passwords', [])
            original_filename = file_info.get('original_filename', 'unknown')

            if not s3_key:
                results.append({
                    'original_filename': original_filename,
                    'status': 'error',
                    'message': 's3_key is missing for a file.'
                })
                continue
            
            result = process_single_file(s3_key, passwords, original_filename)
            results.append(result)
        
        return create_response(200, {'results': results})

    except json.JSONDecodeError:
        logger.exception("Failed to decode JSON from request body.")
        return create_response(400, {'error': 'Invalid JSON format in request body.'})
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return create_response(500, {'error': f'An internal server error occurred: {str(e)}'})

    logger.info("## END: lambda_handler")
    return response
