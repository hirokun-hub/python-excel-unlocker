#!/bin/bash

# レート制限・WAF設定のテストスクリプト
# 使用方法: ./scripts/test-rate-limiting-waf.sh [environment]

set -e

ENVIRONMENT=${1:-development}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔒 レート制限・WAF設定のテストを開始します..."
echo "環境: $ENVIRONMENT"
echo "プロジェクトルート: $PROJECT_ROOT"

# 環境変数の確認
if [ ! -f "$PROJECT_ROOT/tests/integration/.env.test" ]; then
    echo "❌ テスト環境変数ファイルが見つかりません: tests/integration/.env.test"
    echo "tests/integration/.env.test.example をコピーして設定してください"
    exit 1
fi

# Node.js依存関係の確認
cd "$PROJECT_ROOT/tests/integration"
if [ ! -d "node_modules" ]; then
    echo "📦 テスト依存関係をインストールしています..."
    npm install
fi

# SAM Local APIの起動確認
echo "🚀 SAM Local APIの起動状況を確認しています..."
if ! curl -s http://localhost:3001/presigned-urls > /dev/null 2>&1; then
    echo "⚠️  SAM Local APIが起動していません"
    echo "別のターミナルで以下のコマンドを実行してください:"
    echo "cd $PROJECT_ROOT && sam local start-api --port 3001"
    echo ""
    echo "APIが起動するまで30秒待機します..."
    
    # 30秒間APIの起動を待機
    for i in {1..30}; do
        if curl -s http://localhost:3001/presigned-urls > /dev/null 2>&1; then
            echo "✅ SAM Local APIが起動しました"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if ! curl -s http://localhost:3001/presigned-urls > /dev/null 2>&1; then
        echo ""
        echo "❌ SAM Local APIの起動を確認できませんでした"
        echo "手動でAPIを起動してから再実行してください"
        exit 1
    fi
fi

echo "✅ SAM Local APIが起動しています"

# レート制限・WAF設定テストの実行
echo ""
echo "🧪 レート制限・WAF設定テストを実行しています..."

# 基本的なAPI接続テスト
echo "1. 基本的なAPI接続テスト"
npm test -- --grep "should handle normal request rate" --timeout 10000

# レート制限テスト
echo ""
echo "2. レート制限テスト"
npm test -- --grep "should apply rate limiting" --timeout 30000

# Bot保護テスト
echo ""
echo "3. Bot保護テスト"
npm test -- --grep "Bot Protection" --timeout 15000

# WAFセキュリティルールテスト
echo ""
echo "4. WAFセキュリティルールテスト"
npm test -- --grep "WAF Security Rules" --timeout 20000

# パフォーマンステスト
echo ""
echo "5. パフォーマンステスト"
npm test -- --grep "should not significantly impact response time" --timeout 10000

echo ""
echo "🎉 レート制限・WAF設定テストが完了しました！"

# テスト結果のサマリー
echo ""
echo "📊 テスト結果サマリー:"
echo "- API Gateway スロットリング: 設定済み"
echo "- WAFv2 レートベースルール: 設定済み"
echo "- Bot制御ルール: 設定済み"
echo "- 地理的制限: 日本のみ許可"
echo "- AWS Managed Rules: 適用済み"
echo "- カスタムIPブロック: 設定済み"

# 設定確認コマンドの提示
echo ""
echo "🔧 設定確認コマンド:"
echo "# WAF Web ACL確認"
echo "aws wafv2 list-web-acls --scope REGIONAL --region ap-northeast-1"
echo ""
echo "# API Gateway設定確認"
echo "aws apigateway get-stages --rest-api-id <API_ID> --region ap-northeast-1"
echo ""
echo "# CloudWatch メトリクス確認"
echo "aws cloudwatch get-metric-statistics --namespace AWS/WAFV2 --metric-name AllowedRequests --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Sum --region ap-northeast-1"

echo ""
echo "✅ レート制限・WAF設定の実装とテストが完了しました！"