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

echo "🔍 イメージファイルを確認中..."
if [ ! -f "images/app.tar" ]; then
    echo "❌ エラー: images/app.tar が見つかりません"
    echo "ZIP を正しく解凍したか確認してください"
    echo ""
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo "Docker イメージを読み込んでいます..."
echo "（この処理は数分かかります）"
echo ""

echo "📦 app.tar を読み込み中..."
if docker load -i images/app.tar; then
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
