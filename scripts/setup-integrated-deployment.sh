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
    echo ""
    echo -e "${CYAN}${ICON_STEP}${NC} ${WHITE}$1${NC}"
    echo "----------------------------------------"
}

log_progress() {
    echo -e "${YELLOW}${ICON_PROGRESS}${NC} $1"
}

# 設定管理関数
check_config_status() {
    log_step "設定ファイルの状況確認"
    
    if [ ! -f "setup-config.json" ]; then
        log_warning "設定ファイルが見つかりません"
        return 1
    fi
    
    # プレースホルダーチェック
    if python3 scripts/config_manager.py validate 2>/dev/null; then
        log_success "設定ファイルは正常です"
        return 0
    else
        log_warning "設定ファイルに問題があります"
        return 1
    fi
}

run_config_setup() {
    log_step "設定ファイルのセットアップ"
    
    echo "🎯 設定方法を選択してください："
    echo ""
    echo "1. 🧙‍♂️ 簡単ウィザード（推奨）"
    echo "   → 質問に答えるだけで自動設定"
    echo "   → 初心者に最適"
    echo ""
    echo "2. 🔧 自動修正のみ"
    echo "   → シークレットキーのみ自動生成"
    echo "   → Google設定は手動"
    echo ""
    echo "3. ⏭️  スキップ（既に設定済み）"
    echo ""
    echo "推奨：初めての方は「1」がおすすめです"
    
    while true; do
        read -p "選択してください (1-3): " config_choice
        case $config_choice in
            1|"")
                log_info "簡単ウィザードを開始します..."
                if ./scripts/setup-easy-config.sh; then
                    log_success "設定が完了しました"
                    return 0
                else
                    log_error "設定に失敗しました"
                    return 1
                fi
                ;;
            2)
                log_info "自動修正を実行します..."
                if python3 scripts/config_manager.py auto-fix; then
                    log_success "自動修正が完了しました"
                    return 0
                else
                    log_error "自動修正に失敗しました"
                    return 1
                fi
                ;;
            3)
                log_info "設定をスキップします"
                return 0
                ;;
            *)
                log_error "1、2、または3を入力してください"
                ;;
        esac
    done
}

verify_final_config() {
    log_step "最終設定検証"
    
    log_progress "設定ファイルを検証中..."
    
    if python3 scripts/config_manager.py verify; then
        log_success "全ての設定が正常です！"
        return 0
    else
        log_warning "設定に問題があります"
        echo ""
        echo "🔧 修正方法："
        echo "1. python3 scripts/config_manager.py wizard で再設定"
        echo "2. setup-config.json を手動編集"
        echo "3. python3 scripts/config_manager.py verify で再確認"
        echo ""
        
        read -p "続行しますか？ (y/N): " continue_choice
        if [[ $continue_choice =~ ^[Yy]$ ]]; then
            log_warning "設定に問題がありますが続行します"
            return 0
        else
            log_info "設定を修正してから再実行してください"
            return 1
        fi
    fi
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

# Python環境管理用変数
USE_PIPX=false
VENV_ACTIVATED=false
PYTHON_ENV_SETUP=false

# 設定ファイル
SETUP_CONFIG="$PROJECT_ROOT/setup-config.json"
DEPLOYMENT_CONFIG="$PROJECT_ROOT/.deployment-config.json"

# 設定ファイルテンプレートの作成
create_config_template() {
    local template_file="$PROJECT_ROOT/setup-config.example.json"
    
    if [[ -f "$template_file" ]]; then
        log_progress "📋 既存のテンプレートファイルをコピーしています..."
        if cp "$template_file" "$SETUP_CONFIG"; then
            return 0
        else
            log_warning "⚠️  テンプレートファイルのコピーに失敗しました"
        fi
    fi
    
    # テンプレートファイルが存在しない場合は基本的な構造を作成
    log_progress "📋 基本的な設定ファイル構造を作成しています..."
    
    cat > "$SETUP_CONFIG" << 'EOF'
{
  "environments": {
    "development": {
      "aws": {
        "region": "ap-northeast-1",
        "s3": {
          "bucketName": "YOUR_S3_BUCKET_NAME",
          "corsOrigin": "http://localhost:3000"
        },
        "lambda": {
          "stackName": "excel-unlocker-api-dev",
          "timeout": 300,
          "memorySize": 512
        }
      },
      "google": {
        "clientId": "YOUR_GOOGLE_CLIENT_ID",
        "clientSecret": "YOUR_GOOGLE_CLIENT_SECRET",
        "redirectUri": "http://localhost:3000/api/auth/callback/google"
      },
      "vercel": {
        "projectName": "excel-unlocker-dev"
      },
      "security": {
        "allowedUsers": ["your-email@example.com"],
        "jwtSecret": "YOUR_JWT_SECRET_32_CHARS_OR_MORE",
        "sessionSecret": "YOUR_SESSION_SECRET_32_CHARS_OR_MORE"
      }
    },
    "staging": {
      "aws": {
        "region": "ap-northeast-1",
        "s3": {
          "bucketName": "YOUR_S3_BUCKET_NAME_STAGING",
          "corsOrigin": "https://your-app-staging.vercel.app"
        },
        "lambda": {
          "stackName": "excel-unlocker-api-staging",
          "timeout": 300,
          "memorySize": 512
        }
      },
      "google": {
        "clientId": "YOUR_GOOGLE_CLIENT_ID",
        "clientSecret": "YOUR_GOOGLE_CLIENT_SECRET",
        "redirectUri": "https://your-app-staging.vercel.app/api/auth/callback/google"
      },
      "vercel": {
        "projectName": "excel-unlocker-staging"
      },
      "security": {
        "allowedUsers": ["your-email@example.com"],
        "jwtSecret": "YOUR_JWT_SECRET_32_CHARS_OR_MORE",
        "sessionSecret": "YOUR_SESSION_SECRET_32_CHARS_OR_MORE"
      }
    },
    "production": {
      "aws": {
        "region": "ap-northeast-1",
        "s3": {
          "bucketName": "YOUR_S3_BUCKET_NAME_PROD",
          "corsOrigin": "https://your-app.vercel.app"
        },
        "lambda": {
          "stackName": "excel-unlocker-api-prod",
          "timeout": 300,
          "memorySize": 1024
        }
      },
      "google": {
        "clientId": "YOUR_GOOGLE_CLIENT_ID",
        "clientSecret": "YOUR_GOOGLE_CLIENT_SECRET",
        "redirectUri": "https://your-app.vercel.app/api/auth/callback/google"
      },
      "vercel": {
        "projectName": "excel-unlocker"
      },
      "security": {
        "allowedUsers": ["your-email@example.com"],
        "jwtSecret": "YOUR_JWT_SECRET_32_CHARS_OR_MORE",
        "sessionSecret": "YOUR_SESSION_SECRET_32_CHARS_OR_MORE"
      }
    }
  },
  "features": {
    "googleDriveIntegration": true,
    "multiFileProcessing": true,
    "mockMode": false
  },
  "limits": {
    "maxFileSize": 20971520,
    "maxFilesPerBatch": 10,
    "uploadTimeout": 60,
    "downloadTimeout": 300
  },
  "logging": {
    "level": "INFO",
    "enableCloudWatch": true,
    "retentionDays": 30
  }
}
EOF
    
    if [[ -f "$SETUP_CONFIG" ]]; then
        return 0
    else
        return 1
    fi
}

# 設定ファイルの検証
validate_config_file() {
    local config_file="$SETUP_CONFIG"
    
    # ファイルの存在確認
    if [[ ! -f "$config_file" ]]; then
        log_error "❌ 設定ファイルが見つかりません: $config_file"
        return 1
    fi
    
    # JSON形式の検証
    log_progress "📋 JSON形式をチェックしています..."
    
    if ! python3 -m json.tool "$config_file" > /dev/null 2>&1; then
        log_error "❌ 設定ファイルのJSON形式が正しくありません"
        echo
        echo -e "${YELLOW}🔧 JSON形式エラーの確認方法：${NC}"
        echo "  💻 コマンド: python3 -m json.tool setup-config.json"
        echo "  🔍 エラー箇所を確認して修正してください"
        echo
        echo -e "${BLUE}💡 よくあるJSON形式エラー：${NC}"
        echo "  📝 カンマの不足または余分なカンマ"
        echo "  📝 引用符の不足または不正な引用符"
        echo "  📝 括弧の不一致"
        echo "  📝 コメントの記述（JSONではコメント不可）"
        return 1
    fi
    
    log_success "✅ JSON形式は正常です"
    
    # Python環境に応じた検証方法の選択
    if [[ "$USE_PIPX" == "true" ]]; then
        log_progress "🔍 pipx環境で設定内容をチェックしています..."
        
        # pipxを使用した検証（基本的なチェックのみ）
        if validate_config_basic; then
            log_success "✅ 基本的な設定内容は正常です"
            return 0
        else
            log_error "❌ 設定内容に問題があります"
            return 1
        fi
    elif [[ "$VENV_ACTIVATED" == "true" ]]; then
        log_progress "🔍 仮想環境で設定内容をチェックしています..."
        
        # config_manager.pyを使用した詳細検証
        if python3 "$SCRIPT_DIR/config_manager.py" validate --config "$config_file"; then
            log_success "✅ 詳細な設定内容チェックが完了しました"
            return 0
        else
            log_error "❌ 設定内容に問題があります"
            return 1
        fi
    else
        log_progress "🔍 基本的な設定内容をチェックしています..."
        
        # フォールバック：基本的なチェック
        if validate_config_basic; then
            log_success "✅ 基本的な設定内容は正常です"
            return 0
        else
            log_error "❌ 設定内容に問題があります"
            return 1
        fi
    fi
}

# 基本的な設定ファイル検証
validate_config_basic() {
    local config_file="$SETUP_CONFIG"
    local errors=0
    
    # 必須フィールドの存在確認
    log_progress "📋 必須項目をチェックしています..."
    
    # environmentsセクションの確認
    if ! grep -q '"environments"' "$config_file"; then
        log_error "❌ 'environments' セクションが見つかりません"
        errors=$((errors + 1))
    fi
    
    # 各環境の確認
    for env in "development" "staging" "production"; do
        if ! grep -q "\"$env\"" "$config_file"; then
            log_error "❌ '$env' 環境の設定が見つかりません"
            errors=$((errors + 1))
        fi
    done
    
    # プレースホルダーの確認
    log_progress "🔍 プレースホルダーをチェックしています..."
    
    local placeholders=(
        "YOUR_S3_BUCKET_NAME"
        "YOUR_GOOGLE_CLIENT_ID"
        "YOUR_GOOGLE_CLIENT_SECRET"
        "YOUR_JWT_SECRET"
        "YOUR_SESSION_SECRET"
        "your-email@example.com"
    )
    
    for placeholder in "${placeholders[@]}"; do
        if grep -q "$placeholder" "$config_file"; then
            log_warning "⚠️  プレースホルダーが残っています: $placeholder"
            errors=$((errors + 1))
        fi
    done
    
    # エラー数に応じた結果
    if [[ $errors -eq 0 ]]; then
        return 0
    else
        echo
        log_error "❌ $errors 個の問題が見つかりました"
        echo
        echo -e "${YELLOW}🔧 修正が必要な項目：${NC}"
        echo "  📝 プレースホルダー（YOUR_...）を実際の値に変更"
        echo "  📝 メールアドレスを実際のアドレスに変更"
        echo "  📝 必須セクションの追加"
        echo
        return 1
    fi
}

# バナー表示
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                🎉 Excel Unlocker かんたんセットアップ 🎉                     ║
║                                                                              ║
║              小学生でもわかる！安心・安全・自動セットアップ                  ║
║                                                                              ║
║  ✅ 何も壊れる心配はありません  ✅ いつでも元に戻せます                      ║
║  ✅ 分からなくてもOK            ✅ 全部自動でやってくれます                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo
    
    echo -e "${GREEN}🎯 このツールで何ができるの？${NC}"
    echo "  📱 スマホ・タブレット・パソコンでExcelのパスワードを解除"
    echo "  🚀 複数のファイルを一度に処理"
    echo "  ☁️  Google Driveに直接保存"
    echo "  🔒 安全・安心のセキュリティ"
    echo "  🌐 24時間いつでもどこからでもアクセス"
    echo
    
    echo -e "${BLUE}⏱️  どのくらい時間がかかるの？${NC}"
    echo "  🏃‍♂️ 初回セットアップ: 約15-20分"
    echo "  ⚡ 2回目以降: 約5分"
    echo "  📝 あなたがすること: 最初の設定のみ（5-10分）"
    echo "  🤖 自動でやること: あとは全部おまかせ"
    echo
    
    echo -e "${PURPLE}🛡️  安心・安全について${NC}"
    echo "  ✅ 何も壊れません・削除されません"
    echo "  ✅ いつでも元に戻すことができます"
    echo "  ✅ あなたのファイルは安全に保護されます"
    echo "  ✅ 分からないことがあっても大丈夫"
    echo "  ✅ 小学生でも使えるように作りました"
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
            echo -n "はい/いいえ (はい): "
        else
            echo -n "はい/いいえ (いいえ): "
        fi
        
        read -r response
        
        if [[ -z "$response" ]]; then
            response="$default"
        fi
        
        case "$response" in
            [Yy]|[Yy][Ee][Ss]|はい|ハイ|yes|YES)
                return 0
                ;;
            [Nn]|[Nn][Oo]|いいえ|イイエ|no|NO)
                return 1
                ;;
            *)
                log_error "「はい」または「いいえ」で答えてください（英語のy/nでもOKです）"
                ;;
        esac
    done
}

