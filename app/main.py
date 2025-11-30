"""
FastAPI アプリケーションエントリポイント

Excel パスワード解除ツールのメインアプリケーションを定義します。

Requirements: 4.3
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.storage_service import LocalStorageService
from app.services.unlock_service import UnlockService

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 同時リクエスト制御用 Semaphore（Requirements: 1.5）
request_semaphore: asyncio.Semaphore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    アプリケーションのライフサイクル管理
    
    起動時: Semaphore の初期化、サービスのセットアップ
    終了時: リソースのクリーンアップ
    """
    global request_semaphore
    
    # Semaphore を初期化（MAX_WORKERS で制限）
    request_semaphore = asyncio.Semaphore(settings.MAX_WORKERS)
    logger.info(f"Semaphore initialized with MAX_WORKERS={settings.MAX_WORKERS}")
    
    # StorageService と UnlockService を初期化
    storage_service = LocalStorageService()
    unlock_service = UnlockService(storage_service)
    
    # アプリケーション状態に保存
    app.state.storage_service = storage_service
    app.state.unlock_service = unlock_service
    
    logger.info(f"Excel Unlocker started on {settings.HOST}:{settings.PORT}")
    logger.info(f"TMP_DIR: {settings.TMP_DIR}")
    
    yield
    
    # クリーンアップ処理
    logger.info("Excel Unlocker shutting down...")


# FastAPI アプリケーションの初期化
app = FastAPI(
    title="Excel Unlocker",
    description="パスワード付き Excel ファイルを解除する Web アプリケーション",
    version="1.0.0",
    lifespan=lifespan
)

# 静的ファイル配信の設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 テンプレートの設定
templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    グローバル例外ハンドラー
    
    予期せぬ例外をキャッチしてログ出力し、500エラーを返す
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "予期せぬエラーが発生しました"
        }
    )


def get_semaphore() -> asyncio.Semaphore:
    """
    Semaphore インスタンスを取得
    
    Returns:
        同時リクエスト制御用 Semaphore
    
    Raises:
        RuntimeError: Semaphore が初期化されていない場合
    """
    if request_semaphore is None:
        raise RuntimeError("Semaphore not initialized")
    return request_semaphore


async def try_acquire_semaphore() -> bool:
    """
    Semaphore の取得を試み、取得できない場合は False を返す
    
    同時リクエスト数が MAX_WORKERS を超える場合、
    HTTP 429 を返すために使用します。
    
    Returns:
        True: Semaphore を取得できた（呼び出し側で release() が必要）
        False: Semaphore を取得できなかった（429 を返すべき）
    
    Requirements: 1.5
    """
    semaphore = get_semaphore()
    # locked() が True の場合、Semaphore のカウンタが 0（取得不可）
    if semaphore.locked():
        return False
    # 取得を試みる
    await semaphore.acquire()
    return True


def release_semaphore() -> None:
    """
    Semaphore を解放
    
    try_acquire_semaphore() で取得した後、処理完了時に呼び出す
    """
    semaphore = get_semaphore()
    semaphore.release()


def create_too_many_requests_response() -> JSONResponse:
    """
    HTTP 429 Too Many Requests レスポンスを生成
    
    Requirements: 1.5
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "サーバーが混雑しています。しばらく待ってから再試行してください。",
            "retryAfter": settings.RETRY_AFTER_SECONDS
        },
        headers={
            "Retry-After": str(settings.RETRY_AFTER_SECONDS)
        }
    )


# ルーターの登録
from app.routers import unlock, download, health
app.include_router(unlock.router)
app.include_router(download.router)
app.include_router(health.router)


# 一時的なルートエンドポイント（ルーター実装前の動作確認用）
@app.get("/")
async def root(request: Request):
    """
    ルートエンドポイント（Web UI）
    
    Jinja2 テンプレートを使用して index.html を返す
    """
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "client_concurrency": settings.CLIENT_CONCURRENCY,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
