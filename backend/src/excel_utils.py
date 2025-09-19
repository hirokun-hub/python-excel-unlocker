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

def validate_excel_file(file_path: str, declared_mime_type: str = None) -> Dict[str, Any]:
    """
    Excelファイルの形式を検証する（セキュリティ強化版）
    基本的なファイル安全性チェックを統合
    
    Args:
        file_path: 検証するファイルのパス
        declared_mime_type: クライアントが宣言したMIMEタイプ
    
    Returns:
        検証結果の辞書 {valid: bool, message: str, file_type: str, is_encrypted: bool, security_details: dict}
    """
    # 新しいセキュリティチェック機能を使用
    from file_security import comprehensive_security_check
    
    # 包括的なセキュリティチェックを実行
    security_result = comprehensive_security_check(file_path, declared_mime_type)
    
    # セキュリティチェックが失敗した場合は即座に返却
    if not security_result['safe']:
        # 最初の失敗理由を使用（最も重要な問題）
        primary_failure = security_result['failed_checks'][0] if security_result['failed_checks'] else {}
        
        return {
            'valid': False,
            'message': primary_failure.get('reason', security_result['summary']),
            'file_type': _get_file_extension(file_path),
            'is_encrypted': False,
            'security_details': security_result
        }
    
    # セキュリティチェック通過後、暗号化状態をチェック
    is_encrypted = False
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
                'file_type': _get_file_extension(file_path),
                'is_encrypted': False,
                'security_details': security_result
            }
        except Exception as e:
            logger.warning(f"Could not check encryption status: {e}")
            # 暗号化チェックに失敗しても、ファイル自体は有効とみなす
            is_encrypted = None
    
    return {
        'valid': True,
        'message': 'ファイル検証に合格しました（セキュリティチェック含む）',
        'file_type': _get_file_extension(file_path),
        'is_encrypted': is_encrypted,
        'security_details': security_result
    }

def _get_file_extension(file_path: str) -> str:
    """
    ファイル拡張子を取得するヘルパー関数
    
    Args:
        file_path: ファイルパス
    
    Returns:
        str: ファイル拡張子（小文字）
    """
    import os
    return os.path.splitext(file_path.lower())[1]