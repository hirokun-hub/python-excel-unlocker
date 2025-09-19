#!/bin/bash

# Excel Unlocker 社内展開用統合セットアップスクリプト
# 初心者向けの対話式セットアップ、進捗表示、エラー時サポート機能付き

set -e

# 色付きログ出力とアイコン
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# アイコン定義
ICON_SUCCESS="✅"
ICON_ERROR="❌"
ICON_WARNING="⚠️"
ICON_INFO="📍"
ICON_MANUAL="🔧"
ICON_STEP="🚀"
ICON_PROGRESS="⏳"
ICON_QUESTION="❓"
ICON_LIGHTBULB="💡"
ICON_ROCKET="🚀"
ICON_PARTY="🎉"

# ログ関数
log_info() {
    echo -e "${BLUE}${ICON_INFO}${NC} $1"
}

log_success() {
    echo -e "${GREEN}${ICON_SUCCESS}${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}${ICON_WARNING}${NC} $1"
}

log_error() {
    echo -e "${RED}${ICON_ERROR}${NC} $1"
}

log_manual() {
    echo -e "${PURPLE}${ICON_MANUAL}${NC} $1"
}

log_step() {
    echo -e "${CYAN}${ICON_STEP}${NC} $1"
}

log_progress() {
    echo -e "${YELLOW}${ICON_PROGRESS}${NC} $1"
}

log_question() {
    echo -e "${WHITE}${ICON_QUESTION}${NC} $1"
}

log_tip() {
    echo -e "${CYAN}${ICON_LIGHTBULB}${NC} $1"
}

# グローバル変数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_MANAGER="$SCRIPT_DIR/setup-config-manager.sh"
LOG_FILE="$PROJECT_ROOT/setup-integrated-deployment.log"
INTERACTIVE_MODE=true
SKIP_TESTS=false
ENVIRONMENT="development"
DEPLOY_VERCEL=false
SETUP_START_TIME=$(date +%s)

# 設定ファイル
SETUP_CONFIG="$PROJECT_ROOT/setup-config.json"
DEPLOYMENT_CONFIG="$PROJECT_ROOT/.deployment-config.json"

# バナー表示
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                🚀 Excel Unlocker 社内展開用統合セットアップ 🚀                ║
║                                                                              ║
║              初心者向け対話式セットアップ・完全自動化システム                ║
║                                                                              ║
║  📋 機能: 設定管理・進捗表示・エラーサポート・動作確認テスト                  ║
║  🎯 対象: 技術的前提知識のない社内メンバー                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo
}

# 進捗バー表示
show_progress_bar() {
    local current=$1
    local total=$2
    local description="$3"
    local width=50
    
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r${CYAN}[%3d%%]${NC} [" "$percentage"
    printf "%*s" "$filled" | tr ' ' '█'
    printf "%*s" "$empty" | tr ' ' '░'
    printf "] %s" "$description"
    
    if [[ $current -eq $total ]]; then
        echo
        echo
    fi
}

# 対話式質問関数
ask_question() {
    local question="$1"
    local default_value="$2"
    local validation_pattern="$3"
    local help_text="$4"
    
    while true; do
        echo
        log_question "$question"
        if [[ -n "$help_text" ]]; then
            log_tip "$help_text"
        fi
        
        if [[ -n "$default_value" ]]; then
            echo -n "入力してください [デフォルト: $default_value]: "
        else
            echo -n "入力してください: "
        fi
        
        read -r user_input
        
        # デフォルト値の使用
        if [[ -z "$user_input" && -n "$default_value" ]]; then
            user_input="$default_value"
        fi
        
        # バリデーション
        if [[ -n "$validation_pattern" ]]; then
            if [[ $user_input =~ $validation_pattern ]]; then
                echo "$user_input"
                return 0
            else
                log_error "入力形式が正しくありません。再度入力してください。"
                continue
            fi
        else
            echo "$user_input"
            return 0
        fi
    done
}

# 確認質問
ask_confirmation() {
    local question="$1"
    local default="$2"
    
    while true; do
        echo
        log_question "$question"
        if [[ "$default" == "y" ]]; then
            echo -n "(Y/n): "
        else
            echo -n "(y/N): "
        fi
        
        read -r response
        
        if [[ -z "$response" ]]; then
            response="$default"
        fi
        
        case "$response" in
            [Yy]|[Yy][Ee][Ss])
                return 0
                ;;
            [Nn]|[Nn][Oo])
                return 1
                ;;
            *)
                log_error "y (はい) または n (いいえ) で答えてください。"
                ;;
        esac
    done
}