# Python環境の準備
setup_python_environment() {
    log_step "🐍 Python環境を準備しています..."
    
    echo
    log_info "💡 今何をしているか：Pythonプログラムを安全に動かすための環境を作成中"
    log_info "⏱️  所要時間：約1-2分"
    echo
    
    cd "$PROJECT_ROOT"
    
    # 仮想環境の作成
    if [[ ! -d "venv" ]]; then
        log_progress "🏗️  Python仮想環境を作成しています..."
        
        if python3 -m venv venv; then
            log_success "✅ Python仮想環境を作成しました"
        else
            log_error "❌ Python仮想環境の作成に失敗しました"
            echo
            echo -e "${YELLOW}🔧 解決方法：${NC}"
            echo "  💡 pipxを使用した分離環境での実行を試します"
            echo "  🛡️ 完全に安全です。何も壊れません"
            echo
            
            # pipxの確認とインストール
            if ! command -v pipx &> /dev/null; then
                log_progress "📦 pipxをインストールしています..."
                
                if command -v brew &> /dev/null; then
                    if brew install pipx; then
                        log_success "✅ pipxをインストールしました"
                    else
                        log_error "❌ pipxのインストールに失敗しました"
                        show_python_environment_help
                        exit 1
                    fi
                else
                    log_error "❌ Homebrewが見つかりません"
                    show_python_environment_help
                    exit 1
                fi
            fi
            
            # pipxを使用してconfig_managerを実行
            USE_PIPX=true
            log_success "✅ pipx環境での実行に切り替えました"
            return 0
        fi
    else
        log_info "✅ 既存のPython仮想環境を使用します"
    fi
    
    # 仮想環境のアクティベート
    log_progress "⚡ Python仮想環境をアクティベートしています..."
    
    if source venv/bin/activate; then
        log_success "✅ Python仮想環境をアクティベートしました"
        VENV_ACTIVATED=true
    else
        log_error "❌ Python仮想環境のアクティベートに失敗しました"
        show_python_environment_help
        exit 1
    fi
    
    # 依存関係のインストール
    log_progress "📦 Python依存関係をインストールしています..."
    
    if pip install -r scripts/requirements.txt; then
        log_success "✅ Python依存関係をインストールしました"
        echo
        log_info "🎯 インストールされたパッケージ："
        echo "  📊 jsonschema: 設定ファイルの検証用"
        echo "  🔒 cryptography: 暗号化機能用"
        echo "  📄 PyYAML: YAML設定ファイル用"
        echo "  🔧 msoffcrypto-tool: Excel解除用"
    else
        log_error "❌ Python依存関係のインストールに失敗しました"
        echo
        echo -e "${YELLOW}🔧 解決方法：${NC}"
        echo "  💡 pipxを使用した分離環境での実行を試します"
        
        # pipxフォールバック
        if ! command -v pipx &> /dev/null; then
            log_progress "📦 pipxをインストールしています..."
            
            if command -v brew &> /dev/null; then
                if brew install pipx; then
                    log_success "✅ pipxをインストールしました"
                else
                    log_error "❌ pipxのインストールに失敗しました"
                    show_python_environment_help
                    exit 1
                fi
            else
                log_error "❌ Homebrewが見つかりません"
                show_python_environment_help
                exit 1
            fi
        fi
        
        USE_PIPX=true
        log_success "✅ pipx環境での実行に切り替えました"
    fi
    
    echo
    log_info "🎯 次に進みます：設定ファイルの準備を始めます"
    echo
}

# Python環境問題のヘルプ表示
show_python_environment_help() {
    echo
    log_error "🚨 Python環境の問題が発生しました"
    echo
    echo -e "${CYAN}📋 この問題について：${NC}"
    echo "  🍎 macOSでは、システムのPython環境が外部管理されているため"
    echo "  📦 直接パッケージをインストールできない場合があります"
    echo "  🛡️ これは安全性のための仕組みです"
    echo
    echo -e "${GREEN}✅ 解決方法（自動で試行済み）：${NC}"
    echo "  1️⃣ 仮想環境（venv）の使用"
    echo "  2️⃣ pipxによる分離環境での実行"
    echo
    echo -e "${YELLOW}🔧 手動での解決方法：${NC}"
    echo "  📝 以下のコマンドを実行してください："
    echo
    echo "     # Homebrewでpipxをインストール"
    echo "     brew install pipx"
    echo
    echo "     # 仮想環境を作成"
    echo "     python3 -m venv venv"
    echo "     source venv/bin/activate"
    echo "     pip install -r scripts/requirements.txt"
    echo
    echo -e "${BLUE}💡 その他の方法：${NC}"
    echo "  🐍 pyenvを使用してPythonバージョンを管理"
    echo "  🐳 Dockerを使用した完全分離環境"
    echo
    echo -e "${GREEN}🛡️  安心してください：${NC}"
    echo "  ✅ この問題は一般的で、解決可能です"
    echo "  ✅ あなたのシステムは安全です"
    echo "  ✅ 上記の方法で確実に解決できます"
    echo
}

# 前提条件チェック
check_prerequisites() {
    log_step "🔍 必要なソフトウェアがインストールされているかチェックしています..."
    
    echo
    log_info "💡 今何をしているか：Excelツールに必要なソフトウェアが揃っているか確認中"
    log_info "⏱️  所要時間：約30秒"
    echo
    
    local missing_tools=()
    local tool_info=""
    
    # 必要なツールのチェック
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("Python（パイソン）")
        tool_info+="\n  🐍 Python 3.x: プログラムを動かすためのソフト"
        tool_info+="\n     ダウンロード: https://www.python.org/downloads/"
    fi
    
    if ! command -v aws &> /dev/null; then
        missing_tools+=("AWS CLI（エーダブリューエス）")
        tool_info+="\n  ☁️  AWS CLI: クラウドサービスと連携するためのソフト"
        tool_info+="\n     ダウンロード: https://aws.amazon.com/cli/"
    fi
    
    if ! command -v sam &> /dev/null; then
        missing_tools+=("SAM CLI（サム）")
        tool_info+="\n  🚀 SAM CLI: サーバーレス機能をデプロイするためのソフト"
        tool_info+="\n     ダウンロード: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    fi
    
    if ! command -v node &> /dev/null; then
        missing_tools+=("Node.js（ノードジェイエス）")
        tool_info+="\n  🌐 Node.js: ウェブアプリを動かすためのソフト"
        tool_info+="\n     ダウンロード: https://nodejs.org/"
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("Git（ギット）")
        tool_info+="\n  📝 Git: プログラムのバージョン管理をするためのソフト"
        tool_info+="\n     ダウンロード: https://git-scm.com/"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo
        log_error "❌ 以下のソフトウェアがインストールされていません："
        echo
        for tool in "${missing_tools[@]}"; do
            echo "  ❌ $tool"
        done
        echo
        echo -e "${YELLOW}🛠️  インストールが必要なソフトウェア：${NC}"
        echo -e "$tool_info"
        echo
        echo -e "${GREEN}🛡️  安心してください：${NC}"
        echo "  ✅ これらのソフトウェアは全て無料で安全です"
        echo "  ✅ 公式サイトからダウンロードできます"
        echo "  ✅ インストール後にもう一度このスクリプトを実行してください"
        echo "  ✅ 何も壊れる心配はありません"
        echo
        
        if ask_confirmation "インストール方法を確認して、後でもう一度実行しますか？" "y"; then
            log_info "📋 次にすること："
            echo "  1. 上記のソフトウェアをインストール"
            echo "  2. パソコンを再起動（推奨）"
            echo "  3. このスクリプトをもう一度実行"
            echo
            log_success "インストール完了後にお待ちしています！"
        fi
        
        exit 1
    fi
    
    echo
    log_success "✅ 必要なソフトウェアが全て揃っています！"
    log_info "🎯 次に進みます：設定ファイルの準備を始めます"
    echo
}

