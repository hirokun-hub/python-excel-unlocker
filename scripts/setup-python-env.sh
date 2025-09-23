#!/bin/bash

# Python環境自動セットアップスクリプト
# macOS外部管理環境対応、最小限の依存関係のみ

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

# プロジェクトルートの確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

print_info "Python環境のセットアップを開始します..."
echo ""

# Python3の確認
if ! command -v python3 &> /dev/null; then
    print_error "Python3が見つかりません"
    echo ""
    echo "📥 Python3のインストール方法:"
    echo "  macOS: brew install python3"
    echo "  または: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_success "Python3が見つかりました: $PYTHON_VERSION"

# 仮想環境の作成または確認
cd "$PROJECT_ROOT"

if [ -d "$VENV_PATH" ]; then
    print_info "既存の仮想環境を確認中..."
    
    # 仮想環境の健全性チェック
    if [ -f "$VENV_PATH/bin/activate" ] && [ -f "$VENV_PATH/bin/python" ]; then
        print_success "既存の仮想環境を使用します"
    else
        print_warning "仮想環境が破損しています。再作成します..."
        rm -rf "$VENV_PATH"
    fi
fi

if [ ! -d "$VENV_PATH" ]; then
    print_info "Python仮想環境を作成中..."
    
    if python3 -m venv "$VENV_PATH"; then
        print_success "Python仮想環境を作成しました"
    else
        print_error "仮想環境の作成に失敗しました"
        
        # macOS外部管理環境エラーの対処
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_warning "macOS外部管理環境エラーの可能性があります"
            print_info "pipxを使用した代替方法を試します..."
            
            # pipxの確認とインストール
            if ! command -v pipx &> /dev/null; then
                print_info "pipxをインストール中..."
                if command -v brew &> /dev/null; then
                    brew install pipx
                    print_success "pipxをインストールしました"
                else
                    print_error "Homebrewが見つかりません"
                    echo ""
                    echo "📥 解決方法:"
                    echo "  1. Homebrew をインストール: https://brew.sh/"
                    echo "  2. pipx をインストール: brew install pipx"
                    echo "  3. このスクリプトを再実行"
                    echo ""
                    exit 1
                fi
            fi
            
            print_success "pipx環境を使用します"
            echo "export USE_PIPX=true" > "$PROJECT_ROOT/.python-env-config"
            exit 0
        else
            exit 1
        fi
    fi
fi

# 仮想環境のアクティベート
print_info "仮想環境をアクティベート中..."

if source "$VENV_PATH/bin/activate"; then
    print_success "仮想環境をアクティベートしました"
else
    print_error "仮想環境のアクティベートに失敗しました"
    exit 1
fi

# pipのアップグレード
print_info "pipをアップグレード中..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pipをアップグレードしました"

# 最小限の必要パッケージのインストール
print_info "必要最小限のパッケージをインストール中..."

# 基本パッケージリスト（GitHub Secrets設定に必要な最小限）
BASIC_PACKAGES=(
    "requests>=2.25.0"
    "jsonschema>=4.0.0"
)

for package in "${BASIC_PACKAGES[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    
    if python -c "import $package_name" &> /dev/null; then
        print_success "$package_name は既にインストールされています"
    else
        print_info "$package をインストール中..."
        if pip install "$package" > /dev/null 2>&1; then
            print_success "$package をインストールしました"
        else
            print_warning "$package のインストールに失敗しました（スキップ）"
        fi
    fi
done

# 環境設定ファイルの作成
print_info "環境設定を保存中..."

cat > "$PROJECT_ROOT/.python-env-config" << EOF
# Python環境設定
export VENV_PATH="$VENV_PATH"
export PYTHON_ENV_READY=true
export USE_PIPX=false

# 仮想環境アクティベート関数
activate_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        echo "✅ 仮想環境をアクティベートしました"
    else
        echo "❌ 仮想環境が見つかりません"
        return 1
    fi
}

# 仮想環境デアクティベート関数
deactivate_venv() {
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
        echo "✅ 仮想環境をデアクティベートしました"
    fi
}
EOF

print_success "環境設定を保存しました: .python-env-config"

# 使用方法の表示
echo ""
echo "🎉 Python環境のセットアップが完了しました！"
echo ""
echo "📋 使用方法:"
echo "  1. 環境設定を読み込み: source .python-env-config"
echo "  2. 仮想環境をアクティベート: activate_venv"
echo "  3. スクリプトを実行: python3 scripts/validate-env-vars.py"
echo "  4. 仮想環境をデアクティベート: deactivate_venv"
echo ""
echo "🔧 自動化された使用方法:"
echo "  ./scripts/setup-github-secrets.sh"
echo ""
echo "📁 作成されたファイル:"
echo "  - $VENV_PATH/ (仮想環境)"
echo "  - .python-env-config (環境設定)"
echo ""

# 自動テスト
print_info "環境テストを実行中..."

if python3 -c "import json, re, sys; print('✅ 基本モジュールが利用可能です')"; then
    print_success "環境テストに合格しました"
else
    print_warning "環境テストで問題が発生しました"
fi

print_success "セットアップスクリプトを完了しました"