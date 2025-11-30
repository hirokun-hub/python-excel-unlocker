"""
/health エンドポイント

ヘルスチェック API を提供します。

Requirements: 4.4
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# ルーター定義
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    ヘルスチェックエンドポイント
    
    Docker コンテナの稼働状態を確認するために使用します。
    
    Returns:
        200 OK: {"status": "ok"}
    
    Requirements: 4.4
    """
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )
