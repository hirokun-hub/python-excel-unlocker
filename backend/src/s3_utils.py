"""
S3操作の共通ユーティリティ関数
パフォーマンス最適化：コールドスタート対策とURL有効期限統一
セキュリティ強化：機密情報のログ除外
"""
import logging
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
import re

logger = logging.getLogger(__name__)

def sanitize_for_log(text: str) -> str:
    """
    セキュリティ強化：ログ出力用に機密情報をサニタイズする
    
    Args:
        text: サニタイズ対象のテキスト
    
    Returns:
        サニタイズされたテキスト
    """
    if not text:
        return text
    
    # 署名付きURLのクエリパラメータを除去
    sanitized = re.sub(r'\?.*', '?[REDACTED]', text)
    
    # AWSアクセスキーパターンを除去
    sanitized = re.sub(r'AKIA[0-9A-Z]{16}', '[AWS_ACCESS_KEY_REDACTED]', sanitized)
    
    # AWSシークレットキーパターンを除去
    sanitized = re.sub(r'[A-Za-z0-9/+=]{40}', '[AWS_SECRET_REDACTED]', sanitized)
    
    # ファイル名から個人情報を除去（日本語文字を含む可能性）
    sanitized = re.sub(r'[一-龯ぁ-んァ-ヶー]+', '[FILENAME_REDACTED]', sanitized)
    
    return sanitized

# 署名付きURL有効期限の統一仕様（設計書準拠、パフォーマンス最適化）
UPLOAD_URL_EXPIRES_IN = 60    # アップロード用：60秒
DOWNLOAD_URL_EXPIRES_IN = 300  # ダウンロード用：300秒

# S3クライアントの初期化（コールドスタート対策：グローバルスコープ）
# パフォーマンス最適化：接続プールとタイムアウト設定
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'},
        max_pool_connections=50,  # 並列処理対応
        retries={'max_attempts': 3, 'mode': 'adaptive'}  # リトライ設定
    )
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
        # セキュリティ強化：機密情報をログから除外
        sanitized_key = sanitize_for_log(key)
        logger.info(f"Generated presigned URL for {client_method.upper()}: {sanitized_key} (expires in {expires_in}s)")
        return url
    except ClientError as e:
        logger.exception(f"Failed to generate presigned URL: {e}")
        return None

def generate_constrained_upload_url(bucket: str, key: str, content_type: str, max_size: int) -> dict:
    """
    アップロード用署名付きURLを生成する（厳格な条件拘束付き）
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
        content_type: 必須のContent-Type（偽装防止）
        max_size: 最大ファイルサイズ（バイト）
    
    Returns:
        署名付きPOSTデータ辞書、失敗時はNone
    """
    try:
        # セキュリティ強化：許可されたContent-Typeの厳格チェック
        allowed_content_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel',  # .xls
            'application/octet-stream'  # 一部のブラウザで送信される場合
        ]
        
        if content_type not in allowed_content_types:
            logger.warning(f"Rejected content type for S3 upload: {content_type}")
            return None
        
        # 条件拘束の設定（厳格化）
        fields = {}
        conditions = []
        
        # Content-Type拘束（厳格・必須）
        fields['Content-Type'] = content_type
        conditions.append({'Content-Type': content_type})
        
        # ファイルサイズ拘束（厳格）
        min_size = 100  # 最小100バイト
        conditions.append(['content-length-range', min_size, max_size])
        
        # セキュリティ強化：追加の厳格な条件
        conditions.extend([
            {'bucket': bucket},
            {'key': key},
            # Content-Typeの厳格な一致（starts-withではなく完全一致）
            {'Content-Type': content_type},
            # キーのプレフィックス制限
            ['starts-with', '$key', 'uploads/'],
            # サーバーサイド暗号化の強制
            {'x-amz-server-side-encryption': 'AES256'}
        ])
        
        # サーバーサイド暗号化を強制
        fields['x-amz-server-side-encryption'] = 'AES256'
        
        # 署名付きPOSTを生成
        response = s3_client.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=UPLOAD_URL_EXPIRES_IN
        )
        
        # セキュリティ強化：機密情報をログから除外
        sanitized_key = sanitize_for_log(key)
        logger.info(f"Generated constrained presigned POST: {sanitized_key} (expires in {UPLOAD_URL_EXPIRES_IN}s)")
        logger.info(f"Constraints: Content-Type={content_type}, Size={min_size}-{max_size} bytes, Encryption=AES256")
        
        return response
        
    except ClientError as e:
        logger.exception(f"Failed to generate constrained presigned POST: {e}")
        return None

def generate_upload_url(bucket: str, key: str) -> str:
    """
    アップロード用署名付きURLを生成する（従来版、後方互換性のため残存）
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
    
    Returns:
        署名付きURL文字列、失敗時はNone
    """
    return generate_presigned_url(bucket, key, 'put_object', UPLOAD_URL_EXPIRES_IN)

def generate_download_url(bucket: str, key: str) -> str:
    """
    ダウンロード用署名付きURLを生成する（統一仕様）
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
    
    Returns:
        署名付きURL文字列、失敗時はNone
    """
    return generate_presigned_url(bucket, key, 'get_object', DOWNLOAD_URL_EXPIRES_IN)

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
        # セキュリティ強化：機密情報をログから除外
        sanitized_key = sanitize_for_log(key)
        sanitized_path = sanitize_for_log(local_path)
        logger.info(f"Downloading s3://{bucket}/{sanitized_key} to {sanitized_path}")
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
        # セキュリティ強化：機密情報をログから除外
        sanitized_path = sanitize_for_log(local_path)
        sanitized_key = sanitize_for_log(key)
        logger.info(f"Uploading {sanitized_path} to s3://{bucket}/{sanitized_key}")
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

def cleanup_local_file(file_path: str) -> bool:
    """
    セキュリティ強化：ローカル一時ファイルを確実に削除する
    
    Args:
        file_path: 削除対象のファイルパス
    
    Returns:
        削除成功時True、失敗時False
    """
    if not file_path or not os.path.exists(file_path):
        return True
    
    try:
        # セキュリティ強化：ファイル内容を上書きしてから削除
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            with open(file_path, 'r+b') as f:
                # ランダムデータで上書き（3回）
                for _ in range(3):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
        
        os.remove(file_path)
        sanitized_path = sanitize_for_log(file_path)
        logger.info(f"Successfully cleaned up temporary file: {sanitized_path}")
        return True
    except Exception as e:
        sanitized_path = sanitize_for_log(file_path)
        logger.error(f"Failed to cleanup temporary file {sanitized_path}: {e}")
        return False

def cleanup_s3_object(bucket: str, key: str) -> bool:
    """
    セキュリティ強化：S3オブジェクトを削除する
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
    
    Returns:
        削除成功時True、失敗時False
    """
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        sanitized_key = sanitize_for_log(key)
        logger.info(f"Successfully deleted S3 object: s3://{bucket}/{sanitized_key}")
        return True
    except ClientError as e:
        sanitized_key = sanitize_for_log(key)
        logger.error(f"Failed to delete S3 object s3://{bucket}/{sanitized_key}: {e}")
        return False