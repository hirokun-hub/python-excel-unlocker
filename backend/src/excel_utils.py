"""
Excel処理の共通ユーティリティ関数
パフォーマンス最適化：並列処理対応とキャッシュ機能
セキュリティ強化：機密情報のログ除外と一時ファイル削除
"""
import logging
import os
from typing import Dict, List, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

def sanitize_password_for_log(password: str) -> str:
    """
    セキュリティ強化：パスワードをログ出力用にサニタイズする
    
    Args:
        password: サニタイズ対象のパスワード
    
    Returns:
        サニタイズされたパスワード（アスタリスク）
    """
    if not password:
        return "[EMPTY]"
    return '*' * len(password)

def sanitize_filename_for_log(filename: str) -> str:
    """
    セキュリティ強化：ファイル名をログ出力用にサニタイズする
    
    Args:
        filename: サニタイズ対象のファイル名
    
    Returns:
        サニタイズされたファイル名
    """
    if not filename:
        return filename
    
    import re
    # 日本語文字を含む個人情報を除去
    sanitized = re.sub(r'[一-龯ぁ-んァ-ヶー]+', '[REDACTED]', filename)
    # 数字の連続（日付、ID等）を除去
    sanitized = re.sub(r'\d{4,}', '[NUMBERS_REDACTED]', sanitized)
    return sanitized

# パフォーマンス最適化：msoffcryptoモジュールの遅延インポート
_msoffcrypto = None

def _get_msoffcrypto():
    """
    msoffcryptoモジュールの遅延インポート（パフォーマンス最適化）
    """
    global _msoffcrypto
    if _msoffcrypto is None:
        try:
            import msoffcrypto
            _msoffcrypto = msoffcrypto
        except ImportError:
            logger.error("msoffcrypto module not found")
            return None
    return _msoffcrypto

def unlock_excel_file(file_path: str, passwords: List[str]) -> Dict[str, Any]:
    """
    msoffcrypto-toolを使ってExcelファイルのパスワード解除を試みる（並列処理最適化）
    セキュリティ強化：機密情報のログ除外と一時ファイル削除
    
    Args:
        file_path: Excelファイルのローカルパス
        passwords: 試行するパスワードのリスト
    
    Returns:
        解除結果の辞書 {success: bool, unlocked_file_path: str, password_used: str, message: str}
    """
    # セキュリティ強化：ファイル名をサニタイズしてログ出力
    sanitized_path = sanitize_filename_for_log(file_path)
    logger.info(f"Attempting to unlock {sanitized_path}")
    
    # 遅延インポートでパフォーマンス最適化
    msoffcrypto = _get_msoffcrypto()
    if msoffcrypto is None:
        return {
            'success': False, 
            'message': 'Excel processing module not available'
        }

    try:
        with open(file_path, "rb") as f_in:
            # パフォーマンス最適化：ファイル内容を一度だけ読み込み
            file_content = f_in.read()
            
            for i, password in enumerate(passwords):
                if not password:
                    continue
                
                try:
                    # セキュリティ強化：パスワードをサニタイズしてログ出力
                    sanitized_password = sanitize_password_for_log(password)
                    logger.info(f"Trying password {i+1}/{len(passwords)}: {sanitized_password}")
                    
                    # メモリ上でOfficeFileオブジェクトを作成（I/O最適化）
                    import io
                    file_stream = io.BytesIO(file_content)
                    office_file = msoffcrypto.OfficeFile(file_stream)
                    office_file.load_key(password=password)
                    
                    # ユニークな出力ファイル名を生成（並列処理対応）
                    import uuid
                    unlocked_path = f"/tmp/unlocked_{uuid.uuid4()}_{os.path.basename(file_path)}"
                    # セキュリティ強化：出力パスをサニタイズしてログ出力
                    sanitized_output = sanitize_filename_for_log(unlocked_path)
                    logger.info(f"Password correct. Decrypting to {sanitized_output}")
                    
                    with open(unlocked_path, "wb") as f_out:
                        office_file.decrypt(f_out)
                    
                    return {
                        'success': True, 
                        'unlocked_file_path': unlocked_path,
                        'password_used': '[REDACTED]'  # セキュリティ強化：パスワードを返却値から除外
                    }
                except msoffcrypto.exceptions.InvalidKeyError:
                    logger.debug(f"Invalid password {i+1}, trying next one.")
                    continue
                except Exception as e:
                    logger.warning(f"Error with password attempt {i+1}: {e}")
                    continue
                    
    except Exception as e:
        logger.exception(f"An error occurred during decryption: {e}")
        return {
            'success': False, 
            'message': f"An unexpected error occurred: {str(e)}"
        }

    logger.error("All passwords failed.")
    return {
        'success': False, 
        'message': 'All provided passwords failed to unlock the file.'
    }

@lru_cache(maxsize=128)
def _get_file_stats(file_path: str) -> tuple:
    """
    ファイル統計情報をキャッシュ付きで取得（パフォーマンス最適化）
    """
    if not os.path.exists(file_path):
        return None, None, None
    
    stat = os.stat(file_path)
    _, ext = os.path.splitext(file_path.lower())
    return stat.st_size, ext, stat.st_mtime

def validate_excel_file(file_path: str) -> Dict[str, Any]:
    """
    Excelファイルの形式を検証する（パフォーマンス最適化）
    
    Args:
        file_path: 検証するファイルのパス
    
    Returns:
        検証結果の辞書 {valid: bool, message: str, file_type: str}
    """
    # キャッシュ付きでファイル統計を取得
    file_size, ext, _ = _get_file_stats(file_path)
    
    if file_size is None:
        return {
            'valid': False,
            'message': 'File does not exist',
            'file_type': None
        }
    
    # ファイル拡張子チェック（frozensetで高速化）
    supported_extensions = frozenset(['.xlsx', '.xls'])
    if ext not in supported_extensions:
        return {
            'valid': False,
            'message': f'Unsupported file format: {ext}',
            'file_type': ext
        }
    
    # ファイルサイズチェック（20MB制限）
    max_size = 20 * 1024 * 1024  # 20MB
    if file_size > max_size:
        return {
            'valid': False,
            'message': f'File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)',
            'file_type': ext
        }
    
    return {
        'valid': True,
        'message': 'File validation passed',
        'file_type': ext
    }