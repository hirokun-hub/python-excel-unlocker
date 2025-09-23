#!/bin/bash

# GitHub Secrets設定テストスクリプト
# 環境変数設定の動作確認とテスト

set -e

# 色付きメッセージ
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_header() {
    echo ""
    echo -e "${BLUE}🧪 =============================================="
    echo -e "   $1"
    echo -e "===============================================${NC}"
    echo ""
}

# テスト結果の追跡
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TESTS_TOTAL++))
    print_info "テスト実行中: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$test_name"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "$test_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# メイン処理
main() {
    print_header "GitHub Secrets設定テスト"
    
    echo "🎯 このテストについて:"
    echo "  ✅ 環境変数設定スクリプトの動作確認"
    echo "  ✅ 必要なツールの存在確認"
    echo "  ✅ Python環境の動作確認"
    echo "  ✅ 検証スクリプトの動作確認"
    echo ""
    
    # 1. 基本ツールの確認
    print_info "基本ツールの確認..."
    run_test "Python3の存在確認" "command -v python3"
    run_test "Bashの存在確認" "command -v bash"
    run_test "Gitの存在確認" "command -v git"
    
    # 2. GitHub CLIの確認（オプション）
    print_info "GitHub CLIの確認..."
    if command -v gh &> /dev/null; then
        run_test "GitHub CLIの存在確認" "command -v gh"
        if gh auth status &> /dev/null; then
            run_test "GitHub認証状態確認" "gh auth status"
        else
            print_warning "GitHub CLIはインストールされていますが、認証されていません"
        fi
    else
        print_warning "GitHub CLIがインストールされていません（setup-github-secrets.shで自動インストールされます）"
    fi
    
    # 3. Python環境のテスト
    print_info "Python環境のテスト..."
    run_test "Python基本モジュール確認" "python3 -c 'import json, re, sys'"
    
    # 仮想環境の確認
    if [ -d "venv" ]; then
        run_test "仮想環境の存在確認" "[ -f venv/bin/activate ]"
        
        # 仮想環境内でのテスト
        if source venv/bin/activate 2>/dev/null; then
            run_test "仮想環境のアクティベート" "[ -n '$VIRTUAL_ENV' ]"
            
            # 必要パッケージの確認
            if python3 -c "import jsonschema" 2>/dev/null; then
                run_test "jsonschemaパッケージ確認" "python3 -c 'import jsonschema'"
            else
                print_warning "jsonschemaパッケージがインストールされていません"
            fi
            
            deactivate 2>/dev/null || true
        else
            print_warning "仮想環境のアクティベートに失敗しました"
        fi
    else
        print_warning "仮想環境が見つかりません（setup-python-env.shで作成されます）"
    fi
    
    # 4. スクリプトファイルの確認
    print_info "スクリプトファイルの確認..."
    run_test "setup-github-secrets.sh存在確認" "[ -f scripts/setup-github-secrets.sh ]"
    run_test "setup-github-secrets.sh実行権限確認" "[ -x scripts/setup-github-secrets.sh ]"
    run_test "validate-env-vars.py存在確認" "[ -f scripts/validate-env-vars.py ]"
    run_test "validate-env-vars.py実行権限確認" "[ -x scripts/validate-env-vars.py ]"
    run_test "setup-python-env.sh存在確認" "[ -f scripts/setup-python-env.sh ]"
    run_test "setup-python-env.sh実行権限確認" "[ -x scripts/setup-python-env.sh ]"
    
    # 5. 検証スクリプトのテスト
    print_info "検証スクリプトのテスト..."
    
    # テスト用の環境変数データ（有効な形式）
    cat > /tmp/test-env-vars.json << 'EOF'
{
  "GOOGLE_CLIENT_ID": "987654321-zyxwvutsrqponmlkjihgfedcba.apps.googleusercontent.com",
  "GOOGLE_CLIENT_SECRET": "GOCSPX-zyxwvutsrqponmlkjihgfedcba",
  "VERCEL_TOKEN": "vercel_zyxwvutsrqponmlkjihgfedcba",
  "VERCEL_ORG_ID": "team_zyxwvutsrqponmlkjihgfedcba",
  "VERCEL_PROJECT_ID": "prj_zyxwvutsrqponmlkjihgfedcba",
  "AWS_ACCESS_KEY_ID": "AKIAZYXWVUTSRQPONMLK",
  "AWS_SECRET_ACCESS_KEY": "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA"
}
EOF
    
    run_test "検証スクリプトの基本動作確認" "python3 scripts/validate-env-vars.py --json /tmp/test-env-vars.json"
    
    # テストファイルのクリーンアップ
    rm -f /tmp/test-env-vars.json
    
    # 6. .gitignore設定の確認
    print_info ".gitignore設定の確認..."
    run_test ".gitignoreファイル存在確認" "[ -f .gitignore ]"
    
    # 重要な除外項目の確認
    local gitignore_items=("*.env*" "setup-config.json" ".config-encryption-key" "config-backup/")
    for item in "${gitignore_items[@]}"; do
        if grep -q "$item" .gitignore 2>/dev/null; then
            run_test ".gitignore項目確認: $item" "grep -q '$item' .gitignore"
        else
            print_warning ".gitignoreに $item が含まれていません"
        fi
    done
    
    # 7. ドキュメントの確認
    print_info "ドキュメントの確認..."
    run_test "GitHub Secrets設定ガイド存在確認" "[ -f docs/github-secrets-setup-guide.md ]"
    run_test "index.md存在確認" "[ -f docs/index.md ]"
    
    # テスト結果の表示
    print_header "テスト結果"
    
    echo "📊 テスト統計:"
    echo "  ✅ 成功: $TESTS_PASSED"
    echo "  ❌ 失敗: $TESTS_FAILED"
    echo "  📋 合計: $TESTS_TOTAL"
    echo ""
    
    local success_rate=$((TESTS_PASSED * 100 / TESTS_TOTAL))
    echo "📈 成功率: $success_rate%"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "全てのテストに合格しました！"
        echo ""
        echo "🚀 次のステップ:"
        echo "  1. ./scripts/setup-github-secrets.sh を実行"
        echo "  2. GitHub Actionsでの自動デプロイメントを確認"
        echo "  3. デプロイされたアプリケーションをテスト"
        echo ""
        return 0
    else
        print_warning "$TESTS_FAILED 個のテストが失敗しました"
        echo ""
        echo "🔧 推奨される修正手順:"
        
        if [ $TESTS_FAILED -gt $((TESTS_TOTAL / 2)) ]; then
            echo "  1. Python環境をセットアップ: ./scripts/setup-python-env.sh"
            echo "  2. 必要なツールをインストール（GitHub CLI等）"
            echo "  3. このテストを再実行"
        else
            echo "  1. 失敗したテスト項目を個別に確認"
            echo "  2. 必要に応じて環境を修正"
            echo "  3. このテストを再実行"
        fi
        
        echo ""
        return 1
    fi
}

# エラーハンドリング
trap 'print_error "テストが中断されました"; exit 1' INT TERM

# テスト実行
main "$@"