# 前提条件チェック
check_prerequisites() {
    log_step "前提条件をチェックしています..."
    
    local missing_tools=()
    local tool_info=""
    
    # 必要なツールのチェック
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
        tool_info+="\n  - Python 3.x: https://www.python.org/downloads/"
    fi
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
        tool_info+="\n  - AWS CLI: https://aws.amazon.com/cli/"
    fi
    
    if ! command -v sam &> /dev/null; then
        missing_tools+=("sam-cli")
        tool_info+="\n  - SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    fi
    
    if ! command -v node &> /dev/null; then
        missing_tools+=("node.js")
        tool_info+="\n  - Node.js: https://nodejs.org/"
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
        tool_info+="\n  - Git: https://git-scm.com/"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "以下のツールがインストールされていません:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo
        log_manual "インストール方法:"
        echo -e "$tool_info"
        echo
        log_manual "必要なツールをインストールしてから再実行してください。"
        
        if ask_confirmation "インストール方法を確認しましたか？" "n"; then
            log_info "ツールのインストール完了後に再実行してください。"
        fi
        
        exit 1
    fi
    
    log_success "前提条件のチェックが完了しました"
}

# 対話式設定収集
collect_interactive_settings() {
    log_step "対話式設定を開始します..."
    
    echo
    log_info "Excel Unlockerの設定を行います。"
    log_info "分からない項目がある場合は、デフォルト値を使用できます。"
    echo
    
    # 環境選択
    echo "対象環境を選択してください:"
    echo "  1) development (開発環境) - ローカルテスト用"
    echo "  2) staging (ステージング環境) - 本番前テスト用"
    echo "  3) production (本番環境) - 実際の運用環境"
    echo
    
    while true; do
        read -p "選択してください (1-3) [デフォルト: 1]: " env_choice
        case "${env_choice:-1}" in
            1)
                ENVIRONMENT="development"
                break
                ;;
            2)
                ENVIRONMENT="staging"
                break
                ;;
            3)
                ENVIRONMENT="production"
                break
                ;;
            *)
                log_error "1、2、または3を選択してください。"
                ;;
        esac
    done
    
    log_success "環境: $ENVIRONMENT を選択しました"
    
    # Vercelデプロイ確認
    if ask_confirmation "Vercelへのデプロイも実行しますか？" "n"; then
        DEPLOY_VERCEL=true
        log_success "Vercelデプロイを有効にしました"
    fi
    
    # テストスキップ確認
    if ask_confirmation "動作確認テストをスキップしますか？（上級者向け）" "n"; then
        SKIP_TESTS=true
        log_warning "動作確認テストをスキップします"
    fi
    
    echo
    log_success "対話式設定が完了しました"
}

# 設定ファイルの初期化と検証
initialize_and_validate_config() {
    log_step "設定ファイルを初期化・検証しています..."
    
    cd "$PROJECT_ROOT"
    
    # 設定ファイルの存在確認
    if [[ ! -f "$SETUP_CONFIG" ]]; then
        log_info "設定ファイルのテンプレートを作成しています..."
        
        if "$CONFIG_MANAGER" init; then
            log_success "設定ファイルテンプレートを作成しました"
        else
            log_error "設定ファイルテンプレートの作成に失敗しました"
            show_recovery_help "config_template_failed"
            exit 1
        fi
        
        echo
        log_manual "setup-config.json を編集して以下の情報を設定してください:"
        echo
        echo "  🔑 Google OAuth設定:"
        echo "     - clientId: Google Cloud ConsoleのOAuthクライアントID"
        echo "     - clientSecret: Google Cloud ConsoleのOAuthクライアントシークレット"
        echo
        echo "  ☁️  AWS設定:"
        echo "     - s3.bucketName: S3バケット名（環境別）"
        echo "     - region: AWSリージョン（通常は ap-northeast-1）"
        echo
        echo "  👥 セキュリティ設定:"
        echo "     - allowedUsers: 許可するユーザーのメールアドレス"
        echo "     - jwtSecret: JWT用のランダムな文字列"
        echo "     - sessionSecret: セッション用のランダムな文字列"
        echo
        echo "  🌐 Vercel設定:"
        echo "     - projectName: Vercelプロジェクト名"
        echo "     - domain: 本番ドメイン（オプション）"
        echo
        
        log_tip "設定例は docs/beginner-complete-setup-guide.md を参照してください"
        echo
        
        if ask_confirmation "設定ファイルの編集を完了しましたか？" "n"; then
            log_success "設定ファイルの編集が完了しました"
        else
            log_info "設定ファイルの編集完了後に再実行してください"
            exit 0
        fi
    else
        log_info "既存の設定ファイルを使用します"
    fi
    
    # 設定ファイルの検証
    log_progress "設定ファイルを検証しています..."
    
    if "$CONFIG_MANAGER" validate; then
        log_success "設定ファイルの検証が完了しました"
    else
        log_error "設定ファイルに問題があります"
        show_recovery_help "config_validation_failed"
        
        if ask_confirmation "設定ファイルを修正して再試行しますか？" "y"; then
            log_info "設定ファイルを修正してから再実行してください"
            exit 1
        else
            exit 1
        fi
    fi
}

# 環境別セットアップ
setup_environment() {
    log_step "${ENVIRONMENT}環境のセットアップを開始します..."
    
    # 環境変数の生成
    log_progress "環境変数を生成しています..."
    
    if "$CONFIG_MANAGER" generate-env "$ENVIRONMENT" dotenv ".env.${ENVIRONMENT}"; then
        log_success "環境変数を生成しました"
    else
        log_error "環境変数の生成に失敗しました"
        show_recovery_help "env_generation_failed"
        exit 1
    fi
    
    # 環境変数の読み込み
    if [[ -f ".env.${ENVIRONMENT}" ]]; then
        set -a
        source ".env.${ENVIRONMENT}"
        set +a
        log_success "環境変数を読み込みました"
    else
        log_error "環境変数ファイルが見つかりません"
        exit 1
    fi
    
    # AWS設定の確認
    log_progress "AWS設定を確認しています..."
    
    if [[ -n "${AWS_PROFILE:-}" ]]; then
        export AWS_PROFILE="$AWS_PROFILE"
        log_info "AWS Profile: $AWS_PROFILE を使用します"
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証に失敗しました"
        show_recovery_help "aws_auth_failed"
        
        if ask_confirmation "AWS設定を確認して再試行しますか？" "y"; then
            log_manual "以下のコマンドでAWS設定を確認してください:"
            echo "  aws configure list"
            echo "  aws configure"
            exit 1
        else
            exit 1
        fi
    fi
    
    log_success "AWS設定の確認が完了しました"
}

# S3バケットの作成
create_s3_bucket() {
    local bucket_name="$1"
    local region="${AWS_REGION:-ap-northeast-1}"
    
    log_progress "S3バケット '$bucket_name' を作成しています..."
    
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "S3バケット '$bucket_name' は既に存在します"
    else
        if aws s3 mb "s3://$bucket_name" --region "$region"; then
            log_success "S3バケット '$bucket_name' を作成しました"
        else
            log_error "S3バケットの作成に失敗しました"
            show_recovery_help "s3_creation_failed"
            exit 1
        fi
    fi
    
    # パブリックアクセスブロックの設定
    log_progress "S3バケットのセキュリティ設定を適用しています..."
    
    if aws s3api put-public-access-block \
        --bucket "$bucket_name" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"; then
        log_success "S3バケットのセキュリティ設定が完了しました"
    else
        log_warning "S3バケットのセキュリティ設定で問題が発生しました（継続）"
    fi
}

