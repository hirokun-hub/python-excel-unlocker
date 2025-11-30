"""
Pydantic スキーマ定義

API リクエスト/レスポンスの型定義を提供します。

Requirements: API仕様
"""

from typing import Optional

from pydantic import BaseModel, Field


class UnlockRequest(BaseModel):
    """
    /unlock エンドポイントのリクエストスキーマ
    
    Note: 実際のエンドポイントでは multipart/form-data を使用するため、
    このスキーマは主にドキュメント生成と型定義の参照用です。
    """
    password1: str = Field(..., description="第1パスワード（必須）")
    password2: Optional[str] = Field(None, description="第2パスワード（任意、空欄可）")


class UnlockResponse(BaseModel):
    """
    /unlock エンドポイントのレスポンススキーマ
    
    成功時:
        - fileName: 解除後のファイル名
        - status: "success"
        - message: None
        - downloadUrl: ダウンロード URL
    
    エラー時:
        - fileName: 元のファイル名
        - status: "error"
        - message: エラーメッセージ
        - downloadUrl: None
    """
    fileName: str = Field(..., description="ファイル名")
    status: str = Field(..., description="処理結果（'success' または 'error'）")
    message: Optional[str] = Field(None, description="エラーメッセージ（成功時は None）")
    downloadUrl: Optional[str] = Field(None, description="ダウンロード URL（エラー時は None）")


class TooManyRequestsResponse(BaseModel):
    """
    HTTP 429 Too Many Requests のレスポンススキーマ
    
    同時リクエスト数が MAX_WORKERS を超えた場合に返却されます。
    
    Requirements: 1.5
    """
    error: str = Field(default="Too Many Requests", description="エラー種別")
    message: str = Field(
        default="サーバーが混雑しています。しばらく待ってから再試行してください。",
        description="ユーザー向けメッセージ"
    )
    retryAfter: int = Field(default=5, description="リトライまでの待機秒数")


class HealthResponse(BaseModel):
    """
    /health エンドポイントのレスポンススキーマ
    
    Requirements: 4.4
    """
    status: str = Field(default="ok", description="ヘルスステータス")


class NotFoundResponse(BaseModel):
    """
    HTTP 404 Not Found のレスポンススキーマ
    
    ファイルが見つからない/期限切れの場合に返却されます。
    """
    error: str = Field(default="Not Found", description="エラー種別")
    message: str = Field(
        default="ファイルが見つかりません",
        description="ユーザー向けメッセージ"
    )


class ErrorMessages:
    """
    エラーメッセージ定数クラス
    
    アプリケーション全体で使用するエラーメッセージを一元管理します。
    """
    PASSWORD_INCORRECT = "パスワードが正しくありません"
    PASSWORD_NOT_SET = "パスワードが設定されていません"
    FILE_NOT_FOUND = "ファイルが見つかりません"
    UNSUPPORTED_FORMAT = "サポートされていないファイル形式です"
    FILE_TOO_LARGE = "ファイルサイズが大きすぎます"
    SERVER_BUSY = "サーバーが混雑しています。しばらく待ってから再試行してください。"
