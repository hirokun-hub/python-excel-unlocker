#!/bin/bash

# Excel Unlocker 初回デプロイセットアップスクリプト
# 使用方法: ./scripts/setup-deployment.sh

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_info "Excel Unlocker 初回デプロイセットアップを開始します"

# 1. 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLIがインストールされていません"
        log_info "インストール方法: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # AWS SAM CLI
    if ! command -v sam &> /dev/null; then
        log_error "AWS SAM CLIがインストールされていません"
        log_info "インストール方法: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
        exit 1
    fi
    
    # Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.jsがインストールされていません"
        log_info "インストール方法: https://nodejs.org/"
        exit 1
    fi
    
    # Git
    if ! command -v git &> /dev/null; then
        log_error "Gitがインストールされていません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# 2. AWS認証確認
check_aws_auth() {
    log_info "AWS認証を確認中..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証が設定されていません"
        log_info "以下のコマンドで設定してください:"
        log_info "  aws configure"
        log_info "または環境変数を設定してください:"
        log_info "  export AWS_ACCESS_KEY_ID=your-access-key"
        log_info "  export AWS_SECRET_ACCESS_KEY=your-secret-key"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region || echo "ap-northeast-1")
    
    log_success "AWS認証確認完了"
    log_info "アカウントID: $ACCOUNT_ID"
    log_info "リージョン: $REGION"
}

# 3. 環境変数ファイル作成
setup_env_files() {
    log_info "環境変数ファイルを設定中..."
    
    # バックエンド環境変数
    if [[ ! -f "backend/.env.local" ]]; then
        log_info "backend/.env.local を作成中..."
        cp backend/.env.example backend/.env.local
        
        # S3バケット名を動的に設定
        BUCKET_NAME="excel-unlocker-bucket-development-$ACCOUNT_ID-$REGION"
        sed -i.bak "s/S3_BUCKET_NAME=.*/S3_BUCKET_NAME=$BUCKET_NAME/" backend/.env.local
        rm backend/.env.local.bak 2>/dev/null || true
        
        log_success "backend/.env.local を作成しました"
        log_warning "必要に応じて ALLOWED_USERS を編集してください"
    else
        log_info "backend/.env.local は既に存在します"
    fi
    
    # フロントエンド環境変数
    if [[ ! -f "frontend/.env.local" ]]; then
        log_info "frontend/.env.local を作成中..."
        cp frontend/.env.example frontend/.env.local
        
        log_success "frontend/.env.local を作成しました"
        log_warning "Google OAuth設定を編集してください:"
        log_warning "  - GOOGLE_CLIENT_ID"
        log_warning "  - GOOGLE_CLIENT_SECRET"
        log_warning "  - NEXTAUTH_SECRET"
    else
        log_info "frontend/.env.local は既に存在します"
    fi
}

# 4. 依存関係インストール
install_dependencies() {
    log_info "依存関係をインストール中..."
    
    # バックエンド依存関係
    log_info "バックエンド依存関係インストール中..."
    cd backend
    pip install -r src/requirements.txt
    pip install pytest pytest-cov moto  # テスト用
    cd ..
    
    # フロントエンド依存関係
    log_info "フロントエンド依存関係インストール中..."
    cd frontend
    npm ci
    cd ..
    
    log_success "依存関係インストール完了"
}

# 5. 初回テスト実行
run_initial_tests() {
    log_info "初回テスト実行中..."
    
    # バックエンドテスト
    log_info "バックエンドテスト実行中..."
    cd backend
    if pytest tests/unit/ --cov=src --cov-report=term-missing; then
        log_success "バックエンドテスト成功"
    else
        log_warning "バックエンドテストで問題が発生しました"
    fi
    cd ..
    
    # フロントエンドテスト
    log_info "フロントエンドテスト実行中..."
    cd frontend
    if npm run test -- --watchAll=false; then
        log_success "フロントエンドテスト成功"
    else
        log_warning "フロントエンドテストで問題が発生しました"
    fi
    cd ..
}