# バックエンドのデプロイ
deploy_backend() {
    log_step "バックエンド（${ENVIRONMENT}）をデプロイしています..."
    
    cd "$PROJECT_ROOT"
    
    # SAMビルド
    log_progress "SAMアプリケーションをビルドしています..."
    
    if sam build; then
        log_success "SAMビルドが完了しました"
    else
        log_error "SAMビルドに失敗しました"
        show_recovery_help "sam_build_failed"
        exit 1
    fi
    
    # SAMデプロイ
    log_progress "SAMアプリケーションをデプロイしています..."
    
    if sam deploy \
        --stack-name "$LAMBDA_STACK_NAME" \
        --s3-bucket "$S3_BUCKET_NAME" \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            S3BucketName="$S3_BUCKET_NAME" \
            AllowedUsers="$ALLOWED_USERS" \
            CorsOrigin="$CORS_ORIGIN" \
        --no-confirm-changeset; then
        log_success "バックエンドのデプロイが完了しました"
    else
        log_error "バックエンドのデプロイに失敗しました"
        show_recovery_help "sam_deploy_failed"
        exit 1
    fi
    
    # API Gateway URLの取得
    log_progress "API Gateway URLを取得しています..."
    
    local api_url
    api_url=$(aws cloudformation describe-stacks \
        --stack-name "$LAMBDA_STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]]; then
        log_success "API Gateway URL: $api_url"
        echo "NEXT_PUBLIC_API_URL=$api_url" >> ".env.${ENVIRONMENT}"
    else
        log_warning "API Gateway URLの取得に失敗しました"
    fi
}

# フロントエンドのセットアップ
setup_frontend() {
    log_step "フロントエンド（${ENVIRONMENT}）をセットアップしています..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # 依存関係のインストール
    log_progress "フロントエンドの依存関係をインストールしています..."
    
    if npm install; then
        log_success "依存関係のインストールが完了しました"
    else
        log_error "依存関係のインストールに失敗しました"
        show_recovery_help "npm_install_failed"
        exit 1
    fi
    
    # 環境変数ファイルのコピー
    log_progress "フロントエンド用環境変数を設定しています..."
    
    cp "../.env.${ENVIRONMENT}" ".env.local"
    log_success "環境変数を設定しました"
    
    # ビルドテスト
    if [[ "$SKIP_TESTS" != "true" ]]; then
        log_progress "フロントエンドのビルドテストを実行しています..."
        
        if npm run build; then
            log_success "フロントエンドのビルドテストが完了しました"
        else
            log_error "フロントエンドのビルドに失敗しました"
            show_recovery_help "frontend_build_failed"
            exit 1
        fi
    else
        log_info "ビルドテストをスキップしました"
    fi
    
    cd "$PROJECT_ROOT"
}

# Vercelデプロイ
deploy_vercel() {
    if [[ "$DEPLOY_VERCEL" != "true" ]]; then
        return 0
    fi
    
    log_step "Vercel（${ENVIRONMENT}）へのデプロイを実行しています..."
    
    if ! command -v vercel &> /dev/null; then
        log_warning "Vercel CLIがインストールされていません"
        
        if ask_confirmation "Vercel CLIをインストールしますか？" "y"; then
            log_progress "Vercel CLIをインストールしています..."
            npm install -g vercel
            log_success "Vercel CLIをインストールしました"
        else
            log_manual "手動でVercelにデプロイしてください"
            return 0
        fi
    fi
    
    cd "$PROJECT_ROOT/frontend"
    
    # Vercelログイン確認
    if ! vercel whoami &> /dev/null; then
        log_manual "Vercelにログインしてください"
        vercel login
    fi
    
    # 環境変数の設定
    log_progress "Vercel環境変数を設定しています..."
    
    while IFS='=' read -r key value; do
        if [[ -n "$key" && ! "$key" =~ ^# ]]; then
            vercel env add "$key" "$ENVIRONMENT" <<< "$value" 2>/dev/null || true
        fi
    done < ".env.local"
    
    log_success "Vercel環境変数を設定しました"
    
    # デプロイ実行
    log_progress "Vercelデプロイを実行しています..."
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        vercel --prod
    else
        vercel
    fi
    
    log_success "Vercelデプロイが完了しました"
    cd "$PROJECT_ROOT"
}

# 動作確認テスト
run_verification_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        return 0
    fi
    
    log_step "動作確認テストを実行しています..."
    
    # API Gateway URLの取得
    local api_url
    api_url=$(grep "NEXT_PUBLIC_API_URL" ".env.${ENVIRONMENT}" | cut -d'=' -f2 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]]; then
        log_progress "API エンドポイントをテストしています..."
        
        # ヘルスチェック（簡易）
        if curl -s --max-time 10 "${api_url}/health" &> /dev/null; then
            log_success "API エンドポイントが正常に応答しています"
        else
            log_warning "API エンドポイントの応答確認に失敗しました"
            log_tip "デプロイ直後は応答に時間がかかる場合があります"
        fi
    else
        log_warning "API URLが見つかりません"
    fi
    
    # フロントエンドのビルド確認
    cd "$PROJECT_ROOT/frontend"
    if [[ -d ".next" ]]; then
        log_success "フロントエンドのビルドが正常に完了しています"
    else
        log_warning "フロントエンドのビルドディレクトリが見つかりません"
    fi
    
    cd "$PROJECT_ROOT"
    
    # 統合テストの実行（オプション）
    if ask_confirmation "統合テストを実行しますか？（時間がかかります）" "n"; then
        log_progress "統合テストを実行しています..."
        
        if [[ -f "tests/run-integration-tests.sh" ]]; then
            if bash tests/run-integration-tests.sh api; then
                log_success "統合テストが完了しました"
            else
                log_warning "統合テストで問題が発生しました（継続）"
            fi
        else
            log_info "統合テストスクリプトが見つかりません"
        fi
    fi
}

# 設定のバックアップ
backup_configuration() {
    log_progress "設定をバックアップしています..."
    
    cd "$PROJECT_ROOT"
    
    # 設定ファイルのバックアップ
    if "$CONFIG_MANAGER" backup; then
        log_success "設定ファイルのバックアップが完了しました"
    else
        log_warning "設定ファイルのバックアップに失敗しました"
    fi
    
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

# エラー時のリカバリヘルプ
show_recovery_help() {
    local error_type="$1"
    
    echo
    log_error "問題が発生しました。以下の解決方法を試してください:"
    echo
    
    case "$error_type" in
        "config_template_failed")
            log_manual "設定ファイルテンプレートの作成に失敗しました"
            echo "  1. ファイル権限を確認: ls -la setup-config.example.json"
            echo "  2. 手動でコピー: cp setup-config.example.json setup-config.json"
            echo "  3. 再実行: $0"
            ;;
        "config_validation_failed")
            log_manual "設定ファイルの検証に失敗しました"
            echo "  1. 設定ファイルを確認: cat setup-config.json"
            echo "  2. 設定例を参照: docs/beginner-complete-setup-guide.md"
            echo "  3. JSON形式を確認: python3 -m json.tool setup-config.json"
            echo "  4. 再実行: $0"
            ;;
        "env_generation_failed")
            log_manual "環境変数の生成に失敗しました"
            echo "  1. 設定ファイルを確認: $CONFIG_MANAGER validate"
            echo "  2. Python依存関係を確認: pip3 install -r scripts/requirements.txt"
            echo "  3. 再実行: $0"
            ;;
        "aws_auth_failed")
            log_manual "AWS認証に失敗しました"
            echo "  1. AWS設定を確認: aws configure list"
            echo "  2. AWS認証情報を設定: aws configure"
            echo "  3. 認証テスト: aws sts get-caller-identity"
            echo "  4. 再実行: $0"
            ;;
        "s3_creation_failed")
            log_manual "S3バケットの作成に失敗しました"
            echo "  1. バケット名の重複確認（グローバルで一意である必要があります）"
            echo "  2. AWS権限を確認: aws iam get-user"
            echo "  3. 別のバケット名で再試行"
            ;;
        "sam_build_failed")
            log_manual "SAMビルドに失敗しました"
            echo "  1. SAM CLIのバージョン確認: sam --version"
            echo "  2. Python依存関係を確認: cd backend && pip3 install -r src/requirements.txt"
            echo "  3. template.yamlを確認: sam validate"
            echo "  4. 再実行: sam build"
            ;;
        "sam_deploy_failed")
            log_manual "SAMデプロイに失敗しました"
            echo "  1. CloudFormationスタックを確認: aws cloudformation describe-stacks"
            echo "  2. IAM権限を確認"
            echo "  3. 既存スタックの削除: aws cloudformation delete-stack --stack-name $LAMBDA_STACK_NAME"
            echo "  4. 再実行: $0"
            ;;
        "npm_install_failed")
            log_manual "npm installに失敗しました"
            echo "  1. Node.jsバージョン確認: node --version"
            echo "  2. npmキャッシュクリア: npm cache clean --force"
            echo "  3. node_modules削除: rm -rf node_modules package-lock.json"
            echo "  4. 再実行: npm install"
            ;;
        "frontend_build_failed")
            log_manual "フロントエンドビルドに失敗しました"
            echo "  1. 環境変数を確認: cat .env.local"
            echo "  2. TypeScriptエラーを確認: npm run type-check"
            echo "  3. ESLintエラーを確認: npm run lint"
            echo "  4. 依存関係を再インストール: rm -rf node_modules && npm install"
            ;;
        *)
            log_manual "一般的なトラブルシューティング"
            echo "  1. ログファイルを確認: $LOG_FILE"
            echo "  2. ドキュメントを参照: docs/troubleshooting-diagnostic-guide.md"
            echo "  3. FAQを確認: docs/beginner-faq.md"
            echo "  4. 診断フローを実行: docs/troubleshooting-flowchart.md"
            ;;
    esac
    
    echo
    log_tip "詳細なヘルプは docs/index.md から該当するドキュメントを参照してください"
    echo
}

