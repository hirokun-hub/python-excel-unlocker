"""
Excel処理の共通ユーティリティ関数
"""
import logging
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def unlock_excel_file(file_path: str, passwords: List[str]) -> Dict[str, Any]:
    """
    msoffcrypto-toolを使ってExcelファイルのパスワード解除を試みる
    
    Args:
        file_path: Excelファイルのローカルパス
        passwords: 試行するパスワードのリスト
    
    Returns:
        解除結果の辞書 {success: bool, unlocked_file_path: str, password_used: str, message: str}
    """
    logger.info(f"Attempting to unlock {file_path}")
    
    try:
        import msoffcrypto
    except ImportError:
        logger.error("msoffcrypto module not found")
        return {
            'success': False, 
            'message': 'Excel processing module not available'
        }

    try:
        with open(file_path, "rb") as f_in:
            for password in passwords:
                if not password:
                    continue
                    
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
                    logger.warning(f"Error with password attempt: {e}")
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

def validate_excel_file(file_path: str) -> Dict[str, Any]:
    """
    Excelファイルの形式を検証する
    
    Args:
        file_path: 検証するファイルのパス
    
    Returns:
        検証結果の辞書 {valid: bool, message: str, file_type: str}
    """
    if not os.path.exists(file_path):
        return {
            'valid': False,
            'message': 'File does not exist',
            'file_type': None
        }
    
    # ファイル拡張子チェック
    _, ext = os.path.splitext(file_path.lower())
    if ext not in ['.xlsx', '.xls']:
        return {
            'valid': False,
            'message': f'Unsupported file format: {ext}',
            'file_type': ext
        }
    
    # ファイルサイズチェック（20MB制限）
    file_size = os.path.getsize(file_path)
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