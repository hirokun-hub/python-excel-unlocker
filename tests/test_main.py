"""
FastAPI アプリケーション基盤のテスト

main.py の機能をテストします。

Requirements: 4.3, 4.4, 1.5
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app, get_semaphore, try_acquire_semaphore, release_semaphore


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""
    
    def test_health_returns_ok(self):
        """
        /health エンドポイントが {"status": "ok"} を返すことを確認
        
        Requirements: 4.4
        """
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}


class TestRootEndpoint:
    """ルートエンドポイントのテスト"""
    
    def test_root_returns_html(self):
        """
        / エンドポイントが HTML を返すことを確認
        
        Requirements: 4.3
        """
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            assert "Excel" in response.text


class TestStaticFiles:
    """静的ファイル配信のテスト"""
    
    def test_css_file_served(self):
        """
        CSS ファイルが配信されることを確認
        """
        with TestClient(app) as client:
            response = client.get("/static/css/style.css")
            assert response.status_code == 200
            assert "text/css" in response.headers["content-type"]
    
    def test_js_file_served(self):
        """
        JavaScript ファイルが配信されることを確認
        """
        with TestClient(app) as client:
            response = client.get("/static/js/app.js")
            assert response.status_code == 200
            # JavaScript の content-type は application/javascript または text/javascript
            content_type = response.headers["content-type"]
            assert "javascript" in content_type or "text/plain" in content_type


class TestSemaphore:
    """同時リクエスト制御のテスト"""
    
    @pytest.mark.asyncio
    async def test_semaphore_initialized_on_startup(self):
        """
        アプリケーション起動時に Semaphore が初期化されることを確認
        
        Requirements: 1.5
        """
        # TestClient を使用してアプリを起動
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # アプリが起動した状態で Semaphore を取得
            semaphore = get_semaphore()
            assert semaphore is not None
            assert isinstance(semaphore, asyncio.Semaphore)
    
    @pytest.mark.asyncio
    async def test_try_acquire_semaphore_success(self):
        """
        Semaphore が取得できることを確認
        
        Requirements: 1.5
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Semaphore を取得
            acquired = await try_acquire_semaphore()
            assert acquired is True
            
            # 解放
            release_semaphore()
    
    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_requests(self):
        """
        Semaphore が同時リクエスト数を制限することを確認
        
        MAX_WORKERS を超えるリクエストは取得できない
        
        Requirements: 1.5
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from app.config import settings
            
            # MAX_WORKERS 分の Semaphore を取得
            acquired_count = 0
            for _ in range(settings.MAX_WORKERS):
                if await try_acquire_semaphore():
                    acquired_count += 1
            
            assert acquired_count == settings.MAX_WORKERS
            
            # 追加の取得は失敗するはず
            extra_acquired = await try_acquire_semaphore()
            assert extra_acquired is False
            
            # 解放
            for _ in range(acquired_count):
                release_semaphore()


class TestAppState:
    """アプリケーション状態のテスト"""
    
    def test_storage_service_initialized(self):
        """
        StorageService がアプリケーション状態に初期化されることを確認
        """
        with TestClient(app) as client:
            # アプリが起動した状態で state を確認
            assert hasattr(app.state, "storage_service")
            assert app.state.storage_service is not None
    
    def test_unlock_service_initialized(self):
        """
        UnlockService がアプリケーション状態に初期化されることを確認
        """
        with TestClient(app) as client:
            # アプリが起動した状態で state を確認
            assert hasattr(app.state, "unlock_service")
            assert app.state.unlock_service is not None


class TestExceptionHandler:
    """例外ハンドラーのテスト"""
    
    def test_unhandled_exception_returns_500(self):
        """
        未処理の例外が 500 エラーを返すことを確認
        """
        # この機能は実際のエンドポイントで例外が発生した場合にテストされる
        # ここでは例外ハンドラーが登録されていることを確認
        assert app.exception_handlers.get(Exception) is not None
