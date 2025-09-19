#!/bin/bash

# Excel Unlocker 設定管理システム統合セットアップ
# 設定ファイルベースの自動化デプロイメント

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_manual() {
    echo -e "${PURPLE}[手作業必要]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# スクリプトディレクトリの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_MANAGER="$SCRIPT_DIR/setup-config-manager.sh"

# バナー表示
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        Excel Unlocker 設定管理システム統合セットアップ      ║"
    echo "║                                                              ║"
    echo "║  設定ファイルベースの自動化デプロイメント環境構築            ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 前提条件のチェック
check_prerequisites() {
    log_step "前提条件をチェックしています..."
    
    local missing_tools=()
    
    # 必要なツールのチェック
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
    fi
    
    if ! command -v sam &> /dev/null; then
        missing_tools+=("sam-cli")
    fi
    
    if ! command -v node &> /dev/null; then
        missing_tools+=("node.js")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "以下のツールがインストールされていません:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        log_manual "必要なツールをインストールしてから再実行してください"
        exit 1
    fi
    
    log_success "前提条件のチェックが完了しました"
}

# 設定ファイルの初期化
initialize_config() {
    log_step "設定ファイルを初期化しています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "setup-config.json" ]]; then
        log_info "設定ファイルのテンプレートを作成しています..."
        "$CONFIG_MANAGER" init
        
        log_manual "setup-config.json を編集して以下の情報を設定してください:"
        echo "  1. Google OAuth クライアントIDとシークレット"
        echo "  2. AWS S3バケット名（環境別）"
        echo "  3. 許可ユーザーのメールアドレス"
        echo "  4. JWT/セッションシークレット"
        echo ""
        echo "設定完了後、Enterキーを押してください..."
        read -r
    else
        log_info "既存の設定ファイルを使用します"
    fi
    
    # 設定ファイルの検証
    log_info "設定ファイルを検証しています..."
    if "$CONFIG_MANAGER" validate; then
        log_success "設定ファイルの検証が完了しました"
    else
        log_error "設定ファイルに問題があります。修正してから再実行してください。"
        exit 1
    fi
}

# 環境別セットアップ
setup_environment() {
    local environment="$1"
    
    log_step "${environment}環境のセットアップを開始します..."
    
    # 環境変数の生成
    log_info "環境変数を生成しています..."
    "$CONFIG_MANAGER" generate-env "$environment" dotenv ".env.${environment}"
    
    # 環境変数の読み込み
    if [[ -f ".env.${environment}" ]]; then
        set -a
        source ".env.${environment}"
        set +a
        log_success "環境変数を読み込みました"
    else
        log_error "環境変数ファイルの生成に失敗しました"
        exit 1
    fi
    
    # AWS設定の確認
    log_info "AWS設定を確認しています..."
    if [[ -n "${AWS_PROFILE:-}" ]]; then
        export AWS_PROFILE="$AWS_PROFILE"
        log_info "AWS Profile: $AWS_PROFILE を使用します"
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証に失敗しました。aws configure を実行してください。"
        exit 1
    fi
    
    log_success "AWS設定の確認が完了しました"
}

# S3バケットの作成
create_s3_bucket() {
    local bucket_name="$1"
    local region="${AWS_REGION:-ap-northeast-1}"
    
    log_info "S3バケット '$bucket_name' を作成しています..."
    
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "S3バケット '$bucket_name' は既に存在します"
    else
        if aws s3 mb "s3://$bucket_name" --region "$region"; then
            log_success "S3バケット '$bucket_name' を作成しました"
        else
            log_error "S3バケットの作成に失敗しました"
            exit 1
        fi
    fi
    
    # パブリックアクセスブロックの設定
    log_info "S3バケットのセキュリティ設定を適用しています..."
    aws s3api put-public-access-block \
        --bucket "$bucket_name" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    log_success "S3バケットのセキュリティ設定が完了しました"
}

# バックエンドのデプロイ
deploy_backend() {
    local environment="$1"
    
    log_step "バックエンド（${environment}）をデプロイしています..."
    
    cd "$PROJECT_ROOT"
    
    # SAMビルド
    log_info "SAMアプリケーションをビルドしています..."
    if sam build; then
        log_success "SAMビルドが完了しました"
    else
        log_error "SAMビルドに失敗しました"
        exit 1
    fi
    
    # SAMデプロイ
    log_info "SAMアプリケーションをデプロイしています..."
    if sam deploy \
        --stack-name "$LAMBDA_STACK_NAME" \
        --s3-bucket "$S3_BUCKET_NAME" \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment="$environment" \
            S3BucketName="$S3_BUCKET_NAME" \
            AllowedUsers="$ALLOWED_USERS" \
            CorsOrigin="$CORS_ORIGIN" \
        --no-confirm-changeset; then
        log_success "バックエンドのデプロイが完了しました"
    else
        log_error "バックエンドのデプロイに失敗しました"
        exit 1
    fi
    
    # API Gateway URLの取得
    local api_url
    api_url=$(aws cloudformation describe-stacks \
        --stack-name "$LAMBDA_STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text)
    
    if [[ -n "$api_url" ]]; then
        log_success "API Gateway URL: $api_url"
        echo "NEXT_PUBLIC_API_URL=$api_url" >> ".env.${environment}"
    else
        log_warning "API Gateway URLの取得に失敗しました"
    fi
}

# フロントエンドのセットアップ
setup_frontend() {
    local environment="$1"
    
    log_step "フロントエンド（${environment}）をセットアップしています..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # 依存関係のインストール
    log_info "フロントエンドの依存関係をインストールしています..."
    if npm install; then
        log_success "依存関係のインストールが完了しました"
    else
        log_error "依存関係のインストールに失敗しました"
        exit 1
    fi
    
    # 環境変数ファイルのコピー
    log_info "フロントエンド用環境変数を設定しています..."
    cp "../.env.${environment}" ".env.local"
    
    # ビルドテスト
    log_info "フロントエンドのビルドテストを実行しています..."
    if npm run build; then
        log_success "フロントエンドのビルドテストが完了しました"
    else
        log_error "フロントエンドのビルドに失敗しました"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
}

# Vercelデプロイ（オプション）
deploy_vercel() {
    local environment="$1"
    
    log_step "Vercel（${environment}）へのデプロイを準備しています..."
    
    if command -v vercel &> /dev/null; then
        log_info "Vercelデプロイを実行しています..."
        
        cd "$PROJECT_ROOT/frontend"
        
        # 環境変数の設定
        log_info "Vercel環境変数を設定しています..."
        while IFS='=' read -r key value; do
            if [[ -n "$key" && ! "$key" =~ ^# ]]; then
                vercel env add "$key" "$environment" <<< "$value" || true
            fi
        done < ".env.local"
        
        # デプロイ実行
        if [[ "$environment" == "production" ]]; then
            vercel --prod
        else
            vercel
        fi
        
        log_success "Vercelデプロイが完了しました"
        cd "$PROJECT_ROOT"
    else
        log_manual "Vercel CLIがインストールされていません"
        log_manual "手動でVercelにデプロイするか、Vercel CLIをインストールしてください"
    fi
}

# 設定のバックアップ
backup_configuration() {
    log_step "設定をバックアップしています..."
    
    cd "$PROJECT_ROOT"
    
    # 設定ファイルのバックアップ
    "$CONFIG_MANAGER" backup
    
    # 環境変数ファイルのバックアップ
    local backup_dir="config-backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    for env_file in .env.*; do
        if [[ -f "$env_file" ]]; then
            cp "$env_file" "$backup_dir/"
        fi
    done
    
    log_success "設定のバックアップが完了しました: $backup_dir"
}

# デプロイ後の動作確認
verify_deployment() {
    local environment="$1"
    
    log_step "デプロイメントの動作確認を実行しています..."
    
    # API Gateway URLの取得
    local api_url
    api_url=$(grep "NEXT_PUBLIC_API_URL" ".env.${environment}" | cut -d'=' -f2)
    
    if [[ -n "$api_url" ]]; then
        log_info "API エンドポイントをテストしています..."
        
        # ヘルスチェック（簡易）
        if curl -s "${api_url}/health" &> /dev/null; then
            log_success "API エンドポイントが正常に応答しています"
        else
            log_warning "API エンドポイントの応答確認に失敗しました"
        fi
    fi
    
    # フロントエンドのビルド確認
    cd "$PROJECT_ROOT/frontend"
    if [[ -d ".next" ]]; then
        log_success "フロントエンドのビルドが正常に完了しています"
    else
        log_warning "フロントエンドのビルドディレクトリが見つかりません"
    fi
    
    cd "$PROJECT_ROOT"
}

# メイン処理
main() {
    local environment="${1:-development}"
    local deploy_vercel="${2:-false}"
    
    show_banner
    
    log_info "環境: $environment でセットアップを開始します"
    
    # 前提条件のチェック
    check_prerequisites
    
    # 設定ファイルの初期化
    initialize_config
    
    # 環境別セットアップ
    setup_environment "$environment"
    
    # S3バケットの作成
    create_s3_bucket "$S3_BUCKET_NAME"
    
    # バックエンドのデプロイ
    deploy_backend "$environment"
    
    # フロントエンドのセットアップ
    setup_frontend "$environment"
    
    # Vercelデプロイ（オプション）
    if [[ "$deploy_vercel" == "true" ]]; then
        deploy_vercel "$environment"
    fi
    
    # 設定のバックアップ
    backup_configuration
    
    # デプロイメントの動作確認
    verify_deployment "$environment"
    
    # 完了メッセージ
    echo ""
    log_success "🎉 ${environment}環境のセットアップが完了しました！"
    echo ""
    echo "次のステップ:"
    echo "1. フロントエンドをローカルで確認: cd frontend && npm run dev"
    echo "2. バックエンドAPIをテスト: curl \${API_URL}/health"
    if [[ "$deploy_vercel" != "true" ]]; then
        echo "3. Vercelにデプロイ: $0 $environment true"
    fi
    echo ""
    echo "設定ファイル: setup-config.json"
    echo "環境変数: .env.${environment}"
    echo "バックアップ: config-backup/"
    echo ""
}

# 使用方法の表示
show_usage() {
    cat << EOF
設定管理システム統合セットアップ

使用方法:
  $0 [environment] [deploy_vercel]

引数:
  environment     対象環境 (development|staging|production) [デフォルト: development]
  deploy_vercel   Vercelデプロイの実行 (true|false) [デフォルト: false]

例:
  $0                          # 開発環境のセットアップ
  $0 staging                  # ステージング環境のセットアップ
  $0 production true          # 本番環境のセットアップ + Vercelデプロイ

前提条件:
  - Python 3.x
  - AWS CLI (設定済み)
  - SAM CLI
  - Node.js & npm
  - Git

EOF
}

# コマンドライン引数の処理
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    show_usage
    exit 0
fi

# メイン処理の実行
main "$@"