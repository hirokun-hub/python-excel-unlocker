#!/bin/bash

# ローカルAPI テストスクリプト
echo "=== AWS SAM ローカルAPI テスト ==="

# 1. SAMビルド
echo "1. SAMアプリケーションをビルド中..."
sam build
if [ $? -ne 0 ]; then
    echo "❌ SAMビルドに失敗しました"
    exit 1
fi
echo "✅ SAMビルド完了"

# 2. 個別Lambda関数テスト
echo ""
echo "2. 個別Lambda関数のテスト..."

echo "  - GetUploadUrlFunction テスト中..."
sam local invoke GetUploadUrlFunction --event events/get-upload-url-event.json > /tmp/get-upload-url-test.log 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ GetUploadUrlFunction テスト成功"
else
    echo "  ❌ GetUploadUrlFunction テスト失敗"
    cat /tmp/get-upload-url-test.log
fi

echo "  - UnlockFunction テスト中..."
sam local invoke UnlockFunction --event events/unlock-event.json > /tmp/unlock-test.log 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ UnlockFunction テスト成功"
else
    echo "  ❌ UnlockFunction テスト失敗"
    cat /tmp/unlock-test.log
fi

# 3. ローカルAPIサーバーテスト
echo ""
echo "3. ローカルAPIサーバーのテスト..."
echo "  - APIサーバーを起動中..."

# バックグラウンドでAPIサーバーを起動
sam local start-api --port 3001 > /tmp/api-server.log 2>&1 &
API_PID=$!

# サーバーの起動を待つ
sleep 8

# APIエンドポイントをテスト
echo "  - /presigned-urls エンドポイントをテスト中..."
curl -s -X POST http://localhost:3001/presigned-urls \
  -H "Content-Type: application/json" \
  -H "X-User-Email: user1@example.com" \
  -d '{"fileName": "test.xlsx", "fileSize": 1024, "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}' \
  > /tmp/api-test-result.json

if [ $? -eq 0 ]; then
    echo "  ✅ APIエンドポイント テスト成功"
    echo "  📄 レスポンス: $(cat /tmp/api-test-result.json | jq -r '.success')"
else
    echo "  ❌ APIエンドポイント テスト失敗"
fi

# APIサーバーを停止
kill $API_PID 2>/dev/null

echo ""
echo "=== テスト完了 ==="
echo "詳細なログは以下のファイルで確認できます："
echo "  - /tmp/get-upload-url-test.log"
echo "  - /tmp/unlock-test.log"
echo "  - /tmp/api-server.log"
echo "  - /tmp/api-test-result.json"