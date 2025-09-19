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
    msoffcrypto-toolを使ってExcelファイルのパスワード解除を試みる
    パスワードなしファイルの処理も含む改善版
    
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
            # ファイル内容を読み込み
            file_content = f_in.read()
            
            # メモリ上でOfficeFileオブジェクトを作成
            import io
            file_stream = io.BytesIO(file_content)
            
            try:
                office_file = msoffcrypto.OfficeFile(file_stream)
            except msoffcrypto.exceptions.FileFormatError as e:
                logger.error(f"Unsupported file format: {e}")
                return {
                    'success': False,
                    'message': 'サポートされていないファイル形式です'
                }
            
            # ファイルが暗号化されているかチェック
            is_encrypted = office_file.is_encrypted()
            logger.info(f"File encryption status: {is_encrypted}")
            
            # ユニークな出力ファイル名を生成（並列処理対応）
            import uuid
            unlocked_path = f"/tmp/unlocked_{uuid.uuid4()}_{os.path.basename(file_path)}"
            sanitized_output = sanitize_filename_for_log(unlocked_path)
            
            # パスワードなしファイルの処理
            if not is_encrypted:
                logger.info("File is not encrypted, copying as-is")
                # 暗号化されていない場合は、そのままコピー
                with open(unlocked_path, "wb") as f_out:
                    f_out.write(file_content)
                
                return {
                    'success': True,
                    'unlocked_file_path': unlocked_path,
                    'password_used': 'no_password_required',
                    'message': 'ファイルは暗号化されていませんでした'
                }
            
            # 暗号化されている場合のパスワード試行
            if not passwords:
                return {
                    'success': False,
                    'message': 'ファイルが暗号化されていますが、パスワードが提供されていません'
                }
            
            for i, password in enumerate(passwords):
                if password is None:
                    continue
                
                try:
                    # セキュリティ強化：パスワードをサニタイズしてログ出力
                    sanitized_password = sanitize_password_for_log(password)
                    logger.info(f"Trying password {i+1}/{len(passwords)}: {sanitized_password}")
                    
                    # 新しいストリームを作成（前の試行の影響を避けるため）
                    file_stream = io.BytesIO(file_content)
                    office_file = msoffcrypto.OfficeFile(file_stream)
                    
                    # パスワードを設定
                    office_file.load_key(password=password)
                    
                    logger.info(f"Password correct. Decrypting to {sanitized_output}")
                    
                    # 復号化実行
                    with open(unlocked_path, "wb") as f_out:
                        office_file.decrypt(f_out)
                    
                    # 復号化されたファイルのサイズをチェック
                    if os.path.getsize(unlocked_path) == 0:
                        logger.warning("Decrypted file is empty, password may be incorrect")
                        os.remove(unlocked_path)
                        continue
                    
                    return {
                        'success': True, 
                        'unlocked_file_path': unlocked_path,
                        'password_used': '[REDACTED]',  # セキュリティ強化
                        'message': 'パスワード解除に成功しました'
                    }
                    
                except msoffcrypto.exceptions.InvalidKeyError:
                    logger.debug(f"Invalid password {i+1}, trying next one.")
                    continue
                except msoffcrypto.exceptions.DecryptionError as e:
                    logger.warning(f"Decryption error with password {i+1}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error with password attempt {i+1}: {e}")
                    continue
                    
    except Exception as e:
        logger.exception(f"An error occurred during file processing: {e}")
        return {
            'success': False, 
            'message': f"ファイル処理中にエラーが発生しました: {str(e)}"
        }

    logger.error("All passwords failed.")
    return {
        'success': False, 
        'message': '提供されたすべてのパスワードで解除できませんでした'
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
    Excelファイルの形式を検証する（強化版）
    マジックバイト検証とファイル構造チェックを含む
    
    Args:
        file_path: 検証するファイルのパス
    
    Returns:
        検証結果の辞書 {valid: bool, message: str, file_type: str, is_encrypted: bool}
    """
    # キャッシュ付きでファイル統計を取得
    file_size, ext, _ = _get_file_stats(file_path)
    
    if file_size is None:
        return {
            'valid': False,
            'message': 'ファイルが存在しません',
            'file_type': None,
            'is_encrypted': False
        }
    
    # ファイル拡張子チェック（frozensetで高速化）
    supported_extensions = frozenset(['.xlsx', '.xls'])
    if ext not in supported_extensions:
        return {
            'valid': False,
            'message': f'サポートされていないファイル形式です: {ext}',
            'file_type': ext,
            'is_encrypted': False
        }
    
    # ファイルサイズチェック（20MB制限）
    max_size = 20 * 1024 * 1024  # 20MB
    if file_size > max_size:
        return {
            'valid': False,
            'message': f'ファイルサイズ ({file_size} bytes) が上限 ({max_size} bytes) を超えています',
            'file_type': ext,
            'is_encrypted': False
        }
    
    # 最小ファイルサイズチェック
    min_size = 100  # 100バイト未満は無効
    if file_size < min_size:
        return {
            'valid': False,
            'message': f'ファイルサイズが小さすぎます ({file_size} bytes)',
            'file_type': ext,
            'is_encrypted': False
        }
    
    # マジックバイト検証（改善版）
    try:
        with open(file_path, 'rb') as f:
            magic_bytes = f.read(8)
            
        is_encrypted = False
        
        # Officeファイルの一般的なマジックバイト
        # PK: ZIP形式（非暗号化.xlsx）
        # \xd0\xcf\x11\xe0: OLE2形式（.xlsまたは暗号化されたOfficeファイル）
        valid_magic_bytes = [
            b'PK',  # ZIP形式（.xlsx）
            b'\xd0\xcf\x11\xe0'  # OLE2形式（.xlsまたは暗号化ファイル）
        ]
        
        is_valid_format = any(magic_bytes.startswith(magic) for magic in valid_magic_bytes)
        
        if not is_valid_format:
            return {
                'valid': False,
                'message': 'Excelファイルの形式が認識できません',
                'file_type': ext,
                'is_encrypted': False
            }
        
        # msoffcrypto-toolを使用して暗号化状態をチェック
        msoffcrypto = _get_msoffcrypto()
        if msoffcrypto:
            try:
                import io
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                file_stream = io.BytesIO(file_content)
                office_file = msoffcrypto.OfficeFile(file_stream)
                is_encrypted = office_file.is_encrypted()
            except msoffcrypto.exceptions.FileFormatError:
                return {
                    'valid': False,
                    'message': 'ファイル形式が認識できません',
                    'file_type': ext,
                    'is_encrypted': False
                }
            except Exception as e:
                logger.warning(f"Could not check encryption status: {e}")
                # 暗号化チェックに失敗しても、ファイル自体は有効とみなす
                is_encrypted = None
        
        return {
            'valid': True,
            'message': 'ファイル検証に合格しました',
            'file_type': ext,
            'is_encrypted': is_encrypted
        }
        
    except Exception as e:
        logger.exception(f"File validation error: {e}")
        return {
            'valid': False,
            'message': f'ファイル検証中にエラーが発生しました: {str(e)}',
            'file_type': ext,
            'is_encrypted': False
        }