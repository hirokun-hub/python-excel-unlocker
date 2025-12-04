#!/bin/bash

# カレントディレクトリをスクリプトの場所に変更
cd "$(dirname "$0")"

echo "=========================================="
echo "  Excel Unlocker 初回セットアップ"
echo "=========================================="
echo ""

echo "🔍 Docker Desktop の起動を確認中..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ エラー: Docker Desktop が起動していません"
    echo ""
    echo "以下の手順を実行してください："
    echo "1. Docker Desktop を起動"
    echo "2. クジラのアイコンが表示されるまで待つ"
    echo "3. このスクリプトを再実行"
    echo ""
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo "✅ Docker Desktop が起動しています"
echo ""

echo "🔍 アーキテクチャを判定中..."
ARCH=$(docker info --format '{{.Architecture}}' 2>/dev/null || true)
case "$ARCH" in
  x86_64|amd64) ARCH=amd64 ;;
  aarch64|arm64) ARCH=arm64 ;;
  *) echo "❌ エラー: アーキテクチャを取得できませんでした ($ARCH)"; read -p "Enterキーを押して終了..."; exit 1 ;;
esac
IMAGE_TAR="images/app_linux-${ARCH}.tar"

echo "🔍 イメージファイルを確認中 (${IMAGE_TAR})..."
if [ ! -f "$IMAGE_TAR" ]; then
    echo "❌ エラー: ${IMAGE_TAR} が見つかりません"
    echo "ZIP を正しく解凍したか確認してください"
    echo ""
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo "Docker イメージを読み込んでいます..."
echo "（この処理は数分かかります）"
echo ""

echo "📦 ${IMAGE_TAR} を読み込み中..."
if docker load -i "$IMAGE_TAR"; then
    echo "✅ イメージの読み込み完了"
else
    echo "❌ エラー: イメージの読み込みに失敗しました"
    echo "Docker Desktop が起動しているか確認してください"
    echo ""
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ セットアップ完了！"
echo "=========================================="
echo ""
echo "次に start.command をダブルクリックして起動してください"
echo ""
read -p "Enterキーを押して終了..."
