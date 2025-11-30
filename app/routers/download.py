"""
/download エンドポイント

解除済み Excel ファイルのダウンロード API を提供します。

Requirements: API仕様（/download/{file_id}）、ダウンロードURLの有効期限
"""

import logging
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

# ロガー設定
logger = logging.getLogger(__name__)

# ルーター定義
router = APIRouter(tags=["download"])


@router.get("/download/{file_id}")
async def download_file(request: Request, file_id: str) -> Response:
    """
    解除済み Excel ファイルをダウンロード
    
    Args:
        request: FastAPI リクエストオブジェクト
        file_id: ファイルID（StorageService.save で生成）
    
    Returns:
        成功時: ファイルのバイナリデータ（Content-Disposition 付き）
        エラー時: 404 {"error": "Not Found", "message": "ファイルが見つかりません"}
    
    Requirements: API仕様（/download/{file_id}）、ダウンロードURLの有効期限
    """
    storage_service = request.app.state.storage_service
    
    # ファイル内容を取得（存在しない/期限切れの場合は None）
    content = storage_service.load(file_id)
    
    if content is None:
        logger.warning(f"File not found or expired: {file_id}")
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "ファイルが見つかりません"
            }
        )
    
    # ファイル名を取得
    filename = storage_service.get_filename(file_id)
    if filename is None:
        filename = "download.xlsx"
    
    # ダウンロード成功時は必ず storage.delete を呼び出す
    storage_service.delete(file_id)
    logger.info(f"File downloaded and deleted: {file_id} ({filename})")
    
    # Content-Disposition ヘッダーを設定（日本語ファイル名対応）
    # RFC 5987 に準拠した UTF-8 エンコーディング
    encoded_filename = quote(filename)
    content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
    
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": content_disposition
        }
    )
