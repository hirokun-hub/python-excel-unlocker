#!/bin/bash

# GitHub Secrets 設定スクリプト
# 環境変数設定に特化したシンプルなスクリプト

set -e

# 色付きメッセージ関数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}🎉 =============================================="
    echo -e "   $1"
    echo -e "===============================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}💡 $1${NC}"
}

print_step() {
    echo ""
    echo -e "${PURPLE}📋 ステップ $1: $2${NC}"
    echo "----------------------------------------"
}

print_question() {
    echo -e "${WHITE}❓ $1${NC}"
}

# 安全性チェック関数
check_git_status() {
    print_info "Gitの状態を確認中..."
    
    # .gitignoreに機密情報が除外されているかチェック
    if [ ! -f ".gitignore" ]; then
        print_warning ".gitignoreファイルが見つかりません"
        return 1
    fi
    
    # 重要な除外項目をチェック
    local required_ignores=("*.env*" "setup-config.json" ".config-encryption-key" "config-backup/")
    local missing_ignores=()
    
    for ignore_pattern in "${required_ignores[@]}"; do
        if ! grep -q "$ignore_pattern" .gitignore; then
            missing_ignores+=("$ignore_pattern")
        fi
    done
    
    if [ ${#missing_ignores[@]} -gt 0 ]; then
        print_warning "以下の項目が.gitignoreに追加されていません:"
        for pattern in "${missing_ignores[@]}"; do
            echo "  - $pattern"
        done
        
        print_info ".gitignoreに追加しています..."
        for pattern in "${missing_ignores[@]}"; do
            echo "$pattern" >> .gitignore
        done
        print_success ".gitignoreを更新しました"
    fi
    
    # ステージングされた機密ファイルをチェック
    if git diff --cached --name-only | grep -E "(setup-config\.json|\.env|\.key|secret)" > /dev/null 2>&1; then
        print_error "機密情報を含むファイルがステージングされています"
        print_info "以下のコマンドで取り消してください:"
        echo "  git reset HEAD setup-config.json"
        echo "  git reset HEAD .env*"
        return 1
    fi
    
    print_success "Gitの状態は安全です"
    return 0
}

# GitHub CLI の確認とインストール
check_github_cli() {
    print_step "1" "GitHub CLIの確認"
    
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLIが見つかりません"
        print_info "GitHub CLIをインストールします..."
        
        if command -v brew &> /dev/null; then
            print_info "Homebrewを使用してGitHub CLIをインストール中..."
            brew install gh
            print_success "GitHub CLIをインストールしました"
        else
            print_error "Homebrewが見つかりません"
            print_info "以下の方法でGitHub CLIをインストールしてください:"
            echo "  1. Homebrew: https://brew.sh/"
            echo "  2. GitHub CLI: https://cli.github.com/"
            echo "  3. インストール後、このスクリプトを再実行してください"
            exit 1
        fi
    else
        print_success "GitHub CLIが見つかりました: $(gh --version | head -n1)"
    fi
    
    # GitHub認証の確認
    print_info "GitHub認証を確認中..."
    if ! gh auth status &> /dev/null; then
        print_warning "GitHubにログインしていません"
        print_info "GitHubにログインします..."
        
        echo ""
        echo "🔐 GitHubログインについて:"
        echo "  ✅ 完全に安全です"
        echo "  ✅ あなたのアカウントでログインします"
        echo "  ✅ 必要な権限のみ要求します"
        echo "  ✅ いつでもログアウトできます"
        echo ""
        
        if gh auth login; then
            print_success "GitHubにログインしました"
        else
            print_error "GitHubログインに失敗しました"
            exit 1
        fi
    else
        print_success "GitHubにログイン済みです"
    fi
}

# 環境変数の対話式収集
collect_environment_variables() {
    print_step "2" "環境変数の収集"
    
    echo ""
    echo "🛡️ 安心してください:"
    echo "  ✅ 入力された情報は安全に保護されます"
    echo "  ✅ GitHubにのみ保存され、ローカルには残りません"
    echo "  ✅ 暗号化されて送信されます"
    echo "  ✅ いつでも変更・削除できます"
    echo ""
    
    # 必要な環境変数の定義
    declare -A ENV_VARS
    declare -A ENV_DESCRIPTIONS
    declare -A ENV_EXAMPLES
    declare -A ENV_VALIDATIONS
    
    # Google OAuth設定
    ENV_DESCRIPTIONS["GOOGLE_CLIENT_ID"]="Google OAuth認証用のクライアントID"
    ENV_EXAMPLES["GOOGLE_CLIENT_ID"]="123456789-abcdefg.apps.googleusercontent.com"
    ENV_VALIDATIONS["GOOGLE_CLIENT_ID"]="apps.googleusercontent.com"
    
    ENV_DESCRIPTIONS["GOOGLE_CLIENT_SECRET"]="Google OAuth認証用のクライアントシークレット"
    ENV_EXAMPLES["GOOGLE_CLIENT_SECRET"]="GOCSPX-abcdefghijklmnopqrstuvwxyz"
    ENV_VALIDATIONS["GOOGLE_CLIENT_SECRET"]="GOCSPX-"
    
    # Vercel設定
    ENV_DESCRIPTIONS["VERCEL_TOKEN"]="Vercelデプロイ用の個人アクセストークン"
    ENV_EXAMPLES["VERCEL_TOKEN"]="vercel_1234567890abcdef"
    ENV_VALIDATIONS["VERCEL_TOKEN"]="vercel_"
    
    ENV_DESCRIPTIONS["VERCEL_ORG_ID"]="Vercelチーム/組織ID"
    ENV_EXAMPLES["VERCEL_ORG_ID"]="team_1234567890abcdef"
    ENV_VALIDATIONS["VERCEL_ORG_ID"]="team_"
    
    ENV_DESCRIPTIONS["VERCEL_PROJECT_ID"]="Vercelプロジェクト固有ID"
    ENV_EXAMPLES["VERCEL_PROJECT_ID"]="prj_1234567890abcdef"
    ENV_VALIDATIONS["VERCEL_PROJECT_ID"]="prj_"
    
    # AWS設定
    ENV_DESCRIPTIONS["AWS_ACCESS_KEY_ID"]="AWSリソースアクセス用のアクセスキーID"
    ENV_EXAMPLES["AWS_ACCESS_KEY_ID"]="AKIAIOSFODNN7EXAMPLE"
    ENV_VALIDATIONS["AWS_ACCESS_KEY_ID"]="AKIA"
    
    ENV_DESCRIPTIONS["AWS_SECRET_ACCESS_KEY"]="AWSリソースアクセス用のシークレットアクセスキー"
    ENV_EXAMPLES["AWS_SECRET_ACCESS_KEY"]="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    ENV_VALIDATIONS["AWS_SECRET_ACCESS_KEY"]=""
    
    # 各環境変数を収集
    for var_name in "GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_SECRET" "VERCEL_TOKEN" "VERCEL_ORG_ID" "VERCEL_PROJECT_ID" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY"; do
        collect_single_variable "$var_name"
    done
}

# 単一環境変数の収集
collect_single_variable() {
    local var_name="$1"
    local description="${ENV_DESCRIPTIONS[$var_name]}"
    local example="${ENV_EXAMPLES[$var_name]}"
    local validation="${ENV_VALIDATIONS[$var_name]}"
    
    echo ""
    echo "────────────────────────────────────────"
    print_question "$description を入力してください"
    
    if [ -n "$example" ]; then
        print_info "形式例: $example"
    fi
    
    # 取得方法の説明
    case "$var_name" in
        "GOOGLE_CLIENT_ID"|"GOOGLE_CLIENT_SECRET")
            echo ""
            echo "📍 取得方法:"
            echo "  1. Google Cloud Console (https://console.cloud.google.com/) にアクセス"
            echo "  2. プロジェクトを選択"
            echo "  3. 「認証情報」→「OAuth 2.0 クライアント ID」を選択"
            echo "  4. クライアントIDとシークレットをコピー"
            ;;
        "VERCEL_TOKEN")
            echo ""
            echo "📍 取得方法:"
            echo "  1. Vercel Dashboard (https://vercel.com/dashboard) にアクセス"
            echo "  2. Settings → Tokens"
            echo "  3. 「Create Token」で新しいトークンを作成"
            ;;
        "VERCEL_ORG_ID"|"VERCEL_PROJECT_ID")
            echo ""
            echo "📍 取得方法:"
            echo "  1. プロジェクトルートで 'vercel link' を実行"
            echo "  2. .vercel/project.json ファイルを確認"
            echo "  3. orgId と projectId をコピー"
            ;;
        "AWS_ACCESS_KEY_ID"|"AWS_SECRET_ACCESS_KEY")
            echo ""
            echo "📍 取得方法:"
            echo "  1. AWS Console → IAM → Users"
            echo "  2. ユーザーを選択 → Security credentials"
            echo "  3. 「Create access key」でキーペアを作成"
            ;;
    esac
    
    echo ""
    
    while true; do
        if [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"TOKEN"* ]] || [[ "$var_name" == *"KEY"* ]]; then
            # 機密情報は非表示入力
            read -s -p "🔐 $var_name: " var_value
            echo ""
        else
            read -p "📝 $var_name: " var_value
        fi
        
        # 入力値の検証
        if [ -z "$var_value" ]; then
            print_error "この項目は必須です。もう一度入力してください。"
            continue
        fi
        
        # 形式チェック
        if [ -n "$validation" ] && [[ "$var_value" != *"$validation"* ]]; then
            print_error "形式が正しくありません。例: $example"
            continue
        fi
        
        # 確認
        if [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"TOKEN"* ]] || [[ "$var_name" == *"KEY"* ]]; then
            print_success "入力を確認しました（セキュリティのため値は表示されません）"
        else
            print_success "入力値: $var_value"
        fi
        
        ENV_VARS["$var_name"]="$var_value"
        break
    done
}

