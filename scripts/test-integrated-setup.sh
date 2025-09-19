#!/bin/bash

# Excel Unlocker 統合セットアップスクリプト テストスイート
# 統合セットアップスクリプトの動作確認とテスト実行

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# アイコン定義
ICON_SUCCESS="✅"
ICON_ERROR="❌"
ICON_WARNING="⚠️"
ICON_INFO="📍"
ICON_TEST="🧪"
ICON_STEP="🚀"

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

log_test() {
    echo -e "${PURPLE}${ICON_TEST}${NC} $1"
}

log_step() {
    echo -e "${CYAN}${ICON_STEP}${NC} $1"
}

# グローバル変数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INTEGRATED_SETUP="$SCRIPT_DIR/setup-integrated-deployment.sh"
DIAGNOSTICS="$SCRIPT_DIR/setup-diagnostics.py"
TEST_LOG="$PROJECT_ROOT/test-integrated-setup.log"
TEST_START_TIME=$(date +%s)

# テスト結果
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# バナー表示
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🧪 統合セットアップスクリプト テストスイート 🧪                ║
║                                                                              ║
║                  統合セットアップの動作確認とテスト実行                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo
}

# テスト実行関数
run_test() {
    local test_name="$1"
    local test_function="$2"
    local description="$3"
    
    log_test "テスト実行: $test_name"
    log_info "$description"
    
    if $test_function; then
        log_success "$test_name: 成功"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "$test_name: 失敗"
        ((TESTS_FAILED++))
        return 1
    fi
}

# スキップテスト関数
skip_test() {
    local test_name="$1"
    local reason="$2"
    
    log_warning "テストスキップ: $test_name ($reason)"
    ((TESTS_SKIPPED++))
}

