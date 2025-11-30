"""
/unlock エンドポイント

Excel ファイルのパスワード解除 API を提供します。

Requirements: 1.1, 1.2, 1.3, 1.6, 6.2, 6.3
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.unlock_service import ErrorMessages

# ロガー設定
logger = logging.getLogger(__name__)

# ルーター定義
router = APIRouter(tags=["unlock"])


def validate_file_extension(filename: str) -> bool:
    """
    ファイル拡張子を検証
    
    Args:
        filename: ファイル名
    
    Returns:
        許可された拡張子の場合 True
    
    Requirements: 6.2
    """
    if not filename:
        return False
    
    # 拡張子を取得（小文字に変換）
    lower_filename = filename.lower()
    
    # 許可された拡張子のいずれかで終わるかチェック
    for ext in settings.allowed_extensions_list:
        if lower_filename.endswith(ext):
            return True
    
    return False


def validate_file_size(content_length: Optional[int]) -> bool:
    """
    ファイルサイズを検証
    
    Args:
        content_length: ファイルサイズ（バイト）
    
    Returns:
        許可されたサイズ以下の場合 True
    
    Requirements: 6.3
    """
    if content_length is None:
        # サイズ不明の場合は許可（後でチェック）
        return True
    
    return content_length <= settings.max_file_size_bytes


async def get_file_size(file: UploadFile) -> int:
    """
    UploadFile の実際のサイズを取得
    
    Args:
        file: アップロードされたファイル
    
    Returns:
        ファイルサイズ（バイト）
    """
    # ファイル全体を読み込んでサイズを取得
    content = await file.read()
    size = len(content)
    # ファイルポインタを先頭に戻す
    await file.seek(0)
    return size


@router.post("/unlock")
async def unlock_file(
    request: Request,
    file: UploadFile = File(..., description="解除対象の Excel ファイル"),
    password1: str = Form(..., description="第1パスワード（必須）"),
    password2: Optional[str] = Form(None, description="第2パスワード（任意）")
) -> JSONResponse:
    """
    Excel ファイルのパスワードを解除
    
    multipart/form-data で以下を受け取る:
    - file: Excel ファイル（.xlsx または .xls）
    - password1: 第1パスワード（必須）
    - password2: 第2パスワード（任意、空欄可）
    
    Returns:
        成功時: {"fileName": str, "status": "success", "message": null, "downloadUrl": str}
        エラー時: {"fileName": str, "status": "error", "message": str, "downloadUrl": null}
    
    Requirements: 1.1, 1.2, 1.3, 1.6, 6.2, 6.3
    """
    # main.py から Semaphore 関連の関数をインポート
    from app.main import (
        try_acquire_semaphore,
        release_semaphore,
        create_too_many_requests_response
    )
    
    filename = file.filename or "unknown"
    
    # === バリデーション（save 前に実施）===
    
    # 1. 拡張子チェック（Requirements: 6.2）
    if not validate_file_extension(filename):
        logger.warning(f"Invalid file extension: {filename}")
        return JSONResponse(
            status_code=400,
            content={
                "fileName": filename,
                "status": "error",
                "message": ErrorMessages.UNSUPPORTED_FORMAT,
                "downloadUrl": None
            }
        )
    
    # 2. ファイルサイズチェック（Requirements: 6.3）
    file_size = await get_file_size(file)
    if file_size > settings.max_file_size_bytes:
        logger.warning(
            f"File too large: {filename} ({file_size} bytes > {settings.max_file_size_bytes} bytes)"
        )
        return JSONResponse(
            status_code=400,
            content={
                "fileName": filename,
                "status": "error",
                "message": ErrorMessages.FILE_TOO_LARGE,
                "downloadUrl": None
            }
        )
    
    # === 同時リクエスト制御（Requirements: 1.5）===
    acquired = await try_acquire_semaphore()
    if not acquired:
        logger.warning("Too many concurrent requests, returning 429")
        return create_too_many_requests_response()
    
    try:
        # === ファイル保存と解除処理 ===
        storage_service = request.app.state.storage_service
        unlock_service = request.app.state.unlock_service
        
        # バリデーション通過後に storage.save でファイル保存
        file_id, _ = storage_service.save(file.file, filename)
        logger.info(f"File saved: {filename} -> {file_id}")
        
        try:
            # unlock_service.unlock で解除処理
            result = unlock_service.unlock(
                file_id=file_id,
                password1=password1,
                password2=password2 if password2 else None
            )
            
            if result["success"]:
                # 解除成功
                download_url = storage_service.generate_download_url(
                    result["unlocked_file_id"]
                )
                logger.info(
                    f"Unlock success: {filename} -> {result['unlocked_filename']}"
                )
                
                # 元ファイルを削除（Requirements: 1.4）
                storage_service.delete(file_id)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "fileName": result["unlocked_filename"],
                        "status": "success",
                        "message": None,
                        "downloadUrl": download_url
                    }
                )
            else:
                # 解除失敗（パスワード不正、パスワード未設定など）
                logger.warning(f"Unlock failed: {filename} - {result['message']}")
                
                # 元ファイルを削除（Requirements: 1.4）
                storage_service.delete(file_id)
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "fileName": filename,
                        "status": "error",
                        "message": result["message"],
                        "downloadUrl": None
                    }
                )
        
        except Exception as e:
            # 予期せぬエラー時も元ファイルを削除
            logger.exception(f"Unexpected error during unlock: {e}")
            storage_service.delete(file_id)
            raise
    
    finally:
        # Semaphore を解放
        release_semaphore()
