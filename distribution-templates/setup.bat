@echo off
chcp 932 >nul
cd /d "%~dp0"

echo ==========================================
echo   Excel Unlocker 初回セットアップ
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

echo [INFO] イメージファイルを確認中...
if not exist "images\app.tar" (
    echo [ERROR] images\app.tar が見つかりません
    echo ZIP を正しく解凍したか確認してください
    echo.
    pause
    exit /b 1
)

echo Docker イメージを読み込んでいます...
echo (この処理は数分かかります)
echo.

echo [LOAD] app.tar を読み込み中...
docker load -i images\app.tar
if %ERRORLEVEL% neq 0 (
    echo [ERROR] イメージの読み込みに失敗しました
    echo Docker Desktop が起動しているか確認してください
    echo.
    pause
    exit /b 1
)

echo [OK] イメージの読み込み完了
echo.

echo ==========================================
echo   [COMPLETE] セットアップ完了
echo ==========================================
echo.
echo 次に start.bat をダブルクリックして起動してください
echo.
pause