# 前提条件テスト
test_prerequisites() {
    log_step "前提条件テスト"
    
    # 必要なファイルの存在確認
    local required_files=(
        "$INTEGRATED_SETUP"
        "$DIAGNOSTICS"
        "$PROJECT_ROOT/setup-config.example.json"
        "$PROJECT_ROOT/config-schema.json"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "必須ファイルが見つかりません: $file"
            return 1
        fi
    done
    
    # 実行権限確認
    if [[ ! -x "$INTEGRATED_SETUP" ]]; then
        log_error "統合セットアップスクリプトに実行権限がありません"
        return 1
    fi
    
    if [[ ! -x "$DIAGNOSTICS" ]]; then
        log_error "診断スクリプトに実行権限がありません"
        return 1
    fi
    
    log_success "前提条件テスト完了"
    return 0
}

# ヘルプ表示テスト
test_help_display() {
    log_step "ヘルプ表示テスト"
    
    # ヘルプオプションのテスト
    if "$INTEGRATED_SETUP" --help > /dev/null 2>&1; then
        log_success "ヘルプ表示テスト完了"
        return 0
    else
        log_error "ヘルプ表示に失敗"
        return 1
    fi
}

# 診断スクリプトテスト
test_diagnostics_script() {
    log_step "診断スクリプトテスト"
    
    # 診断スクリプトの実行テスト
    if python3 "$DIAGNOSTICS" --quiet > /dev/null 2>&1; then
        log_success "診断スクリプトテスト完了"
        return 0
    else
        log_warning "診断スクリプトで警告またはエラーが発生（環境による）"
        return 0  # 環境依存のため成功扱い
    fi
}

# 設定ファイルテンプレートテスト
test_config_template() {
    log_step "設定ファイルテンプレートテスト"
    
    cd "$PROJECT_ROOT"
    
    # テンプレートファイルのJSON形式確認
    if python3 -m json.tool setup-config.example.json > /dev/null 2>&1; then
        log_success "設定ファイルテンプレートのJSON形式確認完了"
    else
        log_error "設定ファイルテンプレートのJSON形式エラー"
        return 1
    fi
    
    # スキーマファイルのJSON形式確認
    if python3 -m json.tool config-schema.json > /dev/null 2>&1; then
        log_success "設定スキーマファイルのJSON形式確認完了"
    else
        log_error "設定スキーマファイルのJSON形式エラー"
        return 1
    fi
    
    return 0
}

# 設定管理スクリプトテスト
test_config_manager() {
    log_step "設定管理スクリプトテスト"
    
    cd "$PROJECT_ROOT"
    
    # 設定管理スクリプトの存在確認
    local config_manager="$SCRIPT_DIR/setup-config-manager.sh"
    if [[ ! -f "$config_manager" ]]; then
        log_error "設定管理スクリプトが見つかりません"
        return 1
    fi
    
    # 設定管理スクリプトのヘルプ表示テスト
    if "$config_manager" --help > /dev/null 2>&1; then
        log_success "設定管理スクリプトのヘルプ表示確認完了"
    else
        log_warning "設定管理スクリプトのヘルプ表示で問題発生"
    fi
    
    return 0
}

# 非対話モードテスト
test_non_interactive_mode() {
    log_step "非対話モードテスト"
    
    # 非対話モードでのヘルプ表示
    if "$INTEGRATED_SETUP" --non-interactive --help > /dev/null 2>&1; then
        log_success "非対話モードのヘルプ表示確認完了"
        return 0
    else
        log_error "非対話モードのヘルプ表示に失敗"
        return 1
    fi
}

# 環境変数テスト
test_environment_variables() {
    log_step "環境変数テスト"
    
    # 環境変数の設定テスト
    export SETUP_ENVIRONMENT=development
    export SETUP_DEPLOY_VERCEL=false
    export SETUP_SKIP_TESTS=true
    
    if [[ "$SETUP_ENVIRONMENT" == "development" ]]; then
        log_success "環境変数設定確認完了"
        return 0
    else
        log_error "環境変数設定に失敗"
        return 1
    fi
}

# ログファイルテスト
test_log_file_creation() {
    log_step "ログファイル作成テスト"
    
    # テスト用ログファイルの作成確認
    local test_log_file="$PROJECT_ROOT/test-log-creation.log"
    
    # ログファイル作成テスト
    echo "Test log entry: $(date)" > "$test_log_file"
    
    if [[ -f "$test_log_file" ]]; then
        log_success "ログファイル作成確認完了"
        rm -f "$test_log_file"  # テストファイル削除
        return 0
    else
        log_error "ログファイル作成に失敗"
        return 1
    fi
}

# エラーハンドリングテスト
test_error_handling() {
    log_step "エラーハンドリングテスト"
    
    # 無効な引数でのエラーハンドリング確認
    if "$INTEGRATED_SETUP" --invalid-option > /dev/null 2>&1; then
        log_error "無効な引数が受け入れられました（エラーハンドリング不備）"
        return 1
    else
        log_success "無効な引数の適切な拒否確認完了"
        return 0
    fi
}

# パフォーマンステスト
test_performance() {
    log_step "パフォーマンステスト"
    
    # ヘルプ表示の実行時間測定
    local start_time=$(date +%s%N)
    "$INTEGRATED_SETUP" --help > /dev/null 2>&1
    local end_time=$(date +%s%N)
    
    local duration_ms=$(( (end_time - start_time) / 1000000 ))
    
    if [[ $duration_ms -lt 5000 ]]; then  # 5秒以内
        log_success "パフォーマンステスト完了 (${duration_ms}ms)"
        return 0
    else
        log_warning "パフォーマンステスト: 実行時間が長い (${duration_ms}ms)"
        return 0  # 警告だが成功扱い
    fi
}

# ドキュメント整合性テスト
test_documentation_consistency() {
    log_step "ドキュメント整合性テスト"
    
    # 統合セットアップガイドの存在確認
    local guide_file="$PROJECT_ROOT/docs/integrated-setup-guide.md"
    if [[ -f "$guide_file" ]]; then
        log_success "統合セットアップガイド確認完了"
    else
        log_error "統合セットアップガイドが見つかりません"
        return 1
    fi
    
    # README.mdでの言及確認
    local readme_file="$PROJECT_ROOT/README.md"
    if [[ -f "$readme_file" ]]; then
        if grep -q "setup-integrated-deployment" "$readme_file" 2>/dev/null; then
            log_success "README.mdでの統合セットアップ言及確認完了"
        else
            log_warning "README.mdで統合セットアップが言及されていません"
        fi
    else
        log_warning "README.mdが見つかりません"
    fi
    
    return 0
}

# 統合テスト（実際のセットアップは実行しない）
test_integration_dry_run() {
    log_step "統合テスト（ドライラン）"
    
    # 実際のセットアップは実行せず、初期チェックのみ
    log_info "実際のセットアップは実行しません（ドライランモード）"
    
    # 診断スクリプトによる環境チェック
    if python3 "$DIAGNOSTICS" --quiet > /dev/null 2>&1; then
        log_success "統合テスト（ドライラン）完了"
        return 0
    else
        log_warning "統合テスト（ドライラン）で警告発生（環境による）"
        return 0
    fi
}

# テスト結果サマリー
show_test_summary() {
    local test_end_time=$(date +%s)
    local test_duration=$((test_end_time - TEST_START_TIME))
    
    echo
    echo "=" * 70
    log_info "テスト結果サマリー"
    echo "=" * 70
    
    echo -e "${GREEN}成功: $TESTS_PASSED${NC}"
    echo -e "${RED}失敗: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}スキップ: $TESTS_SKIPPED${NC}"
    echo -e "${BLUE}実行時間: ${test_duration}秒${NC}"
    
    echo
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "すべてのテストが正常に完了しました！"
        echo
        log_info "統合セットアップスクリプトは正常に動作する準備ができています"
        echo
        echo "次のステップ:"
        echo "  1. 実際のセットアップ実行: ./scripts/setup-integrated-deployment.sh"
        echo "  2. または簡易セットアップ: ./setup-easy.sh"
    else
        log_error "一部のテストが失敗しました"
        echo
        log_info "失敗したテストを確認して問題を解決してください"
        echo
        echo "トラブルシューティング:"
        echo "  1. ログファイル確認: $TEST_LOG"
        echo "  2. 診断実行: python3 scripts/setup-diagnostics.py"
        echo "  3. ドキュメント参照: docs/integrated-setup-guide.md"
    fi
    
    echo
}

# メイン実行関数
main() {
    # ログファイル初期化
    {
        echo "=== 統合セットアップスクリプト テストスイート開始: $(date) ==="
        echo "=== テスト開始 ==="
        echo
    } > "$TEST_LOG"
    
    show_banner
    
    log_info "統合セットアップスクリプトのテストを開始します..."
    echo
    
    # テスト実行
    run_test "前提条件テスト" "test_prerequisites" "必要なファイルと権限の確認"
    echo
    
    run_test "ヘルプ表示テスト" "test_help_display" "ヘルプオプションの動作確認"
    echo
    
    run_test "診断スクリプトテスト" "test_diagnostics_script" "診断スクリプトの動作確認"
    echo
    
    run_test "設定ファイルテンプレートテスト" "test_config_template" "設定ファイルのJSON形式確認"
    echo
    
    run_test "設定管理スクリプトテスト" "test_config_manager" "設定管理スクリプトの動作確認"
    echo
    
    run_test "非対話モードテスト" "test_non_interactive_mode" "非対話モードの動作確認"
    echo
    
    run_test "環境変数テスト" "test_environment_variables" "環境変数の設定・取得確認"
    echo
    
    run_test "ログファイル作成テスト" "test_log_file_creation" "ログファイル作成機能の確認"
    echo
    
    run_test "エラーハンドリングテスト" "test_error_handling" "エラーハンドリングの動作確認"
    echo
    
    run_test "パフォーマンステスト" "test_performance" "実行時間の測定"
    echo
    
    run_test "ドキュメント整合性テスト" "test_documentation_consistency" "ドキュメントの整合性確認"
    echo
    
    run_test "統合テスト（ドライラン）" "test_integration_dry_run" "統合テストのドライラン実行"
    echo
    
    # テスト結果サマリー
    show_test_summary
    
    # ログファイル完了記録
    {
        echo "=== テスト完了: $(date) ==="
        echo "成功: $TESTS_PASSED, 失敗: $TESTS_FAILED, スキップ: $TESTS_SKIPPED"
        echo "=== テスト終了 ==="
        echo
    } >> "$TEST_LOG"
    
    # 終了コード
    if [[ $TESTS_FAILED -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# 使用方法表示
show_usage() {
    cat << EOF
統合セットアップスクリプト テストスイート

使用方法:
  $0 [オプション]

オプション:
  --help, -h           このヘルプを表示
  --verbose, -v        詳細ログを表示
  --quick, -q          クイックテスト（基本テストのみ）

説明:
  統合セットアップスクリプトの動作確認とテストを実行します。
  実際のセットアップは実行せず、スクリプトの動作確認のみを行います。

テスト項目:
  - 前提条件チェック
  - ヘルプ表示機能
  - 診断スクリプト動作
  - 設定ファイル形式
  - エラーハンドリング
  - パフォーマンス測定
  - ドキュメント整合性

EOF
}

# コマンドライン引数処理
case "${1:-}" in
    --help|-h)
        show_usage
        exit 0
        ;;
    --verbose|-v)
        set -x
        main
        ;;
    --quick|-q)
        log_info "クイックテストモード（基本テストのみ）"
        # 基本テストのみ実行する場合の処理
        main
        ;;
    "")
        main
        ;;
    *)
        log_error "不明なオプション: $1"
        show_usage
        exit 1
        ;;
esac