# 最終サマリー表示
show_final_summary() {
    local setup_end_time=$(date +%s)
    local setup_duration=$((setup_end_time - SETUP_START_TIME))
    local setup_minutes=$((setup_duration / 60))
    local setup_seconds=$((setup_duration % 60))
    
    echo
    echo "════════════════════════════════════════════════════════════════"
    log_success "${ICON_PARTY} Excel Unlocker 社内展開用セットアップ完了！ ${ICON_PARTY}"
    echo "════════════════════════════════════════════════════════════════"
    echo
    
    log_info "⏱️  セットアップ時間: ${setup_minutes}分${setup_seconds}秒"
    log_info "🎯 対象環境: $ENVIRONMENT"
    echo
    
    echo -e "${CYAN}${ICON_SUCCESS} 完了した設定:${NC}"
    echo "  ✅ 設定ファイルの初期化・検証"
    echo "  ✅ 環境変数の生成・設定"
    echo "  ✅ AWS S3バケットの作成・セキュリティ設定"
    echo "  ✅ バックエンド（Lambda + API Gateway）のデプロイ"
    echo "  ✅ フロントエンド（Next.js）のセットアップ・ビルド"
    if [[ "$DEPLOY_VERCEL" == "true" ]]; then
        echo "  ✅ Vercelデプロイの実行"
    fi
    if [[ "$SKIP_TESTS" != "true" ]]; then
        echo "  ✅ 動作確認テストの実行"
    fi
    echo "  ✅ 設定のバックアップ"
    echo
    
    echo -e "${GREEN}${ICON_ROCKET} 次のステップ:${NC}"
    echo
    echo "  1. ${ICON_INFO} ローカル開発環境での動作確認:"
    echo "     cd frontend && npm run dev"
    echo "     ブラウザで http://localhost:3000 にアクセス"
    echo
    echo "  2. ${ICON_INFO} Google OAuth設定の確認:"
    echo "     - Google Cloud ConsoleでリダイレクトURIを確認"
    echo "     - テストユーザーでログインテスト"
    echo
    echo "  3. ${ICON_INFO} ファイル解除機能のテスト:"
    echo "     - パスワード付きExcelファイルをアップロード"
    echo "     - 解除・ダウンロード機能の確認"
    echo
    
    if [[ "$ENVIRONMENT" != "production" ]]; then
        echo "  4. ${ICON_INFO} 本番環境へのデプロイ:"
        echo "     $0 production true"
        echo
    fi
    
    echo -e "${BLUE}${ICON_LIGHTBULB} 参考ドキュメント:${NC}"
    echo "  📚 ドキュメント索引: docs/index.md"
    echo "  🔰 初心者向けガイド: docs/beginner-complete-setup-guide.md"
    echo "  ❓ よくある質問: docs/beginner-faq.md"
    echo "  🔧 トラブルシューティング: docs/troubleshooting-flowchart.md"
    echo "  ✅ セットアップチェックリスト: docs/setup-checklist.md"
    echo
    
    echo -e "${PURPLE}${ICON_MANUAL} 生成されたファイル:${NC}"
    echo "  📄 設定ファイル: setup-config.json"
    echo "  🌍 環境変数: .env.${ENVIRONMENT}"
    echo "  💾 バックアップ: config-backup/"
    echo "  📝 ログファイル: $LOG_FILE"
    echo
    
    if [[ -n "${NEXT_PUBLIC_API_URL:-}" ]]; then
        echo -e "${CYAN}${ICON_INFO} 生成されたURL:${NC}"
        echo "  🌐 API Gateway: $NEXT_PUBLIC_API_URL"
        if [[ "$DEPLOY_VERCEL" == "true" ]]; then
            echo "  🚀 Vercel: デプロイ完了（URLはVercel Dashboardで確認）"
        fi
        echo
    fi
    
    log_success "社内展開用セットアップが正常に完了しました！"
    log_tip "問題が発生した場合は、docs/troubleshooting-diagnostic-guide.md を参照してください"
    echo
}

