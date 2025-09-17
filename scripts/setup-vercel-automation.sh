#!/bin/bash

# Vercel環境変数とプロジェクト設定の自動化スクリプト
# Vercel CLIを使用して手作業を最小限に抑制

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

CONFIG_FILE=".deployment-config.json"

log_info "🚀 Vercel設定の自動化を開始します"

# 1. 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    if ! command -v vercel &> /dev/null; then
        log_error "Vercel CLIがインストールされていません"
        log_info "インストール方法: npm install -g vercel"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jqがインストールされていません"
        log_info "インストール方法: brew install jq (macOS)"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# 2. Vercel認証確認
check_vercel_auth() {
    log_info "Vercel認証を確認中..."
    
    if ! vercel whoami &> /dev/null; then
        log_warning "Vercel認証が必要です"
        log_info "vercel login を実行してください"
        vercel login
    fi
    
    VERCEL_USER=$(vercel whoami)
    log_success "Vercel認証確認完了 (ユーザー: $VERCEL_USER)"
}

# 3. プロジェクト情報の取得
get_project_info() {
    log_info "Vercelプロジェクト情報を取得中..."
    
    cd frontend
    
    # プロジェクトリンク確認
    if [[ ! -f ".vercel/project.json" ]]; then
        log_warning "Vercelプロジェクトがリンクされていません"
        log_info "既存プロジェクトにリンクしますか？ (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            vercel link
        else
            log_info "新しいプロジェクトを作成します"
            vercel --yes
        fi
    fi
    
    # プロジェクト情報取得
    PROJECT_ID=$(jq -r '.projectId' .vercel/project.json)
    ORG_ID=$(jq -r '.orgId' .vercel/project.json)
    
    log_success "プロジェクト情報取得完了"
    log_info "Project ID: $PROJECT_ID"
    log_info "Org ID: $ORG_ID"
    
    # 設定ファイルに保存
    cd ..
    jq --arg pid "$PROJECT_ID" --arg oid "$ORG_ID" \
       '.vercel.project_id = $pid | .vercel.org_id = $oid' "$CONFIG_FILE" > tmp.$$.json && mv tmp.$$.json "$CONFIG_FILE"
}

# 4. 環境変数の自動設定
setup_environment_variables() {
    log_info "Vercel環境変数を自動設定中..."
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "設定ファイルが見つかりません: $CONFIG_FILE"
        log_info "先に scripts/setup-secrets-automation.sh を実行してください"
        exit 1
    fi
    
    # 設定値読み込み
    NEXTAUTH_SECRET=$(jq -r '.secrets.generated.NEXTAUTH_SECRET' "$CONFIG_FILE")
    GOOGLE_CLIENT_ID=$(jq -r '.secrets.manual.GOOGLE_CLIENT_ID' "$CONFIG_FILE")
    GOOGLE_CLIENT_SECRET=$(jq -r '.secrets.manual.GOOGLE_CLIENT_SECRET' "$CONFIG_FILE")
    
    cd frontend
    
    # Production環境変数設定
    log_info "Production環境変数を設定中..."
    
    # API URLは後で手動設定が必要
    log_manual "NEXT_PUBLIC_API_URL と NEXTAUTH_URL は手動設定が必要です"
    echo "Production用の値を入力してください:"
    read -p "本番API URL (例: https://api.example.com): " PROD_API_URL
    read -p "本番フロン��URL (例: https://app.example.com): " PROD_FRONTEND_URL
    
    # Production環境変数設定
    vercel env add NEXT_PUBLIC_API_URL production <<< "$PROD_API_URL"
    vercel env add NEXTAUTH_URL production <<< "$PROD_FRONTEND_URL"
    vercel env add NEXTAUTH_SECRET production <<< "$NEXTAUTH_SECRET"
    vercel env add GOOGLE_CLIENT_ID production <<< "$GOOGLE_CLIENT_ID"
    vercel env add GOOGLE_CLIENT_SECRET production <<< "$GOOGLE_CLIENT_SECRET"
    
    log_success "Production環境変数設定完了"
    
    # Preview環境変数設定
    log_info "Preview環境変数を設定中..."
    
    echo "Preview用の値を入力してください:"
    read -p "ステージングAPI URL (例: https://api-staging.example.com): " STAGING_API_URL
    read -p "PreviewフロントURL (例: https://your-project.vercel.app): " PREVIEW_FRONTEND_URL
    
    vercel env add NEXT_PUBLIC_API_URL preview <<< "$STAGING_API_URL"
    vercel env add NEXTAUTH_URL preview <<< "$PREVIEW_FRONTEND_URL"
    vercel env add NEXTAUTH_SECRET preview <<< "$NEXTAUTH_SECRET"
    vercel env add GOOGLE_CLIENT_ID preview <<< "$GOOGLE_CLIENT_ID"
    vercel env add GOOGLE_CLIENT_SECRET preview <<< "$GOOGLE_CLIENT_SECRET"
    
    log_success "Preview環境変数設定完了"
    
    cd ..
}

