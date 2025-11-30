"""
設定管理モジュール

アプリケーション全体の設定を一元管理します。
環境変数からの読み込みとデフォルト値のフォールバックをサポートします。

Requirements: 5.1, 5.2, 5.3, 5.4
"""

import platform
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    
    環境変数が設定されている場合はその値を使用し、
    設定されていない場合はデフォルト値を使用します。
    """
    
    # サーバー設定
    PORT: int = 3000
    HOST: str = "0.0.0.0"
    
    # ファイル制限
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = ".xlsx,.xls"
    
    # 一時ディレクトリ（OS別デフォルト）
    TMP_DIR: str = (
        "C:\\tmp\\excel-unlocker" 
        if platform.system() == "Windows" 
        else "/tmp/excel-unlocker"
    )
    
    # 同時処理設定
    MAX_WORKERS: int = 4
    CLIENT_CONCURRENCY: int = 3
    
    # ダウンロード有効期限（秒）
    DOWNLOAD_EXPIRY_SECONDS: int = 300  # 5分
    
    # リトライ設定
    MAX_RETRY_COUNT: int = 3
    RETRY_AFTER_SECONDS: int = 5
    
    # Pydantic V2 の設定（ConfigDict を使用）
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """許可拡張子をリストとして取得"""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """最大ファイルサイズをバイト単位で取得"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# シングルトンインスタンス
settings = Settings()