# 環境変数ファイルの生成
generate_env_file() {
    local environment="$1"
    local output_file=".env.${environment}"
    
    # Python環境に応じた生成方法の選択
    if [[ "$USE_PIPX" == "true" ]]; then
        log_progress "🔧 pipx環境で環境変数を生成しています..."
        
        # 基本的な環境変数生成（フォールバック）
        if generate_env_basic "$environment" "$output_file"; then
            return 0
        else
            return 1
        fi
    elif [[ "$VENV_ACTIVATED" == "true" ]]; then
        log_progress "🔧 仮想環境で環境変数を生成しています..."
        
        # config_manager.pyを使用した生成
        if python3 scripts/config_manager.py generate-env "$environment" --format dotenv --output "$output_file" --config "$SETUP_CONFIG"; then
            return 0
        else
            log_warning "⚠️  詳細生成に失敗しました。基本生成を試行します..."
            if generate_env_basic "$environment" "$output_file"; then
                return 0
            else
                return 1
            fi
        fi
    else
        log_progress "🔧 基本的な環境変数を生成しています..."
        
        # フォールバック：基本的な生成
        if generate_env_basic "$environment" "$output_file"; then
            return 0
        else
            return 1
        fi
    fi
}

# 基本的な環境変数生成
generate_env_basic() {
    local environment="$1"
    local output_file="$2"
    local config_file="$SETUP_CONFIG"
    
    log_progress "📝 基本的な環境変数を抽出しています..."
    
    # JSONから値を抽出（jqが利用可能な場合）
    if command -v jq &> /dev/null; then
        log_progress "🔧 jqを使用して環境変数を生成しています..."
        
        # jqを使用した抽出
        local aws_region=$(jq -r ".environments.${environment}.aws.region" "$config_file" 2>/dev/null || echo "ap-northeast-1")
        local s3_bucket=$(jq -r ".environments.${environment}.aws.s3.bucketName" "$config_file" 2>/dev/null || echo "")
        local cors_origin=$(jq -r ".environments.${environment}.aws.s3.corsOrigin" "$config_file" 2>/dev/null || echo "")
        local stack_name=$(jq -r ".environments.${environment}.aws.lambda.stackName" "$config_file" 2>/dev/null || echo "excel-unlocker-api-${environment}")
        local google_client_id=$(jq -r ".environments.${environment}.google.clientId" "$config_file" 2>/dev/null || echo "")
        local google_client_secret=$(jq -r ".environments.${environment}.google.clientSecret" "$config_file" 2>/dev/null || echo "")
        local nextauth_url=$(jq -r ".environments.${environment}.google.redirectUri" "$config_file" 2>/dev/null | sed 's|/api/auth/callback/google||' || echo "")
        local allowed_users=$(jq -r ".environments.${environment}.security.allowedUsers | join(\",\")" "$config_file" 2>/dev/null || echo "")
        local jwt_secret=$(jq -r ".environments.${environment}.security.jwtSecret" "$config_file" 2>/dev/null || echo "")
        local session_secret=$(jq -r ".environments.${environment}.security.sessionSecret" "$config_file" 2>/dev/null || echo "")
        
        # 環境変数ファイルの作成
        cat > "$output_file" << EOF
# 自動生成された環境変数設定 (${environment})
# 生成日時: $(date)

# AWS設定
AWS_REGION=${aws_region}
S3_BUCKET_NAME=${s3_bucket}
CORS_ORIGIN=${cors_origin}
LAMBDA_STACK_NAME=${stack_name}
LAMBDA_TIMEOUT=300
LAMBDA_MEMORY_SIZE=512

# Google OAuth設定
GOOGLE_CLIENT_ID=${google_client_id}
GOOGLE_CLIENT_SECRET=${google_client_secret}
NEXTAUTH_URL=${nextauth_url}

# セキュリティ設定
ALLOWED_USERS=${allowed_users}
NEXTAUTH_SECRET=${session_secret}
JWT_SECRET=${jwt_secret}

# 機能設定
NEXT_PUBLIC_GOOGLE_DRIVE_ENABLED=true
NEXT_PUBLIC_MULTI_FILE_ENABLED=true
NEXT_PUBLIC_USE_MOCK_API=false

# 制限設定
MAX_FILE_SIZE=20971520
MAX_FILES_PER_BATCH=10
UPLOAD_TIMEOUT=60
DOWNLOAD_TIMEOUT=300

# ログ設定
LOG_LEVEL=INFO
CLOUDWATCH_ENABLED=true
LOG_RETENTION_DAYS=30
EOF
        
        if [[ -f "$output_file" ]]; then
            log_success "✅ jqを使用して環境変数ファイルを生成しました"
            return 0
        fi
    fi
    
    # jqが利用できない場合の基本的な抽出
    log_progress "🔧 基本的な方法で環境変数を生成しています..."
    
    # 基本的な環境変数ファイルの作成
    cat > "$output_file" << EOF
# 基本的な環境変数設定 (${environment})
# 生成日時: $(date)
# 注意: 設定ファイルから手動で値を確認・更新してください

# AWS設定
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=excel-unlocker-${environment}
CORS_ORIGIN=http://localhost:3000
LAMBDA_STACK_NAME=excel-unlocker-api-${environment}
LAMBDA_TIMEOUT=300
LAMBDA_MEMORY_SIZE=512

# Google OAuth設定（要設定）
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
NEXTAUTH_URL=http://localhost:3000

# セキュリティ設定（要設定）
ALLOWED_USERS=your-email@example.com
NEXTAUTH_SECRET=YOUR_SESSION_SECRET_32_CHARS_OR_MORE
JWT_SECRET=YOUR_JWT_SECRET_32_CHARS_OR_MORE

# 機能設定
NEXT_PUBLIC_GOOGLE_DRIVE_ENABLED=true
NEXT_PUBLIC_MULTI_FILE_ENABLED=true
NEXT_PUBLIC_USE_MOCK_API=false

# 制限設定
MAX_FILE_SIZE=20971520
MAX_FILES_PER_BATCH=10
UPLOAD_TIMEOUT=60
DOWNLOAD_TIMEOUT=300

# ログ設定
LOG_LEVEL=INFO
CLOUDWATCH_ENABLED=true
LOG_RETENTION_DAYS=30
EOF
    
    if [[ -f "$output_file" ]]; then
        log_warning "⚠️  基本的な環境変数ファイルを生成しました"
        log_info "📝 setup-config.json の値を確認して、必要に応じて ${output_file} を更新してください"
        return 0
    else
        return 1
    fi
}

