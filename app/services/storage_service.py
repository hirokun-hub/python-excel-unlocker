"""
ストレージサービスモジュール

ファイルの保存・読み込み・削除を抽象化し、
将来的な Cloud Storage 連携を容易にします。

Requirements: 1.4, 6.1, 将来拡張性（Cloud Storage 連携）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import BinaryIO, Dict, Optional, Tuple
import os
import uuid

from app.config import settings


@dataclass
class FileEntry:
    """ファイルレジストリのエントリ"""
    file_id: str
    file_path: str
    original_filename: str
    created_at: datetime = field(default_factory=datetime.now)
    downloaded: bool = False


class StorageService(ABC):
    """
    ストレージサービス抽象クラス
    
    MVP では LocalStorageService を使用し、
    将来的には GCSStorageService 等に差し替え可能な設計。
    """
    
    @abstractmethod
    def save(self, file_like: BinaryIO, filename: str) -> Tuple[str, str]:
        """
        ファイルを保存し、(file_id, file_path) を返す
        
        Args:
            file_like: SpooledTemporaryFile 等のファイルライクオブジェクト
            filename: 元のファイル名
        
        Returns:
            (file_id, file_path): 生成されたIDと保存先パス
        """
        pass
    
    @abstractmethod
    def get_path(self, file_id: str) -> Optional[str]:
        """
        file_id からファイルパスを取得（msoffcrypto 用）
        
        Args:
            file_id: ファイルID
        
        Returns:
            ファイルパス、存在しない/期限切れの場合は None
        """
        pass
    
    @abstractmethod
    def load(self, file_id: str) -> Optional[bytes]:
        """
        file_id からファイル内容を取得（ダウンロード用）
        
        Args:
            file_id: ファイルID
        
        Returns:
            ファイル内容のバイト列、存在しない/期限切れの場合は None
        """
        pass
    
    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """
        ファイルを削除
        
        Args:
            file_id: ファイルID
        
        Returns:
            削除成功時 True、失敗時 False
        """
        pass
    
    @abstractmethod
    def generate_download_url(self, file_id: str) -> str:
        """
        ダウンロード URL を生成
        
        MVP: /download/{file_id} を返すだけ（署名処理なし）
        将来 GCS: 署名付き URL を返す
        
        Args:
            file_id: ファイルID
        
        Returns:
            ダウンロードURL
        """
        pass
    
    @abstractmethod
    def get_filename(self, file_id: str) -> Optional[str]:
        """
        file_id から元のファイル名を取得
        
        Args:
            file_id: ファイルID
        
        Returns:
            ファイル名、存在しない場合は None
        """
        pass
    
    @abstractmethod
    def is_expired(self, file_id: str) -> bool:
        """
        file_id が期限切れかどうかを判定
        
        Args:
            file_id: ファイルID
        
        Returns:
            期限切れの場合 True
        """
        pass


class LocalStorageService(StorageService):
    """
    MVP 用ローカルストレージ実装
    
    ファイルを TMP_DIR に保存し、インメモリのレジストリで管理します。
    有効期限（デフォルト5分）を超えたファイルは自動削除されます。
    
    Requirements: 1.4, 6.1, ダウンロードURLの有効期限
    """
    
    # チャンクサイズ: 1MB（50MB上限で十分、設定値化は不要な複雑化を招くため固定）
    CHUNK_SIZE = 1024 * 1024
    
    def __init__(
        self, 
        base_dir: Optional[str] = None, 
        expiry_seconds: Optional[int] = None
    ):
        """
        LocalStorageService を初期化
        
        Args:
            base_dir: ファイル保存先ディレクトリ（デフォルト: settings.TMP_DIR）
            expiry_seconds: 有効期限（秒）（デフォルト: settings.DOWNLOAD_EXPIRY_SECONDS）
        """
        self.base_dir = base_dir or settings.TMP_DIR
        self.expiry_seconds = expiry_seconds or settings.DOWNLOAD_EXPIRY_SECONDS
        self._file_registry: Dict[str, FileEntry] = {}
        
        # ベースディレクトリを作成（存在しない場合）
        os.makedirs(self.base_dir, exist_ok=True)
    
    def save(self, file_like: BinaryIO, filename: str) -> Tuple[str, str]:
        """
        ファイルを保存し、(file_id, file_path) を返す
        
        チャンク書き込みでメモリを抑制（1MB単位）
        """
        # 期限切れファイルをクリーンアップ
        self._cleanup_expired()
        
        file_id = str(uuid.uuid4())
        # ファイル名にfile_idを含めて一意性を確保
        safe_filename = self._sanitize_filename(filename)
        file_path = os.path.join(self.base_dir, f"{file_id}_{safe_filename}")
        
        # チャンク書き込みでメモリを抑制
        with open(file_path, "wb") as f:
            while True:
                chunk = file_like.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
        
        # レジストリに登録
        self._file_registry[file_id] = FileEntry(
            file_id=file_id,
            file_path=file_path,
            original_filename=filename,
            created_at=datetime.now()
        )
        
        return file_id, file_path
    
    def get_path(self, file_id: str) -> Optional[str]:
        """
        file_id からファイルパスを取得（msoffcrypto 用）
        
        UnlockService が msoffcrypto にパスを渡すために使用
        """
        entry = self._file_registry.get(file_id)
        if not entry:
            return None
        
        if self.is_expired(file_id):
            self.delete(file_id)
            return None
        
        # ファイルが実際に存在するか確認
        if not os.path.exists(entry.file_path):
            del self._file_registry[file_id]
            return None
        
        return entry.file_path
    
    def load(self, file_id: str) -> Optional[bytes]:
        """
        file_id からファイル内容を取得（ダウンロード用）
        """
        file_path = self.get_path(file_id)
        if not file_path:
            return None
        
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except (IOError, OSError):
            return None
    
    def delete(self, file_id: str) -> bool:
        """
        ファイルを削除
        """
        entry = self._file_registry.get(file_id)
        if not entry:
            return False
        
        # ファイルを削除
        try:
            if os.path.exists(entry.file_path):
                os.remove(entry.file_path)
        except (IOError, OSError):
            pass  # ファイル削除失敗は無視（レジストリからは削除）
        
        # レジストリから削除
        del self._file_registry[file_id]
        return True
    
    def generate_download_url(self, file_id: str) -> str:
        """
        ダウンロード URL を生成
        
        MVP: /download/{file_id} を返すだけ（署名処理なし）
        """
        return f"/download/{file_id}"
    
    def get_filename(self, file_id: str) -> Optional[str]:
        """
        file_id から元のファイル名を取得
        """
        entry = self._file_registry.get(file_id)
        if not entry:
            return None
        return entry.original_filename
    
    def is_expired(self, file_id: str) -> bool:
        """
        file_id が期限切れかどうかを判定
        """
        entry = self._file_registry.get(file_id)
        if not entry:
            return True
        
        elapsed = (datetime.now() - entry.created_at).total_seconds()
        return elapsed > self.expiry_seconds
    
    def _cleanup_expired(self) -> None:
        """
        期限切れファイルを自動削除
        """
        expired_ids = [
            file_id for file_id in self._file_registry
            if self.is_expired(file_id)
        ]
        for file_id in expired_ids:
            self.delete(file_id)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        ファイル名をサニタイズ（パス区切り文字を除去）
        """
        # パス区切り文字を除去
        sanitized = filename.replace("/", "_").replace("\\", "_")
        # 空文字の場合はデフォルト名
        return sanitized if sanitized else "unnamed"
