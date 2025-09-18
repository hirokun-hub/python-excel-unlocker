#!/bin/bash

# GitHub OIDC化セットアップスクリプト
# 長期AWSキーを廃止してOIDC認証に移行

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 必要なツールの確認
check_prerequisites() {
    log_info "前提条件の確認中..."
    
    # AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLIがインストールされていません"
        exit 1
    fi
    
    # GitHub CLI
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLIがインストールされていません"
        log_info "インストール方法: https://cli.github.com/"
        exit 1
    fi
    
    # SAM CLI
    if ! command -v sam &> /dev/null; then
        log_error "AWS SAM CLIがインストールされていません"
        exit 1
    fi
    
    # jq
    if ! command -v jq &> /dev/null; then
        log_error "jqがインストールされていません"
        exit 1
    fi
    
    log_success "前提条件の確認完了"
}

# AWS認証の確認
check_aws_auth() {
    log_info "AWS認証の確認中..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証が設定されていません"
        log_info "aws configure を実行してください"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    log_success "AWS認証確認完了 (Account: $ACCOUNT_ID)"
}

# GitHub認証の確認
check_github_auth() {
    log_info "GitHub認証の確認中..."
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub認証が設定されていません"
        log_info "gh auth login を実行してください"
        exit 1
    fi
    
    REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
    log_success "GitHub認証確認完了 (Repository: $REPO)"
}

# 環境の選択
select_environment() {
    echo
    log_info "デプロイ環境を選択してください:"
    echo "1) development"
    echo "2) staging"
    echo "3) production"
    echo
    read -p "選択 (1-3): " choice
    
    case $choice in
        1) ENVIRONMENT="development" ;;
        2) ENVIRONMENT="staging" ;;
        3) ENVIRONMENT="production" ;;
        *) 
            log_error "無効な選択です"
            exit 1
            ;;
    esac
    
    log_info "選択された環境: $ENVIRONMENT"
}

# SAMテンプレートのデプロイ
deploy_sam_template() {
    log_info "SAMテンプレートをデプロイ中..."
    
    # ビルド
    log_info "SAMアプリケーションをビルド中..."
    sam build
    
    # デプロイ
    log_info "$ENVIRONMENT 環境にデプロイ中..."
    sam deploy --config-env $ENVIRONMENT --no-confirm-changeset --no-fail-on-empty-changeset
    
    log_success "SAMテンプレートのデプロイ完了"
}

# GitHub Actions用ロールARNの取得
get_role_arn() {
    log_info "GitHub Actions用ロールARNを取得中..."
    
    STACK_NAME="excel-unlocker-api-$ENVIRONMENT"
    ROLE_ARN=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`GitHubActionsRoleArn`].OutputValue' \
        --output text)
    
    if [ -z "$ROLE_ARN" ]; then
        log_error "ロールARNの取得に失敗しました"
        exit 1
    fi
    
    log_success "ロールARN取得完了: $ROLE_ARN"
}

# GitHub Secretsの設定
setup_github_secrets() {
    log_info "GitHub Secretsを設定中..."
    
    # 新しいSecretを設定
    echo "$ROLE_ARN" | gh secret set AWS_GITHUB_ACTIONS_ROLE_ARN
    log_success "AWS_GITHUB_ACTIONS_ROLE_ARN を設定しました"
    
    # 古いSecretsの削除確認
    echo
    log_warning "古いAWSキーSecretsを削除しますか？"
    log_warning "これにより、長期キーベースの認証は使用できなくなります。"
    read -p "削除しますか？ (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        # 古いSecretsを削除
        if gh secret list | grep -q "AWS_ACCESS_KEY_ID"; then
            gh secret delete AWS_ACCESS_KEY_ID
            log_success "AWS_ACCESS_KEY_ID を削除しました"
        fi
        
        if gh secret list | grep -q "AWS_SECRET_ACCESS_KEY"; then
            gh secret delete AWS_SECRET_ACCESS_KEY
            log_success "AWS_SECRET_ACCESS_KEY を削除しました"
        fi
    else
        log_info "古いSecretsは保持されます（手動で削除してください）"
    fi
}

# OIDC認証のテスト
test_oidc_auth() {
    log_info "OIDC認証をテスト中..."
    
    # テスト用ワークフローの実行
    log_info "テストワークフローを実行します..."
    
    # ワークフローの実行
    gh workflow run deploy-backend.yml --ref $(git branch --show-current)
    
    # 実行結果の確認
    sleep 10
    RUN_ID=$(gh run list --workflow=deploy-backend.yml --limit=1 --json databaseId --jq '.[0].databaseId')
    
    log_info "ワークフロー実行ID: $RUN_ID"
    log_info "実行状況を確認してください: gh run view $RUN_ID"
    
    echo
    log_info "ワークフローの完了を待機中..."
    gh run watch $RUN_ID
    
    # 結果の確認
    STATUS=$(gh run view $RUN_ID --json conclusion --jq .conclusion)
    
    if [ "$STATUS" = "success" ]; then
        log_success "OIDC認証テスト成功！"
    else
        log_error "OIDC認証テスト失敗 (Status: $STATUS)"
        log_info "ログを確認してください: gh run view $RUN_ID --log"
        exit 1
    fi
}

# セットアップサマリーの表示
show_summary() {
    echo
    echo "=================================="
    log_success "GitHub OIDC化セットアップ完了！"
    echo "=================================="
    echo
    echo "📋 設定サマリー:"
    echo "  - 環境: $ENVIRONMENT"
    echo "  - AWSアカウント: $ACCOUNT_ID"
    echo "  - リポジトリ: $REPO"
    echo "  - ロールARN: $ROLE_ARN"
    echo
    echo "🔧 次のステップ:"
    echo "  1. 他の環境でも同様にセットアップを実行"
    echo "  2. 古いAWSキーSecretsを削除（まだの場合）"
    echo "  3. ワークフローの動作確認"
    echo
    echo "📚 参考ドキュメント:"
    echo "  - docs/github-oidc-migration.md"
    echo "  - https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect"
    echo
}

# メイン処理
main() {
    echo "🚀 GitHub OIDC化セットアップスクリプト"
    echo "========================================"
    echo
    
    check_prerequisites
    check_aws_auth
    check_github_auth
    select_environment
    
    echo
    log_info "セットアップを開始します..."
    read -p "続行しますか？ (y/N): " confirm
    
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "セットアップをキャンセルしました"
        exit 0
    fi
    
    deploy_sam_template
    get_role_arn
    setup_github_secrets
    test_oidc_auth
    show_summary
}

# スクリプト実行
main "$@"