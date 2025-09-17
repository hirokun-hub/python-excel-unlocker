#!/bin/bash

# 統合テスト実行スクリプト

set -e

echo "🧪 Secure Excel Unlock 統合テスト実行"
echo "=================================="

# 環境変数ファイルの確認
if [ ! -f ".env.test" ]; then
    echo "❌ .env.testファイルが見つかりません"
    echo "📝 .env.test.exampleをコピーして設定してください:"
    echo "   cp .env.test.example .env.test"
    echo "   # .env.testを編集して実際の値を設定"
    exit 1
fi

# 依存関係のインストール
echo "📦 依存関係のインストール中..."
npm install

# テスト環境のセットアップ
echo "🚀 テスト環境セットアップ中..."
npm run setup

# テスト実行
echo "🧪 統合テスト実行中..."

# 引数に応じてテストを実行
case "${1:-all}" in
    "api")
        echo "🔌 API統合テストのみ実行"
        npm run test:api
        ;;
    "s3")
        echo "📦 S3連携テストのみ実行"
        npm run test:s3
        ;;
    "e2e")
        echo "🔄 E2Eテストのみ実行"
        npm run test:e2e
        ;;
    "all")
        echo "🎯 全統合テスト実行"
        npm test
        ;;
    *)
        echo "❌ 無効な引数: $1"
        echo "使用方法: $0 [api|s3|e2e|all]"
        exit 1
        ;;
esac

# テスト結果の表示
if [ $? -eq 0 ]; then
    echo "✅ 統合テスト完了"
    
    # クリーンアップの確認
    read -p "🧹 テスト環境をクリーンアップしますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 クリーンアップ実行中..."
        npm run cleanup
        echo "✅ クリーンアップ完了"
    fi
else
    echo "❌ 統合テスト失敗"
    exit 1
fi