# GitHub Secretsへの登録
register_github_secrets() {
    print_step "3" "GitHub Secretsへの登録"
    
    print_info "収集した環境変数をGitHub Secretsに登録します..."
    echo ""
    
    local success_count=0
    local total_count=${#ENV_VARS[@]}
    
    for var_name in "${!ENV_VARS[@]}"; do
        local var_value="${ENV_VARS[$var_name]}"
        
        print_info "登録中: $var_name"
        
        if echo "$var_value" | gh secret set "$var_name"; then
            print_success "$var_name を登録しました"
            ((success_count++))
        else
            print_error "$var_name の登録に失敗しました"
        fi
    done
    
    echo ""
    print_success "$success_count/$total_count の環境変数を登録しました"
    
    if [ $success_count -eq $total_count ]; then
        print_success "全ての環境変数の登録が完了しました！"
        return 0
    else
        print_warning "一部の環境変数の登録に失敗しました"
        return 1
    fi
}

# 登録確認
verify_github_secrets() {
    print_step "4" "登録確認"
    
    print_info "GitHub Secretsの登録状況を確認中..."
    echo ""
    
    if gh secret list > /dev/null 2>&1; then
        print_success "GitHub Secretsにアクセスできます"
        
        echo "📋 登録済みのSecrets:"
        gh secret list | while read -r line; do
            echo "  ✅ $line"
        done
        
        return 0
    else
        print_error "GitHub Secretsの確認に失敗しました"
        return 1
    fi
}

# クリーンアップ
cleanup() {
    print_step "5" "クリーンアップ"
    
    print_info "一時ファイルをクリーンアップ中..."
    
    # 環境変数をメモリから削除
    for var_name in "${!ENV_VARS[@]}"; do
        unset ENV_VARS["$var_name"]
    done
    
    # 履歴をクリア（bash）
    if [ -n "$BASH_VERSION" ]; then
        history -c
        history -w
    fi
    
    print_success "クリーンアップが完了しました"
}

# メイン処理
main() {
    print_header "GitHub Secrets 環境変数設定"
    
    echo "🎯 このスクリプトについて:"
    echo "  ✅ 環境変数設定に特化したシンプルなツール"
    echo "  ✅ 必要な7つの環境変数のみを収集"
    echo "  ✅ GitHub Secretsに安全に保存"
    echo "  ✅ 機密情報の保護を徹底"
    echo "  ✅ 初心者でも安心して使用可能"
    echo ""
    
    echo "⏱️ 所要時間: 約10-15分"
    echo "🛡️ 安全性: 完全に安全です"
    echo "🔄 変更可能: いつでも更新・削除可能"
    echo ""
    
    # 確認プロンプト
    read -p "続行しますか？ (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "セットアップをキャンセルしました"
        exit 0
    fi
    
    # 安全性チェック
    if ! check_git_status; then
        print_error "安全性チェックに失敗しました。修正してから再実行してください。"
        exit 1
    fi
    
    # GitHub CLI確認
    check_github_cli
    
    # 環境変数収集
    collect_environment_variables
    
    # GitHub Secrets登録
    if register_github_secrets; then
        # 登録確認
        verify_github_secrets
        
        # 成功メッセージ
        print_header "設定完了"
        echo "🎉 おめでとうございます！環境変数の設定が完了しました"
        echo ""
        echo "✅ 完了した作業:"
        echo "  - 7つの環境変数を収集"
        echo "  - GitHub Secretsに安全に保存"
        echo "  - 機密情報の保護を確認"
        echo "  - 登録状況の確認"
        echo ""
        echo "🚀 次のステップ:"
        echo "  1. GitHub Actionsワークフローが自動実行されます"
        echo "  2. デプロイメントが開始されます"
        echo "  3. 完了通知をお待ちください"
        echo ""
        echo "📋 管理方法:"
        echo "  - 確認: gh secret list"
        echo "  - 更新: gh secret set VARIABLE_NAME"
        echo "  - 削除: gh secret delete VARIABLE_NAME"
        echo ""
    else
        print_error "環境変数の登録に失敗しました"
        exit 1
    fi
    
    # クリーンアップ
    cleanup
    
    print_success "スクリプトを正常に終了しました"
}

# エラーハンドリング
trap 'print_error "スクリプトが中断されました"; cleanup; exit 1' INT TERM

# スクリプト実行
main "$@"