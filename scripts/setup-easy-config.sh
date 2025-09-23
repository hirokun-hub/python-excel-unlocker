#!/bin/bash

# Excel解除ツール 簡単設定スクリプト
# 初心者でも迷わず設定できるように作られています

set -e

# 色付きメッセージ関数
print_header() {
    echo ""
    echo "🎉 =============================================="
    echo "   $1"
    echo "=============================================="
    echo ""
}

print_success() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

print_info() {
    echo "💡 $1"
}

print_step() {
    echo ""
    echo "📋 ステップ $1: $2"
    echo "----------------------------------------"
}

# メイン処理開始
print_header "Excel解除ツール 簡単設定ウィザード"

echo "🛡️ 完全に安全です。何も壊れません"
echo "🔄 いつでも元に戻すことができます"
echo "👨‍💻 専門知識は一切不要です"
echo "⏱️ 約10分で完了します"
echo "📞 困ったときはサポートがあります"
echo ""

# 前提条件の確認
print_step "1" "環境の確認"

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    print_error "Python3が見つかりません"
    print_info "Pythonをインストールしてから再実行してください"
    exit 1
fi

print_success "Python3が見つかりました: $(python3 --version)"

# 必要なPythonパッケージの確認とインストール
print_info "必要なパッケージを確認中..."

# 仮想環境の作成（macOS対応）
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_info "macOS環境を検出しました。仮想環境を使用します"
    
    if [ ! -d "venv" ]; then
        print_info "仮想環境を作成中..."
        python3 -m venv venv
        print_success "仮想環境を作成しました"
    fi
    
    print_info "仮想環境をアクティベート中..."
    source venv/bin/activate
    print_success "仮想環境をアクティベートしました"
fi

# 必要なパッケージのインストール
REQUIRED_PACKAGES="jsonschema cryptography"

for package in $REQUIRED_PACKAGES; do
    if ! python3 -c "import $package" &> /dev/null; then
        print_info "${package}をインストール中..."
        pip install $package
        print_success "${package}をインストールしました"
    else
        print_success "${package}は既にインストールされています"
    fi
done

# 設定ファイルの確認
print_step "2" "設定ファイルの確認"

if [ ! -f "setup-config.json" ]; then
    if [ -f "setup-config.example.json" ]; then
        print_info "テンプレートから設定ファイルを作成中..."
        cp setup-config.example.json setup-config.json
        print_success "設定ファイルを作成しました"
    else
        print_error "設定ファイルのテンプレートが見つかりません"
        exit 1
    fi
else
    print_success "設定ファイルが見つかりました"
fi

# 設定方法の選択
print_step "3" "設定方法の選択"

echo "どの方法で設定を行いますか？"
echo ""
echo "1. 🧙‍♂️ ウィザード形式（推奨）"
echo "   → 質問に答えるだけで自動設定"
echo "   → 初心者に最適"
echo "   → 安全で簡単"
echo ""
echo "2. 🔧 自動修正のみ"
echo "   → シークレットキーのみ自動生成"
echo "   → Google設定は手動"
echo "   → 中級者向け"
echo ""
echo "推奨：初めての方は「1」がおすすめです"
echo ""

while true; do
    read -p "選択してください (1-2): " choice
    case $choice in
        1|"")
            print_success "ウィザード形式を選択しました"
            SETUP_MODE="wizard"
            break
            ;;
        2)
            print_success "自動修正モードを選択しました"
            SETUP_MODE="auto-fix"
            break
            ;;
        *)
            print_error "1または2を入力してください"
            ;;
    esac
done

# 設定実行
print_step "4" "設定の実行"

if [ "$SETUP_MODE" = "wizard" ]; then
    print_info "ウィザードを開始します..."
    echo "💡 質問に答えるだけで設定が完了します"
    echo "🛡️ 途中で止めても安全です"
    echo ""
    
    python3 scripts/config_manager.py wizard
    
elif [ "$SETUP_MODE" = "auto-fix" ]; then
    print_info "自動修正を開始します..."
    echo "💡 シークレットキーを自動生成します"
    echo ""
    
    python3 scripts/config_manager.py auto-fix --non-interactive
fi

# 検証テスト実行
print_step "5" "設定の検証"

print_info "設定が正しく完了したかチェック中..."
echo ""

if python3 scripts/config_manager.py verify; then
    print_success "検証テストに合格しました！"
    VERIFICATION_PASSED=true
else
    print_warning "検証テストで問題が見つかりました"
    VERIFICATION_PASSED=false
fi

# 結果表示
print_header "設定完了"

if [ "$VERIFICATION_PASSED" = true ]; then
    echo "🎉 おめでとうございます！設定が完了しました"
    echo ""
    echo "✅ 完了した設定:"
    echo "   - 設定ファイル: setup-config.json"
    echo "   - セキュリティキー: 自動生成済み"
    echo "   - 検証テスト: 合格"
    echo ""
    echo "🚀 次のステップ:"
    echo "   1. デプロイメントスクリプトを実行"
    echo "   2. ./scripts/setup-integrated-deployment.sh"
    echo ""
    echo "📁 重要なファイル:"
    echo "   - 設定ファイル: setup-config.json"
    echo "   - バックアップ: config-backup/ フォルダ"
    echo ""
else
    echo "⚠️  設定は完了しましたが、いくつかの問題があります"
    echo ""
    echo "🔧 修正方法:"
    echo "   1. 上記の問題を確認してください"
    echo "   2. 必要に応じて手動で修正してください"
    echo "   3. python3 scripts/config_manager.py verify で再確認"
    echo ""
fi

echo "📞 困ったときは:"
echo "   - 設定ファイル: setup-config.json を確認"
echo "   - バックアップから復元: config-backup/ フォルダ"
echo "   - 管理者にお問い合わせください"
echo ""

print_success "設定スクリプトを終了します"

# 仮想環境の無効化（macOS）
if [[ "$OSTYPE" == "darwin"* ]] && [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi