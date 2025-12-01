#!/bin/bash

cd "$(dirname "$0")"

echo "=========================================="
echo "  Excel Unlocker 起動中"
echo "=========================================="
echo ""

echo "🔍 Docker Desktop の起動を確認中..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker Desktop が起動していません"
    echo "クジラのアイコンが表示されるまで待ってから再実行してください"
    echo ""
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo "✅ Docker Desktop が起動しています"
echo ""

echo "起動中です... (初回は少し時間がかかります)"
echo "起動したらブラウザで http://localhost:3000 を開いてください"
echo "停止するにはターミナルで Ctrl+C を押してください"
echo ""

docker compose up

echo ""
echo "アプリケーションを停止しました"
read -p "Enterキーを押して終了..."