# 6. 初回デプロイ実行
initial_deploy() {
    log_info "開発環境への初回デプロイを実行中..."
    
    # SAMガイド付きデプロイ
    log_info "AWS SAM ガイド付きデプロイを実行します"
    log_warning "以下の設定を推奨します:"
    log_warning "  - Stack Name: excel-unlocker-api-dev"
    log_warning "  - AWS Region: ap-northeast-1"
    log_warning "  - Confirm changes before deploy: Y"
    log_warning "  - Allow SAM CLI IAM role creation: Y"
    log_warning "  - Save parameters to samconfig.toml: Y"
    
    read -p "初回デプロイを実行しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sam build
        sam deploy --guided
        
        if [[ $? -eq 0 ]]; then
            log_success "初回デプロイ成功！"
            
            # API URL取得
            STACK_NAME="excel-unlocker-api-dev"
            API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text 2>/dev/null || echo "取得失敗")
            
            log_info "API URL: $API_URL"
            
            # フロントエンド環境変数更新
            if [[ "$API_URL" != "取得失敗" ]]; then
                sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$API_URL|" frontend/.env.local
                rm frontend/.env.local.bak 2>/dev/null || true
                log_success "フロントエンド環境変数を更新しました"
            fi
        else
            log_error "初回デプロイが失敗しました"
            exit 1
        fi
    else
        log_info "初回デプロイをスキップしました"
        log_info "後で以下のコマンドで実行できます:"
        log_info "  sam build && sam deploy --guided"
    fi
}

# 7. GitHub Actions設定案内
setup_github_actions() {
    log_info "GitHub Actions設定案内"
    
    log_warning "GitHub Actionsを使用するには、以下のシークレットを設定してください:"
    echo
    echo "AWS関連:"
    echo "  - AWS_ACCESS_KEY_ID: $(aws configure get aws_access_key_id || echo '設定してください')"
    echo "  - AWS_SECRET_ACCESS_KEY: [シークレット]"
    echo
    echo "Vercel関連（フロントエンドデプロイ用）:"
    echo "  - VERCEL_TOKEN: [Vercelアクセストークン]"
    echo "  - VERCEL_ORG_ID: [Vercel組織ID]"
    echo "  - VERCEL_PROJECT_ID: [VercelプロジェクトID]"
    echo
    echo "環境変数:"
    echo "  - NEXTAUTH_SECRET: [NextAuth.jsシークレット]"
    echo "  - GOOGLE_CLIENT_ID: [Google OAuth クライアントID]"
    echo "  - GOOGLE_CLIENT_SECRET: [Google OAuth クライアントシークレット]"
    echo
    log_info "設定方法: GitHubリポジトリ > Settings > Secrets and variables > Actions"
}

# 8. 次のステップ案内
show_next_steps() {
    log_success "初回セットアップ完了！"
    echo
    log_info "次のステップ:"
    echo "1. 環境変数の確認・編集:"
    echo "   - backend/.env.local"
    echo "   - frontend/.env.local"
    echo
    echo "2. Google OAuth設定:"
    echo "   - Google Cloud Console でOAuth 2.0クライアントを作成"
    echo "   - クライアントIDとシークレットを frontend/.env.local に設定"
    echo
    echo "3. ローカル開発サーバー起動:"
    echo "   - バックエンド: sam local start-api --port 3001"
    echo "   - フロントエンド: cd frontend && npm run dev"
    echo
    echo "4. 段階的デプロイ:"
    echo "   - 開発環境: ./scripts/deploy.sh development all"
    echo "   - ステージング: ./scripts/deploy.sh staging all"
    echo "   - 本番環境: ./scripts/deploy.sh production all"
    echo
    echo "5. GitHub Actions設定:"
    echo "   - 上記のシークレットをGitHubリポジトリに設定"
    echo
    log_info "詳細は docs/deployment-guide.md を参照してください"
}

# メイン実行
main() {
    check_prerequisites
    check_aws_auth
    setup_env_files
    install_dependencies
    run_initial_tests
    initial_deploy
    setup_github_actions
    show_next_steps
}

# スクリプト実行
main