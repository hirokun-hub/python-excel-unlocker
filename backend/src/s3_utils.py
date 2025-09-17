"""
S3操作の共通ユーティリティ関数
"""
import logging
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

logger = logging.getLogger(__name__)

# S3クライアントの初期化
AWS_REGION = os.environ.get('AWS_REGION')
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
)

def generate_presigned_url(bucket: str, key: str, client_method: str, expires_in: int) -> str:
    """
    S3の署名付きURLを生成する
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
        client_method: S3クライアントメソッド ('put_object' or 'get_object')
        expires_in: URL有効期限（秒）
    
    Returns:
        署名付きURL文字列、失敗時はNone
    """
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

def download_file_from_s3(bucket: str, key: str) -> str:
    """
    S3からファイルをダウンロードし、一時ファイルとして保存する
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
    
    Returns:
        ローカルファイルパス、失敗時はNone
    """
    try:
        local_path = f"/tmp/{uuid.uuid4()}-{os.path.basename(key)}"
        logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
        s3_client.download_file(bucket, key, local_path)
        logger.info("Download successful.")
        return local_path
    except ClientError as e:
        logger.exception(f"Failed to download file from S3: {e}")
        return None

def upload_file_to_s3(local_path: str, bucket: str, key: str) -> bool:
    """
    ローカルファイルをS3にアップロードする
    
    Args:
        local_path: ローカルファイルパス
        bucket: S3バケット名
        key: S3オブジェクトキー
    
    Returns:
        成功時True、失敗時False
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

def generate_unique_key(prefix: str, filename: str) -> str:
    """
    ユニークなS3キーを生成する
    
    Args:
        prefix: キーのプレフィックス
        filename: 元のファイル名
    
    Returns:
        ユニークなS3キー
    """
    base, ext = os.path.splitext(filename)
    return f"{prefix}/{uuid.uuid4()}-{base}{ext}"