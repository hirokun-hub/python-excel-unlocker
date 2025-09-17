#!/bin/bash

# Excel Unlocker 段階的デプロイメントスクリプト
# 使用方法: ./scripts/deploy.sh [environment] [component]
# 例: ./scripts/deploy.sh development backend
#     ./scripts/deploy.sh staging all
#     ./scripts/deploy.sh production frontend

set -e  # エラー時に停止

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

# 引数チェック
ENVIRONMENT=${1:-development}
COMPONENT=${2:-all}

if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "無効な環境です: $ENVIRONMENT"
    log_info "使用可能な環境: development, staging, production"
    exit 1
fi

if [[ ! "$COMPONENT" =~ ^(backend|frontend|all)$ ]]; then
    log_error "無効なコンポーネントです: $COMPONENT"
    log_info "使用可能なコンポーネント: backend, frontend, all"
    exit 1
fi

log_info "段階的デプロイメント開始"
log_info "環境: $ENVIRONMENT"
log_info "コンポーネント: $COMPONENT"

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # AWS CLI確認
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLIがインストールされていません"
        exit 1
    fi
    
    # AWS認証確認
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証が設定されていません"
        log_info "aws configure を実行してください"
        exit 1
    fi
    
    # SAM CLI確認（バックエンドデプロイ時）
    if [[ "$COMPONENT" == "backend" || "$COMPONENT" == "all" ]]; then
        if ! command -v sam &> /dev/null; then
            log_error "AWS SAM CLIがインストールされていません"
            exit 1
        fi
    fi
    
    # Vercel CLI確認（フロントエンドデプロイ時）
    if [[ "$COMPONENT" == "frontend" || "$COMPONENT" == "all" ]]; then
        if ! command -v vercel &> /dev/null; then
            log_warning "Vercel CLIがインストールされていません"
            log_info "npm install -g vercel を実行してください"
        fi
    fi
    
    log_success "前提条件チェック完了"
}

# バックエンドデプロイ
deploy_backend() {
    log_info "バックエンドデプロイ開始 (環境: $ENVIRONMENT)"
    
    # テスト実行
    log_info "バックエンドテスト実行中..."
    cd backend
    if ! pytest tests/unit/ --cov=src --cov-report=term-missing; then
        log_error "バックエンドテストが失敗しました"
        exit 1
    fi
    cd ..
    
    # SAMビルド
    log_info "SAMアプリケーションビルド中..."
    if ! sam build; then
        log_error "SAMビルドが失敗しました"
        exit 1
    fi
    
    # 環境別デプロイ
    case $ENVIRONMENT in
        "development")
            log_info "開発環境にデプロイ中..."
            sam deploy --config-env default --no-confirm-changeset --no-fail-on-empty-changeset
            ;;
        "staging")
            log_info "ステージング環境にデプロイ中..."
            sam deploy --config-env staging --no-confirm-changeset --no-fail-on-empty-changeset
            ;;
        "production")
            log_warning "本番環境へのデプロイには確認が必要です"
            read -p "本番環境にデプロイしますか？ (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "本番環境にデプロイ中..."
                sam deploy --config-env production --confirm-changeset
            else
                log_info "本番デプロイをキャンセルしました"
                return 0
            fi
            ;;
    esac
    
    # デプロイ結果取得
    STACK_NAME="excel-unlocker-api-$ENVIRONMENT"
    API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text 2>/dev/null || echo "取得失敗")
    
    log_success "バックエンドデプロイ完了"
    log_info "API URL: $API_URL"
}

# フロントエンドデプロイ
deploy_frontend() {
    log_info "フロントエンドデプロイ開始 (環境: $ENVIRONMENT)"
    
    cd frontend
    
    # 依存関係インストール
    log_info "依存関係インストール中..."
    npm ci
    
    # テスト実行
    log_info "フロントエンドテスト実行中..."
    if ! npm run test -- --watchAll=false; then
        log_error "フロントエンドテストが失敗しました"
        exit 1
    fi
    
    # 型チェック
    log_info "TypeScript型チェック中..."
    if ! npm run type-check; then
        log_error "TypeScript型チェックが失敗しました"
        exit 1
    fi
    
    # リント
    log_info "ESLintチェック中..."
    if ! npm run lint; then
        log_error "ESLintチェックが失敗しました"
        exit 1
    fi
    
    # ビルド
    log_info "アプリケーションビルド中..."
    if ! npm run build; then
        log_error "ビルドが失敗しました"
        exit 1
    fi
    
    log_success "フロントエンドデプロイ準備完了"
    log_warning "Vercelへの実際のデプロイはGitHub Actionsまたは手動で実行してください"
    
    cd ..
}

# 統合テスト実行
run_integration_tests() {
    log_info "統合テスト実行中..."
    
    if [[ -f "./tests/run-integration-tests.sh" ]]; then
        ./tests/run-integration-tests.sh api
        log_success "統合テスト完了"
    else
        log_warning "統合テストスクリプトが見つかりません"
    fi
}

# デプロイ後の疎通確認
verify_deployment() {
    log_info "デプロイ後疎通確認中..."
    
    STACK_NAME="excel-unlocker-api-$ENVIRONMENT"
    API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text 2>/dev/null || echo "")
    
    if [[ -n "$API_URL" ]]; then
        log_info "API疎通確認: $API_URL"
        
        # ヘルスチェック
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/presigned-urls" -X POST -H "Content-Type: application/json" -d '{}' || echo "000")
        
        if [[ "$HTTP_STATUS" =~ ^[45][0-9][0-9]$ ]]; then
            log_success "API Gateway疎通確認成功 (Status: $HTTP_STATUS)"
        else
            log_warning "API Gateway疎通確認で予期しないステータス: $HTTP_STATUS"
        fi
    else
        log_warning "API URLを取得できませんでした"
    fi
}

# メイン実行
main() {
    check_prerequisites
    
    case $COMPONENT in
        "backend")
            deploy_backend
            verify_deployment
            ;;
        "frontend")
            deploy_frontend
            ;;
        "all")
            deploy_backend
            deploy_frontend
            verify_deployment
            run_integration_tests
            ;;
    esac
    
    log_success "段階的デプロイメント完了！"
    log_info "環境: $ENVIRONMENT"
    log_info "コンポーネント: $COMPONENT"
    
    # 環境別の次のステップ案内
    case $ENVIRONMENT in
        "development")
            log_info "次のステップ: ステージング環境へのデプロイ"
            log_info "コマンド: ./scripts/deploy.sh staging all"
            ;;
        "staging")
            log_info "次のステップ: 本番環境へのデプロイ"
            log_info "コマンド: ./scripts/deploy.sh production all"
            ;;
        "production")
            log_success "本番環境デプロイ完了！運用開始可能です。"
            ;;
    esac
}

# スクリプト実行
main