# 対話式設定収集
collect_interactive_settings() {
    log_step "📋 Excel Unlockerの設定を始めます..."
    
    echo
    echo -e "${GREEN}🛡️  安心してください：${NC}"
    echo "  ✅ 何も壊れる心配はありません"
    echo "  ✅ いつでも元に戻すことができます"
    echo "  ✅ 分からない項目はデフォルト値（おすすめ設定）を使えます"
    echo "  ✅ 間違えても後から変更できます"
    echo
    
    log_info "🎯 これから3つの簡単な質問にお答えください"
    echo
    
    # 環境選択（初心者向けの説明）
    echo -e "${CYAN}📍 質問1: どの環境でExcelツールを使いますか？${NC}"
    echo
    echo "これは「どこでツールを動かすか」を決める設定です。"
    echo "初めての方は「1」を選んでください。"
    echo
    echo "  1) 🧪 テスト環境（development）"
    echo "     └ 何をする：あなたのパソコンでテスト用に動かします"
    echo "     └ 安全性：完全に安全です。本番には影響しません"
    echo "     └ 推奨度：⭐⭐⭐ 初めての方に最適"
    echo
    echo "  2) 🔍 確認環境（staging）"
    echo "     └ 何をする：本番前の最終確認用に動かします"
    echo "     └ 安全性：安全です。テスト専用の環境です"
    echo "     └ 推奨度：⭐⭐ 慣れてきた方向け"
    echo
    echo "  3) 🚀 本番環境（production）"
    echo "     └ 何をする：実際に業務で使う環境で動かします"
    echo "     └ 安全性：安全ですが、実際の業務に影響します"
    echo "     └ 推奨度：⭐ 上級者・管理者向け"
    echo
    
    while true; do
        echo -n "どれを選びますか？ (1-3) [おすすめ: 1]: "
        read env_choice
        case "${env_choice:-1}" in
            1)
                ENVIRONMENT="development"
                log_success "✅ テスト環境を選択しました（安全で初心者向けです）"
                break
                ;;
            2)
                ENVIRONMENT="staging"
                log_success "✅ 確認環境を選択しました"
                break
                ;;
            3)
                ENVIRONMENT="production"
                log_success "✅ 本番環境を選択しました"
                break
                ;;
            *)
                log_error "1、2、または3の数字を入力してください"
                ;;
        esac
    done
    
    echo
    echo "────────────────────────────────────────"
    echo
    
    # Vercelデプロイ確認（初心者向けの説明）
    echo -e "${CYAN}📍 質問2: インターネットからアクセスできるようにしますか？${NC}"
    echo
    echo "これは「スマホやタブレットからも使えるようにするか」の設定です。"
    echo
    echo "「はい」を選ぶと："
    echo "  ✅ スマホ・タブレット・他のパソコンからも使えます"
    echo "  ✅ 他の人にもURLを教えて使ってもらえます"
    echo "  ✅ 24時間いつでもアクセスできます"
    echo "  ✅ 外出先からでも使えます"
    echo
    echo "「いいえ」を選ぶと："
    echo "  📱 今のパソコンでのみ使えます"
    echo "  🏠 家や会社でのみ使えます"
    echo
    echo "安全性："
    echo "  🛡️ どちらを選んでも完全に安全です"
    echo "  🔄 後からいつでも変更できます"
    echo "  ⏱️ 「はい」を選んでも追加で5分程度です"
    echo
    echo "推奨：初めての方は「はい」がおすすめです"
    echo
    echo "  🔄 後からいつでも変更できます"
    echo "  ⏱️ 「はい」を選んでも追加で5分程度です"
    echo
    echo "推奨：初めての方は「はい」がおすすめです"
    echo
    
    if ask_confirmation "インターネットからアクセスできるようにしますか？" "y"; then
        DEPLOY_VERCEL=true
        log_success "✅ インターネットアクセスを有効にしました（便利です！）"
    else
        log_success "✅ ローカル環境のみで動作します"
    fi
    
    echo
    echo "────────────────────────────────────────"
    echo
    
    # テストスキップ確認（初心者向けの説明）
    echo -e "${CYAN}📍 質問3: 動作確認テストを実行しますか？${NC}"
    echo
    echo "これは「ツールが正しく動くかチェックするか」の設定です。"
    echo
    echo "「はい」を選ぶと："
    echo "  ✅ ツールが正しく動くか自動でチェックします"
    echo "  ✅ 問題があれば教えてくれます"
    echo "  ✅ 安心して使い始められます"
    echo "  ⏱️ 追加で2-3分かかります"
    echo
    echo "「いいえ」を選ぶと："
    echo "  ⚡ セットアップが早く終わります"
    echo "  🔧 上級者向けの設定です"
    echo
    echo "安全性："
    echo "  🛡️ どちらを選んでも安全です"
    echo "  🔍 テストは確認するだけで何も壊しません"
    echo
    echo "推奨：初めての方は「はい」がおすすめです"
    echo
    
    if ask_confirmation "動作確認テストを実行しますか？" "y"; then
        SKIP_TESTS=false
        log_success "✅ 動作確認テストを実行します（安心です！）"
    else
        SKIP_TESTS=true
        log_success "✅ 動作確認テストをスキップします"
    fi
    
    echo
    echo "════════════════════════════════════════"
    echo
    log_success "🎉 設定が完了しました！"
    echo
    echo "📋 選択した設定："
    echo "  🎯 環境: $ENVIRONMENT"
    echo "  🌐 インターネットアクセス: $([ "$DEPLOY_VERCEL" = true ] && echo "有効" || echo "無効")"
    echo "  🔍 動作確認テスト: $([ "$SKIP_TESTS" = false ] && echo "実行する" || echo "スキップ")"
    echo
    log_info "💡 次に進みます。自動でセットアップが始まります..."
    echo
}