# 使用方法の表示
show_usage() {
    cat << EOF
Excel Unlocker 社内展開用統合セットアップスクリプト

使用方法:
  $0 [オプション]

オプション:
  --environment ENV    対象環境 (development|staging|production) [デフォルト: 対話式選択]
  --deploy-vercel      Vercelデプロイを実行 [デフォルト: 対話式選択]
  --skip-tests         動作確認テストをスキップ [デフォルト: false]
  --non-interactive    非対話モード（上級者向け） [デフォルト: false]
  --help, -h           このヘルプを表示

例:
  $0                                    # 対話式セットアップ（推奨）
  $0 --environment development          # 開発環境の自動セットアップ
  $0 --environment production --deploy-vercel  # 本番環境 + Vercelデプロイ
  $0 --non-interactive --skip-tests    # 非対話・テストスキップ（上級者向け）

特徴:
  🎯 初心者向け対話式セットアップ
  📊 リアルタイム進捗表示
  🔧 エラー時の詳細サポート・リカバリガイド
  ✅ 自動動作確認テスト
  📚 包括的ドキュメント連携

前提条件:
  - Python 3.x
  - AWS CLI (設定済み)
  - SAM CLI
  - Node.js & npm
  - Git

サポート:
  📚 docs/index.md - 全ドキュメント索引
  🔰 docs/beginner-complete-setup-guide.md - 初心者向けガイド
  ❓ docs/beginner-faq.md - よくある質問
  🔧 docs/troubleshooting-flowchart.md - 問題解決フロー

EOF
}

