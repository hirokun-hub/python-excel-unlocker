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

echo [INFO] アーキテクチャを判定中...
for /f %%i in ('docker info --format "{{.Architecture}}"') do set ARCH=%%i
if "%ARCH%"=="" (
    echo [ERROR] アーキテクチャを取得できませんでした
    echo.
    pause
    exit /b 1
)
if /I "%ARCH%"=="x86_64" set ARCH=amd64
if /I "%ARCH%"=="amd64" set ARCH=amd64
if /I "%ARCH%"=="aarch64" set ARCH=arm64
if /I "%ARCH%"=="arm64" set ARCH=arm64
set IMAGE_TAR=imagespp_linux-%ARCH%.tar

echo [INFO] イメージファイルを確認中 (%IMAGE_TAR%)...
if not exist "%IMAGE_TAR%" (
    echo [ERROR] %IMAGE_TAR% が見つかりません
    echo ZIP を正しく解凍したか確認してください
    echo.
    pause
    exit /b 1
)

echo Docker イメージを読み込んでいます...
echo (この処理は数分かかります)
echo.

echo [LOAD] %IMAGE_TAR% を読み込み中...
docker load -i "%IMAGE_TAR%"
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
