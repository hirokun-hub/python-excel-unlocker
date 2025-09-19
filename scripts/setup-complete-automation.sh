#!/bin/bash

# Excel Unlocker 完全自動化セットアップ（マスタースクリプト）
# 手作業を最小限に抑えた統合セットアップ

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

# バナー表示
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           Excel Unlocker 完全自動化セットアップ             ║"
    echo "║                                                              ║"
    echo "║  手作業を最小限に抑えた統合デプロイメント環境構築            ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
}

# 手作業項目の事前案内
show_manual_requirements() {
    log_manual "このスクリプトで自動化できない手作業項目（事前準備）:"
    echo
    echo "🔑 Google Cloud Console (5分程度)"
    echo "   - OAuth同意画面の設定"
    echo "   - OAuthクライアントIDの作成"
    echo "   - リダイレクトURI/JavaScript生成元の設定"
    echo
    echo "☁️  AWS Console (3分程度)"
    echo "   - IAMユーザー 'github-deploy-bot' の作成"
    echo "   - 最小権限ポリシーのアタッチ"
    echo "   - アクセスキーの発行"
    echo
    echo "🚀 Vercel Dashboard (2分程度)"
    echo "   - APIトークンの作成"
    echo "   - Git連携の解除確認"
    echo
    echo "📋 合計所要時間: 約10分の手作業 + 自動化処理"
    echo
    
    read -p "事前準備を完了してから続行しますか？ (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "事前準備完了後に再実行してください"
        exit 0
    fi
}

# ステップ実行関数
execute_step() {
    local step_name="$1"
    local script_path="$2"
    local description="$3"
    
    log_step "$step_name: $description"
    echo
    
    if [[ -f "$script_path" ]]; then
        if bash "$script_path"; then
            log_success "$step_name 完了"
        else
            log_error "$step_name でエラーが発生しました"
            exit 1
        fi
    else
        log_error "スクリプトが見つかりません: $script_path"
        exit 1
    fi
    
    echo
    echo "----------------------------------------"
    echo
}

# 進捗表示
show_progress() {
    local current=$1
    local total=$2
    local description="$3"
    
    local percentage=$((current * 100 / total))
    local filled=$((current * 50 / total))
    local empty=$((50 - filled))
    
    printf "\r${CYAN}[%3d%%]${NC} [" "$percentage"
    printf "%*s" "$filled" | tr ' ' '█'
    printf "%*s" "$empty" | tr ' ' '░'
    printf "] %s" "$description"
    
    if [[ $current -eq $total ]]; then
        echo
    fi
}

# メイン実行フロー
main() {
    show_banner
    show_manual_requirements
    
    local total_steps=7
    local current_step=0
    
    # Step 0: 環境変数自動検出
    ((current_step++))
    show_progress $current_step $total_steps "環境変数自動検出"
    execute_step "STEP 0" "./scripts/auto-detect-env-vars.sh" "AWS設定と環境変数の自動検出・設定"
    
    # Step 1: 前提条件とシークレット設定
    ((current_step++))
    show_progress $current_step $total_steps "シークレット設定と認証"
    execute_step "STEP 1" "./scripts/setup-secrets-automation.sh" "GitHub Secrets と AWS/Google 認証設定"
    
    # Step 2: Vercel設定
    ((current_step++))
    show_progress $current_step $total_steps "Vercel環境設定"
    execute_step "STEP 2" "./scripts/setup-vercel-automation.sh" "Vercel プロジェクト設定と環境変数"
    
    # Step 3: 初回デプロイ
    ((current_step++))
    show_progress $current_step $total_steps "初回デプロイ実行"
    execute_step "STEP 3" "./scripts/setup-deployment.sh" "AWS SAM 初回デプロイと環境構築"
    
    # Step 4: 段階的デプロイテスト
    ((current_step++))
    show_progress $current_step $total_steps "デプロイメントテスト"
    log_step "STEP 4: 段階的デプロイメントテスト"
    
    log_info "開発環境デプロイテスト実行中..."
    if ./scripts/deploy.sh development backend; then
        log_success "開発環境バックエンドデプロイ成功"
    else
        log_warning "開発環境デプロイで問題が発生しました（継続）"
    fi
    
    # Step 5: GitHub Actions テスト
    ((current_step++))
    show_progress $current_step $total_steps "CI/CDパイプラインテスト"
    log_step "STEP 5: GitHub Actions CI/CD テスト"
    
    log_info "GitHub Actions ワークフローの疎通確認..."
    if gh workflow list &> /dev/null; then
        log_success "GitHub Actions設定確認完了"
        log_info "手動でワークフローをテスト実行してください:"
        echo "  1. GitHub → Actions → 'Deploy Full Stack'"
        echo "  2. 'Run workflow' → environment: development"
    else
        log_warning "GitHub CLI認証が必要です（後で手動確認）"
    fi
    
    # Step 6: 最終確認と案内
    ((current_step++))
    show_progress $current_step $total_steps "セットアップ完了"
    log_step "STEP 6: 最終確認と次のステップ案内"
    
    # 設定ファイル確認
    if [[ -f ".deployment-config.json" ]]; then
        log_success "設定ファイル確認完了"
    else
        log_warning "設定ファイルが見つかりません"
    fi
    
    # 最終サマリー
    show_final_summary
}

# 最終サマリー表示
show_final_summary() {
    echo
    log_success "🎉 Excel Unlocker 完全自動化セットアップ完了！"
    echo
    
    echo -e "${CYAN}📋 完了した設定:${NC}"
    echo "  ✅ GitHub Secrets (AWS, Vercel, Google OAuth)"
    echo "  ✅ AWS IAM最小権限ポリシー生成"
    echo "  ✅ Vercel環境変数 (Production/Preview)"
    echo "  ✅ 初回デプロイ実行"
    echo "  ✅ CI/CDパイプライン設定"
    echo
    
    echo -e "${YELLOW}⚠️  手動確認が必要な項目:${NC}"
    echo "  🔍 Google OAuth設定の動作確認"
    echo "  🔍 Vercel Git連携解除の確認"
    echo "  🔍 GitHub Actions手動実行テスト"
    echo
    
    echo -e "${GREEN}🚀 次のステップ:${NC}"
    echo "  1. 開発環境での動作確認:"
    echo "     cd frontend && npm run dev"
    echo
    echo "  2. ステージング環境デプロイ:"
    echo "     ./scripts/deploy.sh staging all"
    echo
    echo "  3. 本番環境デプロイ:"
    echo "     ./scripts/deploy.sh production all"
    echo
    echo "  4. GitHub Actions自動デプロイテスト:"
    echo "     - develop ブランチにプッシュ → 開発環境"
    echo "     - main ブランチにプッシュ → ステージング環境"
    echo
    
    echo -e "${BLUE}📚 参考ドキュメント:${NC}"
    echo "  - docs/deployment-guide.md (詳細デプロイ手順)"
    echo "  - docs/runbook/ (各種設定ランブック)"
    echo "  - .deployment-config.json (生成された設定)"
    echo
    
    log_info "本番運用開始の準備が完了しました！"
}

# エラーハンドリング
trap 'log_error "スクリプト実行中にエラーが発生しました"; exit 1' ERR

# スクリプト実行
main "$@"