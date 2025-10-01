#!/bin/bash

# GitHub OIDC プロバイダーを手動作成するスクリプト
# CloudFormationでの自動作成を避けるため、事前に手動作成する

set -euo pipefail

# 色付きログ関数
log_info() {
    echo -e "\033[36m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

log_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# AWS CLI の確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    exit 1
fi

# AWS認証の確認
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS認証が設定されていません。aws configure を実行してください"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_info "AWS Account ID: $ACCOUNT_ID"

# OIDCプロバイダーの存在確認
OIDC_URL="https://token.actions.githubusercontent.com"
EXISTING_PROVIDER=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_PROVIDER" ]; then
    log_warning "GitHub OIDC プロバイダーは既に存在します: $EXISTING_PROVIDER"
    echo ""
    echo "既存のプロバイダー情報:"
    aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$EXISTING_PROVIDER" || true
    echo ""
    log_info "既存のプロバイダーを使用します"
    exit 0
fi

log_info "GitHub OIDC プロバイダーを作成します..."

# OIDCプロバイダーの作成
aws iam create-open-id-connect-provider \
    --url "$OIDC_URL" \
    --client-id-list "sts.amazonaws.com" \
    --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" "1c58a3a8518e8759bf075b76b750d4f2df264fcd" \
    --tags Key=Name,Value=GitHubOIDC Key=Purpose,Value=GitHubActions Key=CreatedBy,Value=ManualScript

PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

log_success "GitHub OIDC プロバイダーを作成しました: $PROVIDER_ARN"

# 作成されたプロバイダーの確認
echo ""
log_info "作成されたプロバイダーの詳細:"
aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVIDER_ARN"

echo ""
log_success "✅ GitHub OIDC プロバイダーの作成が完了しました"
echo ""
echo "📋 次のステップ:"
echo "1. CloudFormationテンプレートでこのプロバイダーを参照します"
echo "2. GitHub ActionsでOIDC認証を使用できるようになります"
echo ""
echo "🔗 プロバイダーARN: $PROVIDER_ARN"