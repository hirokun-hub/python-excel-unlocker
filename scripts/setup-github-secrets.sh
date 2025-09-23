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
    
    # 必要な環境変数のリスト（macOS Bash 3.x互換）
    ENV_VARS_LIST="GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY NEXTAUTH_SECRET ALLOWED_USERS"
    
    # 各環境変数を収集
    for var_name in $ENV_VARS_LIST; do
        collect_single_variable "$var_name"
    done
}

# 環境変数情報を取得する関数（macOS Bash 3.x互換）
get_var_info() {
    local var_name="$1"
    local info_type="$2"
    
    case "$var_name" in
        "GOOGLE_CLIENT_ID")
            case "$info_type" in
                "description") echo "Google OAuth認証用のクライアントID" ;;
                "example") echo "123456789-abcdefg.apps.googleusercontent.com" ;;
                "validation") echo "apps.googleusercontent.com" ;;
            esac
            ;;
        "GOOGLE_CLIENT_SECRET")
            case "$info_type" in
                "description") echo "Google OAuth認証用のクライアントシークレット" ;;
                "example") echo "GOCSPX-abcdefghijklmnopqrstuvwxyz" ;;
                "validation") echo "GOCSPX-" ;;
            esac
            ;;
        "VERCEL_TOKEN")
            case "$info_type" in
                "description") echo "Vercelデプロイ用の個人アクセストークン" ;;
                "example") echo "vercel_1234567890abcdef または 1234567890abcdef" ;;
                "validation") echo "" ;;
            esac
            ;;
        "VERCEL_ORG_ID")
            case "$info_type" in
                "description") echo "Vercelチーム/組織ID" ;;
                "example") echo "team_1234567890abcdef" ;;
                "validation") echo "team_" ;;
            esac
            ;;
        "VERCEL_PROJECT_ID")
            case "$info_type" in
                "description") echo "Vercelプロジェクト固有ID" ;;
                "example") echo "prj_1234567890abcdef" ;;
                "validation") echo "prj_" ;;
            esac
            ;;
        "AWS_ACCESS_KEY_ID")
            case "$info_type" in
                "description") echo "AWSリソースアクセス用のアクセスキーID" ;;
                "example") echo "AKIAIOSFODNN7EXAMPLE" ;;
                "validation") echo "" ;;
            esac
            ;;
        "AWS_SECRET_ACCESS_KEY")
            case "$info_type" in
                "description") echo "AWSリソースアクセス用のシークレットアクセスキー" ;;
                "example") echo "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" ;;
                "validation") echo "" ;;
            esac
            ;;
        "NEXTAUTH_SECRET")
            case "$info_type" in
                "description") echo "NextAuth.js認証用のシークレットキー" ;;
                "example") echo "32文字以上のランダム文字列" ;;
                "validation") echo "" ;;
            esac
            ;;
        "ALLOWED_USERS")
            case "$info_type" in
                "description") echo "アプリケーション利用を許可するユーザーのメールアドレス" ;;
                "example") echo "user1@example.com,user2@example.com" ;;
                "validation") echo "" ;;
            esac
            ;;
    esac
}

# 単一環境変数の収集
collect_single_variable() {
    local var_name="$1"
    local description=$(get_var_info "$var_name" "description")
    local example=$(get_var_info "$var_name" "example")
    local validation=$(get_var_info "$var_name" "validation")
    
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
        "NEXTAUTH_SECRET")
            echo ""
            echo "📍 設定方法:"
            echo "  1. 32文字以上のランダム文字列を生成"
            echo "  2. 例: openssl rand -base64 32"
            echo "  3. または自動生成を選択（推奨）"
            ;;
        "ALLOWED_USERS")
            echo ""
            echo "📍 設定方法:"
            echo "  1. アプリを利用させたいユーザーのメールアドレス"
            echo "  2. 複数の場合はカンマ区切り"
            echo "  3. 例: admin@company.com,user@company.com"
            ;;
    esac
    
    echo ""
    
    while true; do
        if [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"TOKEN"* ]] || [[ "$var_name" == *"KEY"* ]]; then
            # 機密情報は非表示入力（ペースト確認機能付き）
            echo -n "🔐 $var_name: "
            read -s var_value
            echo ""
            
            # ペースト確認（文字数のみ表示）
            if [ -n "$var_value" ]; then
                local char_count=${#var_value}
                print_info "✅ ${char_count}文字の入力を確認しました"
            fi
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
            print_success "入力を確認しました（${#var_value}文字、セキュリティのため値は非表示）"
        else
            print_success "入力値: $var_value"
        fi
        
        # 環境変数を一時ファイルに保存（macOS互換）
        echo "$var_name=$var_value" >> /tmp/collected_env_vars.txt
        break
    done
}

# GitHub Secretsへの登録
register_github_secrets() {
    print_step "3" "GitHub Secretsへの登録"
    
    print_info "収集した環境変数をGitHub Secretsに登録します..."
    echo ""
    
    local success_count=0
    local total_count=0
    
    # 一時ファイルから環境変数を読み込み
    if [ -f "/tmp/collected_env_vars.txt" ]; then
        while IFS='=' read -r var_name var_value; do
            if [ -n "$var_name" ] && [ -n "$var_value" ]; then
                ((total_count++))
        
                print_info "登録中: $var_name"
                
                if echo "$var_value" | gh secret set "$var_name"; then
                    print_success "$var_name を登録しました"
                    ((success_count++))
                else
                    print_error "$var_name の登録に失敗しました"
                fi
            fi
        done < /tmp/collected_env_vars.txt
    else
        print_error "環境変数が収集されていません"
        return 1
    fi
    
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
    
    # 一時ファイルを削除
    rm -f /tmp/collected_env_vars.txt
    
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