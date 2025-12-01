@echo off
chcp 932 >nul
cd /d "%~dp0"

echo ==========================================
echo   Excel Unlocker 起動中
echo ==========================================
echo.

echo [INFO] Docker Desktop の起動を確認中...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Desktop が起動していません
    echo.
    echo 以下の手順を実行してください:
    echo 1. Docker Desktop を起動
    echo 2. クジラのアイコンが表示されるまで待つ
    echo 3. このスクリプトを再実行
    echo.
    pause
    exit /b 1
)

echo [OK] Docker Desktop が起動しています
echo.
echo 起動中です...
echo (初回は少し時間がかかります)
echo.
echo 起動したらブラウザで次を開いてください:
echo   http://localhost:3000
echo.
echo 停止するには Ctrl+C を押してください
echo.
echo ==========================================
echo.

docker compose up

echo.
echo アプリケーションを停止しました
pause