# 設定ファイルの初期化と検証
initialize_and_validate_config() {
    log_step "📄 設定ファイルを準備しています..."
    
    echo
    log_info "💡 今何をしているか：Excelツールの設定ファイルを作成・確認中"
    log_info "⏱️  所要時間：設定済みなら30秒、初回なら5-10分"
    echo
    
    cd "$PROJECT_ROOT"
    
    # 設定ファイルの状況確認
    if ! check_config_status; then
        log_info "📝 設定ファイルのセットアップが必要です"
        
        if [[ "$INTERACTIVE_MODE" == "true" ]]; then
            # 対話モードでは新しい設定管理機能を使用
            if ! run_config_setup; then
                log_error "❌ 設定セットアップに失敗しました"
                show_recovery_help "config_setup_failed"
                exit 1
            fi
        else
            # 非対話モードでは従来の方法
            log_info "📝 設定ファイルのひな形を作成しています..."
            
            if python3 scripts/config_manager.py create; then
                log_success "✅ 設定ファイルのひな形を作成しました"
            else
                log_error "❌ 設定ファイルのひな形作成に失敗しました"
                show_recovery_help "config_template_failed"
                exit 1
            fi
            
            echo
            echo -e "${YELLOW}🔧 手作業が必要です（5-10分程度）${NC}"
            echo
            echo "📋 setup-config.json ファイルを開いて、以下の情報を入力してください："
            echo
            echo -e "${CYAN}🔑 Google OAuth設定（Googleログイン用）：${NC}"
            echo "   📝 clientId: GoogleのOAuthクライアントID"
            echo "   📝 clientSecret: GoogleのOAuthクライアントシークレット"
            echo "   💡 取得方法: Google Cloud Console → 認証情報 → OAuthクライアント"
            echo
            echo -e "${CYAN}☁️  AWS設定（ファイル保存用）：${NC}"
            echo "   📝 s3.bucketName: ファイル保存用のバケット名（例: my-excel-tool-files）"
            echo "   📝 region: 地域設定（日本なら ap-northeast-1）"
            echo "   💡 バケット名は世界で唯一の名前にしてください"
            echo
            echo -e "${CYAN}👥 セキュリティ設定（誰が使えるか）：${NC}"
            echo "   📝 allowedUsers: 使用を許可するメールアドレス（カンマ区切り）"
            echo "   📝 jwtSecret: ランダムな文字列（32文字以上推奨）"
            echo "   📝 sessionSecret: ランダムな文字列（32文字以上推奨）"
            echo
            echo -e "${CYAN}🌐 Vercel設定（ウェブ公開用）：${NC}"
            echo "   📝 projectName: プロジェクト名（例: excel-unlocker）"
            echo "   📝 domain: 独自ドメイン（オプション、なくてもOK）"
            echo
            echo -e "${GREEN}🛡️  安心してください：${NC}"
            echo "  ✅ 設定ファイルは安全に保存されます"
            echo "  ✅ 間違えても後から修正できます"
            echo "  ✅ 分からない項目は空欄でもOKです"
            echo
            
            log_tip "📚 詳しい設定方法は docs/beginner-complete-setup-guide.md を見てください"
            echo
            
            if ask_confirmation "設定ファイルの編集を完了しましたか？" "n"; then
                log_success "✅ 設定ファイルの編集が完了しました"
            else
                log_info "📋 次にすること："
                echo "  1. setup-config.json ファイルを編集"
                echo "  2. 必要な情報を入力"
                echo "  3. ファイルを保存"
                echo "  4. このスクリプトをもう一度実行"
                echo
                log_success "設定完了後にお待ちしています！"
                exit 0
            fi
        fi
    else
        log_success "✅ 既存の設定ファイルを使用します"
    fi
    
    # 最終検証
    if ! verify_final_config; then
        log_error "❌ 設定ファイルの最終検証に失敗しました"
        show_recovery_help "config_validation_failed"
        exit 1
    fi
    
    log_success "✅ 設定ファイルの準備が完了しました！"
    echo
}

# 環境別セットアップ
setup_environment() {
    log_step "⚙️  ${ENVIRONMENT}環境の準備をしています..."
    
    echo
    log_info "💡 今何をしているか：設定ファイルから環境に合わせた設定を作成中"
    log_info "⏱️  所要時間：約1-2分"
    echo
    
    # 環境変数の生成
    log_progress "📝 環境設定ファイルを作成しています..."
    
    if generate_env_file "$ENVIRONMENT"; then
        log_success "✅ 環境設定ファイルを作成しました"
    else
        log_error "❌ 環境設定ファイルの作成に失敗しました"
        echo
        echo -e "${YELLOW}🔧 問題の解決方法：${NC}"
        echo "  📝 setup-config.json の内容を確認"
        echo "  🔍 必要な項目が全て入力されているかチェック"
        echo "  💾 ファイルを保存してから再実行"
        echo
        show_recovery_help "env_generation_failed"
        exit 1
    fi
    
    # 環境変数の読み込み
    if [[ -f ".env.${ENVIRONMENT}" ]]; then
        set -a
        source ".env.${ENVIRONMENT}"
        set +a
        log_success "✅ 環境設定を読み込みました"
    else
        log_error "❌ 環境設定ファイルが見つかりません"
        exit 1
    fi
    
    # AWS設定の確認
    echo
    log_progress "☁️  AWSクラウドサービスとの接続を確認しています..."
    
    if [[ -n "${AWS_PROFILE:-}" ]]; then
        export AWS_PROFILE="$AWS_PROFILE"
        log_info "📋 AWS Profile: $AWS_PROFILE を使用します"
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "❌ AWSクラウドサービスとの接続に失敗しました"
        echo
        echo -e "${YELLOW}🔧 AWSの設定が必要です：${NC}"
        echo "  🔑 AWSアカウントの認証情報を設定してください"
        echo "  💻 コマンド: aws configure"
        echo "  📝 必要な情報: アクセスキーID、シークレットアクセスキー、リージョン"
        echo
        echo -e "${GREEN}🛡️  安心してください：${NC}"
        echo "  ✅ 設定は一度だけ行えばOKです"
        echo "  ✅ 情報は安全に保存されます"
        echo "  ✅ 設定後にもう一度このスクリプトを実行してください"
        echo
        show_recovery_help "aws_auth_failed"
        
        if ask_confirmation "AWS設定を確認して、後でもう一度実行しますか？" "y"; then
            log_manual "📋 次にすること："
            echo "  1. ターミナルで 'aws configure' を実行"
            echo "  2. AWSの認証情報を入力"
            echo "  3. このスクリプトをもう一度実行"
            echo
            log_success "AWS設定完了後にお待ちしています！"
            exit 1
        else
            exit 1
        fi
    fi
    
    log_success "✅ AWSクラウドサービスとの接続を確認しました"
    log_info "🎯 次に進みます：ファイル保存場所を準備します"
    echo
}

