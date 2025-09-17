#!/bin/bash

# 統合テスト実行メインスクリプト

set -e

echo "🧪 Secure Excel Unlock 統合テスト実行"
echo "===================================="

# 引数の処理
TEST_TYPE="${1:-all}"
CLEANUP="${2:-ask}"

# 色付きログ関数
log_info() {
    echo -e "\033[34mℹ️ $1\033[0m"
}

log_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

log_warning() {
    echo -e "\033[33m⚠️ $1\033[0m"
}

log_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件チェック中..."

    # AWS CLI確認
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLIがインストールされていません"
        exit 1
    fi

    # AWS設定確認
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS認証情報が設定されていません"
        log_info "aws configure を実行してください"
        exit 1
    fi

    # Node.js確認
    if ! command -v node &> /dev/null; then
        log_error "Node.jsがインストールされていません"
        exit 1
    fi

    # Python確認
    if ! command -v python3 &> /dev/null; then
        log_error "Python3がインストールされていません"
        exit 1
    fi

    log_success "前提条件チェック完了"
}

# バックエンド統合テスト
run_backend_tests() {
    log_info "バックエンド統合テスト実行中..."
    
    cd tests/integration
    
    # 依存関係インストール
    if [ ! -d "node_modules" ]; then
        log_info "依存関係インストール中..."
        npm install
    fi

    # テスト環境セットアップ
    log_info "テスト環境セットアップ中..."
    npm run setup

    # テスト実行
    case "$TEST_TYPE" in
        "api")
            npm run test:api
            ;;
        "s3")
            npm run test:s3
            ;;
        "e2e")
            npm run test:e2e
            ;;
        "all"|"backend")
            npm test
            ;;
    esac

    cd ../..
    log_success "バックエンド統合テスト完了"
}

# フロントエンド統合テスト
run_frontend_tests() {
    log_info "フロントエンド統合テスト実行中..."
    
    cd frontend
    
    # 依存関係確認
    if [ ! -d "node_modules" ]; then
        log_info "フロントエンド依存関係インストール中..."
        npm install
    fi

    # API統合テスト
    if [ "$TEST_TYPE" = "all" ] || [ "$TEST_TYPE" = "frontend" ] || [ "$TEST_TYPE" = "api" ]; then
        log_info "フロントエンドAPI統合テスト実行中..."
        npm run test -- __tests__/integration/
    fi

    # E2Eテスト
    if [ "$TEST_TYPE" = "all" ] || [ "$TEST_TYPE" = "frontend" ] || [ "$TEST_TYPE" = "e2e" ]; then
        log_info "Playwright E2Eテスト実行中..."
        
        # Playwrightブラウザインストール確認
        if [ ! -d "node_modules/@playwright" ]; then
            log_info "Playwrightインストール中..."
            npx playwright install
        fi
        
        npm run test:e2e -- e2e/integration.spec.ts
    fi

    cd ..
    log_success "フロントエンド統合テスト完了"
}

# クリーンアップ
cleanup_test_environment() {
    log_info "テスト環境クリーンアップ中..."
    
    cd tests/integration
    npm run cleanup
    cd ../..
    
    log_success "クリーンアップ完了"
}

# メイン実行
main() {
    log_info "統合テスト開始: $TEST_TYPE"
    
    check_prerequisites

    case "$TEST_TYPE" in
        "backend"|"api"|"s3")
            run_backend_tests
            ;;
        "frontend")
            run_frontend_tests
            ;;
        "e2e")
            run_backend_tests
            run_frontend_tests
            ;;
        "all")
            run_backend_tests
            run_frontend_tests
            ;;
        *)
            log_error "無効なテストタイプ: $TEST_TYPE"
            echo "使用方法: $0 [all|backend|frontend|api|s3|e2e] [cleanup|no-cleanup]"
            exit 1
            ;;
    esac

    log_success "全統合テスト完了"

    # クリーンアップ確認
    if [ "$CLEANUP" = "cleanup" ]; then
        cleanup_test_environment
    elif [ "$CLEANUP" = "ask" ]; then
        read -p "🧹 テスト環境をクリーンアップしますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cleanup_test_environment
        fi
    fi

    log_success "統合テスト実行完了"
}

# ヘルプ表示
show_help() {
    echo "Secure Excel Unlock 統合テスト実行スクリプト"
    echo ""
    echo "使用方法:"
    echo "  $0 [TEST_TYPE] [CLEANUP_OPTION]"
    echo ""
    echo "TEST_TYPE:"
    echo "  all       - 全統合テスト実行（デフォルト）"
    echo "  backend   - バックエンド統合テストのみ"
    echo "  frontend  - フロントエンド統合テストのみ"
    echo "  api       - API統合テストのみ"
    echo "  s3        - S3連携テストのみ"
    echo "  e2e       - E2Eテストのみ"
    echo ""
    echo "CLEANUP_OPTION:"
    echo "  ask       - クリーンアップを確認（デフォルト）"
    echo "  cleanup   - 自動クリーンアップ"
    echo "  no-cleanup - クリーンアップしない"
    echo ""
    echo "例:"
    echo "  $0 all cleanup          # 全テスト実行後、自動クリーンアップ"
    echo "  $0 api no-cleanup       # APIテストのみ、クリーンアップなし"
    echo "  $0 e2e                  # E2Eテストのみ、クリーンアップ確認"
}

# 引数チェック
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# メイン実行
main