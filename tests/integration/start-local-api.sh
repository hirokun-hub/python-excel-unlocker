#!/bin/bash

# SAM Local API起動スクリプト

set -e

echo "🚀 SAM Local API起動中..."

# 環境変数の設定
export S3_BUCKET_NAME=excel-unlocker-test-bucket-101271927126-ap-northeast-1
export ALLOWED_USERS=hironomac2025@gmail.com
export LOG_LEVEL=DEBUG

# SAM Local API起動
echo "📡 ポート3001でAPI起動中..."
sam local start-api --port 3001 --env-vars tests/integration/env.json &

# プロセスIDを保存
echo $! > tests/integration/sam-local.pid

echo "✅ SAM Local API起動完了"
echo "📍 API URL: http://localhost:3001"
echo "🛑 停止するには: kill \$(cat tests/integration/sam-local.pid)"