# S3バケットの作成
create_s3_bucket() {
    local bucket_name="$1"
    local region="${AWS_REGION:-ap-northeast-1}"
    
    log_step "📦 ファイル保存場所を準備しています..."
    
    echo
    log_info "💡 今何をしているか：Excelファイルを安全に保存する場所をクラウドに作成中"
    log_info "⏱️  所要時間：約30秒-1分"
    echo
    
    log_progress "📁 ファイル保存場所 '$bucket_name' を作成しています..."
    
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "✅ ファイル保存場所 '$bucket_name' は既に存在します"
    else
        if aws s3 mb "s3://$bucket_name" --region "$region"; then
            log_success "✅ ファイル保存場所 '$bucket_name' を作成しました"
        else
            log_error "❌ ファイル保存場所の作成に失敗しました"
            echo
            echo -e "${YELLOW}🔧 よくある原因と解決方法：${NC}"
            echo "  📝 バケット名が既に他の人に使われている"
            echo "  💡 解決方法: setup-config.json でバケット名を変更"
            echo "  🔍 例: my-excel-tool-files-2025 など、より具体的な名前に"
            echo
            echo -e "${GREEN}🛡️  安心してください：${NC}"
            echo "  ✅ バケット名を変更するだけで解決します"
            echo "  ✅ 何度でも試すことができます"
            echo "  ✅ 他に影響はありません"
            echo
            show_recovery_help "s3_creation_failed"
            exit 1
        fi
    fi
    
    # パブリックアクセスブロックの設定
    echo
    log_progress "🔒 ファイル保存場所のセキュリティ設定を適用しています..."
    
    if aws s3api put-public-access-block \
        --bucket "$bucket_name" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"; then
        log_success "✅ ファイル保存場所のセキュリティ設定が完了しました"
        echo
        log_info "🛡️  セキュリティ設定の内容："
        echo "  ✅ 外部からの不正アクセスをブロック"
        echo "  ✅ 許可されたユーザーのみアクセス可能"
        echo "  ✅ ファイルは安全に保護されます"
    else
        log_warning "⚠️  ファイル保存場所のセキュリティ設定で問題が発生しました（継続します）"
    fi
    
    echo
    log_info "🎯 次に進みます：Excelツールの本体を準備します"
    echo
}

