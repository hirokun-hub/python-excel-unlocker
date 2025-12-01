from typing import List
from datetime import datetime, timezone
import logging
from urllib.parse import quote

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.zip_service import ZipService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["download"])

class BulkDownloadRequest(BaseModel):
    fileIds: List[str] = Field(..., min_items=1, max_items=100)

@router.post("/download/bulk")
def bulk_download(
    request: Request,
    body: BulkDownloadRequest
) -> Response:
    """
    複数ファイルをZIP形式で一括ダウンロード

    Returns:
        HTTP 200: ZIPバイナリストリーム
        HTTP 206: JSON（部分成功、downloadUrl含む）
        HTTP 400: バリデーションエラー
        HTTP 404: 全ファイル不在
        HTTP 500: ZIP生成失敗
    """
    storage_service: StorageService = request.app.state.storage_service
    zip_service = ZipService(storage_service)

    try:
        # ZIP生成
        zip_buffer, successful_ids, missing_ids = zip_service.create_zip(body.fileIds)

        # 全件失敗
        if not successful_ids:
             return JSONResponse(
                status_code=404,
                content={"error": "ファイルが見つかりません"}
            )

        filename = f"解除済み_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%SZ')}.zip"

        # 部分成功 (HTTP 206)
        if missing_ids:
            zip_id, _ = zip_service.save_temp_zip(zip_buffer, filename)
            return JSONResponse(
                status_code=206,
                content={
                    "status": "partial",
                    "downloadUrl": f"/download/bulk/{zip_id}",
                    "downloadedCount": len(successful_ids),
                    "missingCount": len(missing_ids),
                    "message": f"{len(missing_ids)}件のファイルが見つかりませんでした",
                    "successfulIds": successful_ids
                }
            )

        # 全件成功 (HTTP 200)
        encoded_filename = quote(filename)
        content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"

        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": content_disposition
            }
        )

    except Exception as e:
        logger.exception(f"Bulk download failed: {e}")
        return JSONResponse(status_code=500, content={"error": "ZIP生成に失敗しました"})


@router.get("/download/bulk/{zip_id}")
def download_bulk_zip(
    request: Request,
    zip_id: str
) -> Response:
    """
    一時保存されたZIPファイルをダウンロード (部分成功時用)
    """
    storage_service: StorageService = request.app.state.storage_service

    # ファイル名を取得
    filename = storage_service.get_filename(zip_id)
    if not filename:
        return JSONResponse(status_code=404, content={"error": "Not Found"})

    # コンテンツを取得
    content = storage_service.load_zip(zip_id)
    if content is None:
        return JSONResponse(status_code=404, content={"error": "Not Found"})

    encoded_filename = quote(filename)
    content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"

    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": content_disposition
        }
    )
