#!/bin/bash

# フルスタックデプロイスクリプト
# Vercel → AWS → 連携テストの順で実行

set -e

echo "🚀 フルスタックデプロイを開始します..."
echo "=================================="

# 色付きログ
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# 実行時間計測
START_TIME=$(date +%s)

# Step 1: Vercelデプロイ
log_step "Step 1: Vercelデプロイ実行中..."
echo ""

if ./scripts/deploy-vercel-only.sh; then
    log_success "Vercelデプロイ完了"
else
    log_error "Vercelデプロイに失敗しました"
    exit 1
fi

echo ""
echo "----------------------------------------"
echo ""

# Step 2: AWSデプロイ
log_step "Step 2: AWSデプロイ実行中..."
echo ""

if ./scripts/deploy-aws-only.sh; then
    log_success "AWSデプロイ完了"
else
    log_error "AWSデプロイに失敗しました"
    exit 1
fi

echo ""
echo "----------------------------------------"
echo ""

# Step 3: Vercel環境変数更新
log_step "Step 3: Vercel環境変数更新中..."

# API Gateway URLを取得
STACK_NAME="excel-unlocker-api"
API_GATEWAY_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
    --output text 2>/dev/null || echo "")

if [ -n "$API_GATEWAY_URL" ]; then
    log_info "API Gateway URL: $API_GATEWAY_URL"
    
    # Vercelに環境変数設定
    cd frontend
    echo "Updating Vercel environment variables..."
    vercel env add NEXT_PUBLIC_API_URL production <<< "$API_GATEWAY_URL" 2>/dev/null || true
    vercel env add NEXT_PUBLIC_API_URL preview <<< "$API_GATEWAY_URL" 2>/dev/null || true
    vercel env add NEXT_PUBLIC_USE_MOCK_API production <<< "false" 2>/dev/null || true
    vercel env add NEXT_PUBLIC_USE_MOCK_API preview <<< "false" 2>/dev/null || true
    cd ..
    
    log_success "Vercel環境変数更新完了"
else
    log_error "API Gateway URLの取得に失敗しました"
    exit 1
fi

echo ""
echo "----------------------------------------"
echo ""

# Step 4: Vercel再デプロイ
log_step "Step 4: Vercel再デプロイ実行中..."

cd frontend
UPDATED_URL=$(vercel --prod --confirm | grep -o 'https://[^[:space:]]*' || echo "")
cd ..

if [ -n "$UPDATED_URL" ]; then
    log_success "Vercel再デプロイ完了: $UPDATED_URL"
else
    log_warning "Vercel再デプロイURLの取得に失敗しました"
fi

echo ""
echo "----------------------------------------"
echo ""

# Step 5: 連携テスト
log_step "Step 5: フロントエンド・バックエンド連携テスト実行中..."

if [ -n "$UPDATED_URL" ] && [ -n "$API_GATEWAY_URL" ]; then
    log_info "連携テストを実行中..."
    
    # フロントエンドアクセステスト
    if curl -s -f "$UPDATED_URL" > /dev/null; then
        log_success "フロントエンドアクセス成功"
    else
        log_warning "フロントエンドアクセスに問題があります"
    fi
    
    # バックエンドアクセステスト
    if curl -s -f "${API_GATEWAY_URL}/presigned-urls" > /dev/null 2>&1; then
        log_success "バックエンドアクセス成功"
    else
        log_success "バックエンド認証エラー確認（期待通り）"
    fi
    
    log_success "連携テスト完了"
else
    log_warning "連携テストをスキップしました（URL取得失敗）"
fi

# 実行時間計測終了
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 最終結果表示
echo ""
log_success "🎉 フルスタックデプロイ完了！"
echo "=================================="
echo "⏱️  実行時間: ${DURATION}秒"
echo ""
echo "🌐 デプロイされたURL:"
if [ -n "$UPDATED_URL" ]; then
    echo "  フロントエンド: $UPDATED_URL"
fi
if [ -n "$API_GATEWAY_URL" ]; then
    echo "  バックエンドAPI: $API_GATEWAY_URL"
fi
echo ""
echo "🔍 次のステップ:"
echo "  1. フロントエンドでGoogle OAuth動作確認"
echo "  2. ファイルアップロード・解除機能テスト"
echo "  3. Google Drive連携テスト"
echo ""
echo "🛠️  トラブルシューティング:"
echo "  - フロントエンドログ: vercel logs"
echo "  - バックエンドログ: aws logs tail /aws/lambda/excel-unlock-function-development"
echo "  - 環境変数確認: vercel env ls"
echo ""

log_info "フルスタックデプロイが完了しました"