#!/bin/bash

# AWS単体デプロイスクリプト
# Vercel設定は一切触らず、AWSのみに集中

set -e

echo "☁️  AWS単体デプロイを開始します..."
echo "=================================="

# 色付きログ
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. 前提条件確認
log_info "AWS前提条件を確認中..."

# AWS CLI確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    echo "インストール方法:"
    echo "  macOS: brew install awscli"
    exit 1
fi

# SAM CLI確認
if ! command -v sam &> /dev/null; then
    log_error "SAM CLI がインストールされていません"
    echo "インストール方法:"
    echo "  macOS: brew install aws-sam-cli"
    exit 1
fi

# AWS認証確認
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS認証が設定されていません"
    echo "設定方法:"
    echo "  aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "ap-northeast-1")
log_success "AWS認証済み: $AWS_ACCOUNT_ID ($AWS_REGION)"

# 2. 環境変数確認
log_info "バックエンド環境変数を確認中..."

BACKEND_ENV="backend/.env.local"
if [ ! -f "$BACKEND_ENV" ]; then
    log_warning "バックエンド環境変数ファイルが見つかりません"
    log_info "自動生成します..."
    
    # 環境変数自動生成
    cat > "$BACKEND_ENV" << EOF
# AWS設定
AWS_REGION=$AWS_REGION
AWS_PROFILE=default

# S3設定
S3_BUCKET_NAME=excel-unlocker-bucket-development-${AWS_ACCOUNT_ID}-${AWS_REGION}

# 認証設定
ALLOWED_USERS=hironomac2025@gmail.com

# ログ設定
LOG_LEVEL=INFO
AWS_LAMBDA_LOG_LEVEL=INFO

# 環境識別
ENVIRONMENT=development
EOF
    
    log_success "バックエンド環境変数を自動生成: $BACKEND_ENV"
fi

# 3. SAMビルド
log_info "SAMビルドを実行中..."
if sam build; then
    log_success "SAMビルド成功"
else
    log_error "SAMビルドに失敗しました"
    exit 1
fi

# 4. 初回デプロイ確認
log_info "CloudFormationスタック確認中..."

STACK_NAME="excel-unlocker-api"
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" &> /dev/null; then
    log_success "既存スタック検出: $STACK_NAME"
    DEPLOY_MODE="update"
else
    log_info "新規スタック作成: $STACK_NAME"
    DEPLOY_MODE="create"
fi

# 5. デプロイ実行
if [ "$DEPLOY_MODE" = "create" ]; then
    log_info "初回デプロイを実行中（ガイド付き）..."
    sam deploy --guided
else
    log_info "スタック更新を実行中..."
    sam deploy
fi

# 6. デプロイ結果確認
log_info "デプロイ結果を確認中..."

# API Gateway URL取得
API_GATEWAY_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
    --output text 2>/dev/null || echo "")

if [ -n "$API_GATEWAY_URL" ]; then
    log_success "API Gateway URL: $API_GATEWAY_URL"
    
    # フロントエンド環境変数更新
    FRONTEND_ENV="frontend/.env.local"
    if [ -f "$FRONTEND_ENV" ]; then
        # API URLを更新
        if grep -q "NEXT_PUBLIC_API_URL=" "$FRONTEND_ENV"; then
            sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$API_GATEWAY_URL|" "$FRONTEND_ENV"
        else
            echo "NEXT_PUBLIC_API_URL=$API_GATEWAY_URL" >> "$FRONTEND_ENV"
        fi
        
        # モックモードを無効化
        if grep -q "NEXT_PUBLIC_USE_MOCK_API=" "$FRONTEND_ENV"; then
            sed -i.bak "s/NEXT_PUBLIC_USE_MOCK_API=.*/NEXT_PUBLIC_USE_MOCK_API=false/" "$FRONTEND_ENV"
        else
            echo "NEXT_PUBLIC_USE_MOCK_API=false" >> "$FRONTEND_ENV"
        fi
        
        log_success "フロントエンド環境変数を更新: $FRONTEND_ENV"
    fi
else
    log_error "API Gateway URLの取得に失敗しました"
fi

# 7. 動作確認テスト
log_info "AWS API動作確認テスト実行中..."

if [ -n "$API_GATEWAY_URL" ]; then
    # ヘルスチェック（存在する場合）
    if curl -s -f "${API_GATEWAY_URL}/health" > /dev/null 2>&1; then
        log_success "API ヘルスチェック成功"
    else
        log_warning "API ヘルスチェックエンドポイントが見つかりません（正常）"
    fi
    
    # 認証テスト（署名付きURL生成）
    log_info "認証テストを実行中..."
    TEST_RESPONSE=$(curl -s -X POST "${API_GATEWAY_URL}/presigned-urls" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer dummy-token-for-test" \
        -d '{"fileName": "test.xlsx", "fileSize": 1024, "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}' \
        || echo "")
    
    if [[ "$TEST_RESPONSE" == *"error"* ]] || [[ "$TEST_RESPONSE" == *"Unauthorized"* ]]; then
        log_success "認証エラー確認（期待通り）"
    else
        log_warning "認証テストの結果が予期しないものです"
    fi
fi

# 8. 結果表示
echo ""
log_success "🎉 AWSデプロイ完了！"
echo "=================================="
echo ""
echo "☁️  デプロイされたリソース:"
echo "  CloudFormationスタック: $STACK_NAME"
if [ -n "$API_GATEWAY_URL" ]; then
    echo "  API Gateway URL: $API_GATEWAY_URL"
fi
echo "  S3バケット: excel-unlocker-bucket-development-${AWS_ACCOUNT_ID}-${AWS_REGION}"
echo ""
echo "🔍 次のステップ:"
echo "  1. Vercelの環境変数にAPI URLを設定"
echo "  2. Vercelを再デプロイ"
echo "  3. フロントエンド・バックエンド連携テスト"
echo ""
echo "⚙️  AWS設定確認:"
echo "  aws cloudformation describe-stacks --stack-name $STACK_NAME"
echo "  aws s3 ls | grep excel-unlocker"
echo ""

log_info "AWS単体デプロイが完了しました"