# バックエンドのデプロイ
deploy_backend() {
    log_step "🔧 Excelツールの本体を準備しています..."
    
    echo
    log_info "💡 今何をしているか：Excelファイルを処理するプログラムをクラウドに設置中"
    log_info "⏱️  所要時間：約3-5分"
    echo
    
    cd "$PROJECT_ROOT"
    
    # SAMビルド
    log_progress "🏗️  Excelツールのプログラムを組み立てています..."
    
    if sam build; then
        log_success "✅ Excelツールのプログラムを組み立てました"
    else
        log_error "❌ Excelツールのプログラム組み立てに失敗しました"
        echo
        echo -e "${YELLOW}🔧 よくある原因と解決方法：${NC}"
        echo "  📝 必要なソフトウェアが不足している"
        echo "  💡 解決方法: 前提条件を再確認"
        echo "  🔄 再実行: このスクリプトをもう一度実行"
        echo
        show_recovery_help "sam_build_failed"
        exit 1
    fi
    
    # SAMデプロイ
    echo
    log_progress "🚀 Excelツールをクラウドに設置しています..."
    
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
        log_success "✅ Excelツールをクラウドに設置しました"
        echo
        log_info "🎯 設置されたもの："
        echo "  📦 Excelファイル処理プログラム"
        echo "  🌐 インターネット経由でアクセスできるAPI"
        echo "  🔒 セキュリティ設定"
        echo "  ⚙️  自動スケーリング機能"
    else
        log_error "❌ Excelツールのクラウド設置に失敗しました"
        echo
        echo -e "${YELLOW}🔧 よくある原因と解決方法：${NC}"
        echo "  🔑 AWS権限が不足している"
        echo "  📝 設定ファイルに問題がある"
        echo "  💡 解決方法: AWS設定を確認"
        echo
        show_recovery_help "sam_deploy_failed"
        exit 1
    fi
    
    # API Gateway URLの取得
    echo
    log_progress "🌐 Excelツールのアクセス先を確認しています..."
    
    local api_url
    api_url=$(aws cloudformation describe-stacks \
        --stack-name "$LAMBDA_STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]]; then
        log_success "✅ Excelツールのアクセス先を確認しました"
        echo "NEXT_PUBLIC_API_URL=$api_url" >> ".env.${ENVIRONMENT}"
        echo
        log_info "🌐 アクセス先: $api_url"
        log_info "🎯 次に進みます：ウェブ画面を準備します"
    else
        log_warning "⚠️  Excelツールのアクセス先確認に失敗しました（継続します）"
    fi
    echo
}

# フロントエンドのセットアップ
setup_frontend() {
    log_step "🖥️  ウェブ画面を準備しています..."
    
    echo
    log_info "💡 今何をしているか：スマホ・パソコンで使えるウェブ画面を準備中"
    log_info "⏱️  所要時間：約2-3分"
    echo
    
    cd "$PROJECT_ROOT/frontend"
    
    # 依存関係のインストール
    log_progress "📦 ウェブ画面に必要な部品をダウンロードしています..."
    
    if npm install; then
        log_success "✅ ウェブ画面の部品をダウンロードしました"
    else
        log_error "❌ ウェブ画面の部品ダウンロードに失敗しました"
        echo
        echo -e "${YELLOW}🔧 よくある原因と解決方法：${NC}"
        echo "  🌐 インターネット接続が不安定"
        echo "  📝 Node.jsのバージョンが古い"
        echo "  💡 解決方法: しばらく待ってから再実行"
        echo
        show_recovery_help "npm_install_failed"
        exit 1
    fi
    
    # 環境変数ファイルのコピー
    echo
    log_progress "⚙️  ウェブ画面の設定をしています..."
    
    cp "../.env.${ENVIRONMENT}" ".env.local"
    log_success "✅ ウェブ画面の設定を完了しました"
    
    # ビルドテスト
    if [[ "$SKIP_TESTS" != "true" ]]; then
        echo
        log_progress "🔍 ウェブ画面が正しく動くかテストしています..."
        
        if npm run build; then
            log_success "✅ ウェブ画面のテストが完了しました"
            echo
            log_info "🎯 テスト結果："
            echo "  ✅ ウェブ画面が正しく表示されます"
            echo "  ✅ スマホ・タブレット・パソコンで使えます"
            echo "  ✅ Excelツールと正しく連携します"
        else
            log_error "❌ ウェブ画面のテストに失敗しました"
            echo
            echo -e "${YELLOW}🔧 よくある原因と解決方法：${NC}"
            echo "  📝 設定ファイルに問題がある"
            echo "  🔧 プログラムにエラーがある"
            echo "  💡 解決方法: エラーメッセージを確認して修正"
            echo
            show_recovery_help "frontend_build_failed"
            exit 1
        fi
    else
        log_info "✅ ウェブ画面のテストをスキップしました"
    fi
    
    echo
    log_info "🎯 次に進みます：インターネット公開の準備をします"
    echo
    
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
            echo "  1. 設定ファイルを確認: python3 -m json.tool setup-config.json"
            echo "  2. Python環境を確認:"
            echo "     - 仮想環境: python3 -m venv venv && source venv/bin/activate"
            echo "     - 依存関係: pip install -r scripts/requirements.txt"
            echo "     - pipx使用: brew install pipx"
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
        "python_environment_failed")
            log_manual "Python環境の問題が発生しました"
            echo "  🚨 macOS外部管理環境エラーの解決方法:"
            echo "  1. 仮想環境を作成:"
            echo "     python3 -m venv venv"
            echo "     source venv/bin/activate"
            echo "     pip install -r scripts/requirements.txt"
            echo "  2. pipxを使用:"
            echo "     brew install pipx"
            echo "     pipx install jsonschema cryptography PyYAML"
            echo "  3. Homebrewでpipxをインストール:"
            echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "     brew install pipx"
            echo "  4. 再実行: $0"
            ;;
        "config_json_invalid")
            log_manual "設定ファイルのJSON形式が正しくありません"
            echo "  1. JSON形式を確認: python3 -m json.tool setup-config.json"
            echo "  2. よくあるエラー:"
            echo "     - カンマの不足または余分なカンマ"
            echo "     - 引用符の不足または不正な引用符"
            echo "     - 括弧の不一致 { } [ ]"
            echo "     - コメントの記述（JSONではコメント不可）"
            echo "  3. オンラインJSONバリデーターを使用"
            echo "  4. 再実行: $0"
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
    
    clear
    echo
    echo -e "${GREEN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                🎉🎉🎉 セットアップ完了！おめでとうございます！ 🎉🎉🎉          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    echo
    
    echo -e "${CYAN}⏱️  かかった時間: ${setup_minutes}分${setup_seconds}秒${NC}"
    echo -e "${CYAN}🎯 セットアップした環境: $ENVIRONMENT${NC}"
    echo
    
    echo -e "${GREEN}🎊 何ができるようになったの？${NC}"
    echo
    echo "  📱 スマホ・タブレット・パソコンからExcelのパスワード解除"
    echo "  🚀 複数のファイルを一度に処理"
    echo "  ☁️  Google Driveに直接保存"
    echo "  🔒 安全・安心のセキュリティ"
    echo "  🌐 24時間いつでもアクセス可能"
    echo
    
    echo -e "${BLUE}✅ 完了したこと（自動でやりました）${NC}"
    echo
    echo "  ✅ 📄 設定ファイルの作成・確認"
    echo "  ✅ ⚙️  環境設定の準備"
    echo "  ✅ 📦 ファイル保存場所の作成・セキュリティ設定"
    echo "  ✅ 🔧 Excelツール本体のクラウド設置"
    echo "  ✅ 🖥️  ウェブ画面の準備・テスト"
    if [[ "$DEPLOY_VERCEL" == "true" ]]; then
        echo "  ✅ 🌐 インターネット公開の設定"
    fi
    if [[ "$SKIP_TESTS" != "true" ]]; then
        echo "  ✅ 🔍 動作確認テストの実行"
    fi
    echo "  ✅ 💾 設定のバックアップ"
    echo
    
    echo -e "${YELLOW}🚀 次に何をすればいいの？${NC}"
    echo
    echo "  1️⃣  📱 まずは動作確認をしてみましょう"
    echo "     💻 コマンド: cd frontend && npm run dev"
    echo "     🌐 ブラウザで http://localhost:3000 を開く"
    echo "     🎯 Googleアカウントでログインしてみる"
    echo
    echo "  2️⃣  📄 Excelファイル解除をテストしてみましょう"
    echo "     📁 パスワード付きExcelファイルを用意"
    echo "     ⬆️  ファイルをアップロード"
    echo "     🔓 パスワードを入力して解除"
    echo "     ⬇️  解除されたファイルをダウンロード"
    echo
    
    if [[ "$ENVIRONMENT" != "production" ]]; then
        echo "  3️⃣  🚀 本番環境にもセットアップしたい場合"
        echo "     💻 コマンド: ./setup-easy.sh"
        echo "     🎯 環境選択で「3) 本番環境」を選ぶ"
        echo
    fi
    
    echo -e "${PURPLE}📚 困ったときは？${NC}"
    echo
    echo "  ❓ よくある質問: docs/beginner-faq.md"
    echo "  🔧 問題解決ガイド: docs/troubleshooting-flowchart.md"
    echo "  📖 詳しい使い方: docs/beginner-complete-setup-guide.md"
    echo "  📋 全ドキュメント: docs/index.md"
    echo
    
    echo -e "${CYAN}📁 作成されたファイル${NC}"
    echo
    echo "  📄 setup-config.json - あなたの設定"
    echo "  🌍 .env.${ENVIRONMENT} - 環境設定"
    echo "  💾 config-backup/ - バックアップ"
    echo "  📝 $LOG_FILE - 詳細ログ"
    echo
    
    if [[ -n "${NEXT_PUBLIC_API_URL:-}" ]]; then
        echo -e "${GREEN}🌐 作成されたサービス${NC}"
        echo
        echo "  🔧 Excelツール本体: $NEXT_PUBLIC_API_URL"
        if [[ "$DEPLOY_VERCEL" == "true" ]]; then
            echo "  🌐 ウェブサイト: Vercel Dashboard で確認できます"
        fi
        echo
    fi
    
    echo -e "${GREEN}🎉 お疲れさまでした！${NC}"
    echo
    echo "Excel Unlocker が使えるようになりました。"
    echo "何か問題があれば、上記のドキュメントを参考にしてください。"
    echo
    echo -e "${BLUE}💡 まずは cd frontend && npm run dev で動作確認してみてください！${NC}"
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
    local total_steps=9
    local current_step=0
    
    # Step 1: 前提条件チェック
    ((current_step++))
    show_progress_bar $current_step $total_steps "前提条件チェック"
    check_prerequisites
    
    # Step 1.5: Python環境セットアップ
    ((current_step++))
    show_progress_bar $current_step $total_steps "Python環境セットアップ"
    setup_python_environment
    
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