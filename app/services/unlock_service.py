"""
Excel パスワード解除サービスモジュール

msoffcrypto-tool を使用して Excel ファイルのパスワードを解除します。

Requirements: 1.1, 1.2, 1.3, 1.6, 1.7
"""

import io
import os
import tempfile
from typing import Any, Dict, Optional

import msoffcrypto

from app.services.storage_service import StorageService


class ErrorMessages:
    """エラーメッセージ定数"""
    PASSWORD_INCORRECT = "パスワードが正しくありません"
    PASSWORD_NOT_SET = "パスワードが設定されていません"
    FILE_NOT_FOUND = "ファイルが見つかりません"
    UNSUPPORTED_FORMAT = "サポートされていないファイル形式です"
    FILE_TOO_LARGE = "ファイルサイズが大きすぎます"
    SERVER_BUSY = "サーバーが混雑しています。しばらく待ってから再試行してください。"


class UnlockService:
    """
    Excel パスワード解除サービス
    
    msoffcrypto-tool を使用してパスワード保護された Excel ファイルを解除します。
    第1パスワード → 第2パスワードの順で試行し、最初に成功したパスワードで解除します。
    
    Requirements: 1.1, 1.2, 1.3, 1.6, 1.7
    """
    
    def __init__(self, storage: StorageService):
        """
        UnlockService を初期化
        
        Args:
            storage: ファイル保存に使用する StorageService インスタンス
        """
        self.storage = storage
    
    def unlock(
        self, 
        file_id: str, 
        password1: str, 
        password2: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Excel ファイルのパスワード解除を試行
        
        Args:
            file_id: StorageService.save で返された file_id
            password1: 第1パスワード（必須）
            password2: 第2パスワード（任意、空欄可）
        
        Returns:
            {
                "success": bool,
                "unlocked_file_id": Optional[str],
                "message": Optional[str],
                "original_filename": str,
                "unlocked_filename": Optional[str]
            }
        """
        # ファイルパスを取得
        file_path = self.storage.get_path(file_id)
        if not file_path:
            return self._error_response(
                ErrorMessages.FILE_NOT_FOUND,
                original_filename=""
            )
        
        # 元のファイル名を取得
        original_filename = self.storage.get_filename(file_id) or ""
        
        # パスワードリストを構築（第1 → 第2 の順で試行）
        passwords_to_try = [password1]
        if password2:  # 空欄でなければ追加
            passwords_to_try.append(password2)
        
        # msoffcrypto を使用した解除処理
        try:
            return self._try_unlock(
                file_path=file_path,
                passwords=passwords_to_try,
                original_filename=original_filename
            )
        except Exception as e:
            # 予期せぬエラー
            return self._error_response(
                str(e),
                original_filename=original_filename
            )

    def _try_unlock(
        self,
        file_path: str,
        passwords: list[str],
        original_filename: str
    ) -> Dict[str, Any]:
        """
        パスワードリストを順次試行して解除を試みる
        
        Args:
            file_path: 暗号化ファイルのパス
            passwords: 試行するパスワードのリスト
            original_filename: 元のファイル名
        
        Returns:
            解除結果の辞書
        """
        # ファイルを開いて暗号化状態をチェック
        with open(file_path, "rb") as f:
            try:
                office_file = msoffcrypto.OfficeFile(f)
            except Exception:
                # msoffcrypto が処理できないファイル形式
                return self._error_response(
                    ErrorMessages.UNSUPPORTED_FORMAT,
                    original_filename=original_filename
                )
            
            # 暗号化されているかチェック
            if not office_file.is_encrypted():
                return self._error_response(
                    ErrorMessages.PASSWORD_NOT_SET,
                    original_filename=original_filename
                )
            
            # パスワードを順次試行
            for password in passwords:
                result = self._attempt_decrypt(
                    office_file=office_file,
                    password=password,
                    original_filename=original_filename,
                    source_file=f
                )
                if result["success"]:
                    return result
                
                # ファイルポインタをリセットして次のパスワードを試行
                f.seek(0)
                office_file = msoffcrypto.OfficeFile(f)
        
        # 全パスワードで失敗
        return self._error_response(
            ErrorMessages.PASSWORD_INCORRECT,
            original_filename=original_filename
        )
    
    def _attempt_decrypt(
        self,
        office_file: msoffcrypto.OfficeFile,
        password: str,
        original_filename: str,
        source_file
    ) -> Dict[str, Any]:
        """
        単一のパスワードで解除を試みる
        
        Args:
            office_file: msoffcrypto.OfficeFile インスタンス
            password: 試行するパスワード
            original_filename: 元のファイル名
            source_file: 元ファイルのファイルオブジェクト
        
        Returns:
            解除結果の辞書
        """
        try:
            # パスワードを設定
            office_file.load_key(password=password)
            
            # 解除済みファイルを一時バッファに書き込み
            decrypted_buffer = io.BytesIO()
            office_file.decrypt(decrypted_buffer)
            
            # バッファを先頭に戻す
            decrypted_buffer.seek(0)
            
            # 解除後のファイル名を生成
            unlocked_filename = self._generate_unlocked_filename(original_filename)
            
            # StorageService で保存
            unlocked_file_id, _ = self.storage.save(
                decrypted_buffer, 
                unlocked_filename
            )
            
            return {
                "success": True,
                "unlocked_file_id": unlocked_file_id,
                "message": None,
                "original_filename": original_filename,
                "unlocked_filename": unlocked_filename
            }
            
        except msoffcrypto.exceptions.DecryptionError:
            # パスワードが不正
            return self._error_response(
                ErrorMessages.PASSWORD_INCORRECT,
                original_filename=original_filename
            )
        except msoffcrypto.exceptions.InvalidKeyError:
            # パスワードが不正（別の例外タイプ）
            return self._error_response(
                ErrorMessages.PASSWORD_INCORRECT,
                original_filename=original_filename
            )
        except Exception:
            # その他のエラーは失敗として扱う（次のパスワードを試行）
            return self._error_response(
                ErrorMessages.PASSWORD_INCORRECT,
                original_filename=original_filename
            )
    
    def _generate_unlocked_filename(self, original: str) -> str:
        """
        解除後のファイル名を生成
        
        例: 
            sample.xlsx -> sample_解除.xlsx
            sample -> sample_解除
            sample.backup.xlsx -> sample.backup_解除.xlsx
        
        Args:
            original: 元のファイル名
        
        Returns:
            解除後のファイル名
        
        Requirements: 1.7
        """
        if not original:
            return "_解除"
        
        # 最後のドットで分割（拡張子を取得）
        last_dot_index = original.rfind(".")
        
        if last_dot_index == -1 or last_dot_index == 0:
            # 拡張子なし、またはドットで始まる隠しファイル
            return f"{original}_解除"
        
        name = original[:last_dot_index]
        ext = original[last_dot_index:]  # ドットを含む
        return f"{name}_解除{ext}"
    
    def _error_response(
        self, 
        message: str, 
        original_filename: str
    ) -> Dict[str, Any]:
        """
        エラーレスポンスを生成
        
        Args:
            message: エラーメッセージ
            original_filename: 元のファイル名
        
        Returns:
            エラーレスポンスの辞書
        """
        return {
            "success": False,
            "unlocked_file_id": None,
            "message": message,
            "original_filename": original_filename,
            "unlocked_filename": None
        }