# 5. Git連携の解除
disconnect_git_integration() {
    log_info "Vercel Git自動連携を解除中..."
    
    cd frontend
    
    # Git連携解除（CLI経由では直接できないため、手動案内）
    log_manual "以下の手順でGit連携を解除してください:"
    echo "1. https://vercel.com/dashboard にアクセス"
    echo "2. プロジェクト → Settings → Git"
    echo "3. 'Disconnect' をクリック"
    echo
    read -p "Git連携解除を完了したら Enter を押してください..."
    
    cd ..
    
    log_success "Git連携解除確認完了"
}

# 6. ドメイン設定の案内
setup_domain_guide() {
    log_info "ドメイン設定の案内"
    
    log_manual "本番ドメインを設定する場合:"
    echo "1. Vercel Dashboard → プロジェクト → Settings → Domains"
    echo "2. 'Add' をクリックしてドメインを追加"
    echo "3. 提示されるDNS設定をドメイン側に反映"
    echo "4. SSL証明書が自動で配布されます（数分〜数十分）"
    echo
    
    read -p "ドメイン設定を行いますか？ (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "設定するドメイン名を入力してください: " DOMAIN_NAME
        
        cd frontend
        vercel domains add "$DOMAIN_NAME"
        cd ..
        
        log_success "ドメイン追加完了: $DOMAIN_NAME"
        log_info "DNS設定を忘れずに行ってください"
    else
        log_info "ドメイン設定をスキップしました"
    fi
}

# 7. 設定確認
verify_vercel_setup() {
    log_info "Vercel設定を確認中..."
    
    cd frontend
    
    # 環境変数確認
    log_info "環境変数一覧:"
    vercel env ls
    
    # プロジェクト情報確認
    log_info "プロジェクト情報:"
    vercel project ls | grep -E "(Name|ID)"
    
    cd ..
    
    log_success "Vercel設定確認完了"
}

# 8. テストデプロイ
test_deployment() {
    log_info "テストデプロイを実行しますか？ (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "テストデプロイを実行中..."
        
        cd frontend
        
        # プレビューデプロイ
        vercel --yes
        
        DEPLOY_URL=$(vercel ls | head -n 2 | tail -n 1 | awk '{print $2}')
        
        log_success "テストデプロイ完了"
        log_info "デプロイURL: https://$DEPLOY_URL"
        
        cd ..
    else
        log_info "テストデプロイをスキップしました"
    fi
}

# 9. 設定サマリー出力
output_summary() {
    log_success "🎉 Vercel設定の自動化が完了しました！"
    echo
    
    PROJECT_ID=$(jq -r '.vercel.project_id' "$CONFIG_FILE" 2>/dev/null || echo "未設定")
    ORG_ID=$(jq -r '.vercel.org_id' "$CONFIG_FILE" 2>/dev/null || echo "未設定")
    
    echo "📋 設定サマリー:"
    echo "  - Project ID: $PROJECT_ID"
    echo "  - Org ID: $ORG_ID"
    echo "  - 環境変数: Production/Preview設定済み"
    echo "  - Git連携: 解除済み（手動確認）"
    echo
    
    log_info "次のステップ:"
    echo "1. GitHub Actions でのデプロイテスト"
    echo "2. Google OAuth設定の確認"
    echo "3. 本番デプロイの実行"
    echo
    
    log_info "設定ファイル: $CONFIG_FILE"
    log_info "詳細は docs/deployment-guide.md を参照してください"
}

# メイン実行
main() {
    check_prerequisites
    check_vercel_auth
    get_project_info
    setup_environment_variables
    disconnect_git_integration
    setup_domain_guide
    verify_vercel_setup
    test_deployment
    output_summary
}

# スクリプト実行
main "$@"