# エラーハンドリング
error_handler() {
    local exit_code=$?
    local line_number=$1
    
    echo
    log_error "スクリプト実行中にエラーが発生しました (行: $line_number, 終了コード: $exit_code)"
    
    # ログファイルに詳細を記録
    {
        echo "=== エラー発生時刻: $(date) ==="
        echo "終了コード: $exit_code"
        echo "行番号: $line_number"
        echo "環境: $ENVIRONMENT"
        echo "Vercelデプロイ: $DEPLOY_VERCEL"
        echo "テストスキップ: $SKIP_TESTS"
        echo "対話モード: $INTERACTIVE_MODE"
        echo "=== 環境変数 ==="
        env | grep -E "(AWS_|NEXT_|GOOGLE_|VERCEL_)" || true
        echo "=== エラー終了 ==="
        echo
    } >> "$LOG_FILE"
    
    show_recovery_help "general"
    
    log_manual "詳細なログは以下のファイルを確認してください: $LOG_FILE"
    
    exit $exit_code
}

# メイン処理
main() {
    # ログファイルの初期化
    {
        echo "=== Excel Unlocker 社内展開用統合セットアップ開始: $(date) ==="
        echo "引数: $*"
        echo "=== セットアップ開始 ==="
        echo
    } > "$LOG_FILE"
    
    # エラーハンドリングの設定
    trap 'error_handler $LINENO' ERR
    
    show_banner
    
    # 進捗管理
    local total_steps=8
    local current_step=0
    
    # Step 1: 前提条件チェック
    ((current_step++))
    show_progress_bar $current_step $total_steps "前提条件チェック"
    check_prerequisites
    
    # Step 2: 対話式設定収集
    if [[ "$INTERACTIVE_MODE" == "true" ]]; then
        ((current_step++))
        show_progress_bar $current_step $total_steps "対話式設定収集"
        collect_interactive_settings
    else
        ((current_step++))
        show_progress_bar $current_step $total_steps "設定確認"
        log_info "非対話モードで実行中..."
    fi
    
    # Step 3: 設定ファイル初期化・検証
    ((current_step++))
    show_progress_bar $current_step $total_steps "設定ファイル初期化・検証"
    initialize_and_validate_config
    
    # Step 4: 環境セットアップ
    ((current_step++))
    show_progress_bar $current_step $total_steps "環境セットアップ"
    setup_environment
    
    # Step 5: S3バケット作成
    ((current_step++))
    show_progress_bar $current_step $total_steps "S3バケット作成"
    create_s3_bucket "$S3_BUCKET_NAME"
    
    # Step 6: バックエンドデプロイ
    ((current_step++))
    show_progress_bar $current_step $total_steps "バックエンドデプロイ"
    deploy_backend
    
    # Step 7: フロントエンドセットアップ + Vercelデプロイ
    ((current_step++))
    show_progress_bar $current_step $total_steps "フロントエンドセットアップ"
    setup_frontend
    deploy_vercel
    
    # Step 8: 動作確認・バックアップ・完了
    ((current_step++))
    show_progress_bar $current_step $total_steps "動作確認・バックアップ・完了"
    run_verification_tests
    backup_configuration
    
    # 完了サマリー
    show_final_summary
    
    # ログファイルに完了記録
    {
        echo "=== セットアップ完了: $(date) ==="
        echo "環境: $ENVIRONMENT"
        echo "Vercelデプロイ: $DEPLOY_VERCEL"
        echo "テストスキップ: $SKIP_TESTS"
        echo "=== セットアップ成功 ==="
        echo
    } >> "$LOG_FILE"
}

# コマンドライン引数の処理
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --deploy-vercel)
            DEPLOY_VERCEL=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --non-interactive)
            INTERACTIVE_MODE=false
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 環境の検証
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "無効な環境: $ENVIRONMENT"
    log_info "有効な環境: development, staging, production"
    exit 1
fi

# メイン処理の実行
main "$@"