#!/bin/bash

# 設定ファイル管理スクリプト（Python環境に依存しない基本版）
# Python環境の問題が発生した場合のフォールバック機能を提供

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ログ関数
log_info() {
    echo -e "${BLUE}📍${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# スクリプトディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 設定ファイルパス
SETUP_CONFIG="$PROJECT_ROOT/setup-config.json"
EXAMPLE_CONFIG="$PROJECT_ROOT/setup-config.example.json"
SCHEMA_CONFIG="$PROJECT_ROOT/config-schema.json"

# 初期化（テンプレートから設定ファイルを作成）
init_config() {
    log_info "設定ファイルのテンプレートを作成しています..."
    
    if [[ -f "$SETUP_CONFIG" ]]; then
        log_warning "設定ファイルが既に存在します: $SETUP_CONFIG"
        echo -n "上書きしますか？ (y/N): "
        read -r response
        if [[ "$response" != "y" && "$response" != "Y" ]]; then
            log_info "作成をキャンセルしました"
            return 0
        fi
    fi
    
    # テンプレートファイルの確認
    if [[ -f "$EXAMPLE_CONFIG" ]]; then
        log_info "既存のテンプレートファイルを使用します"
        cp "$EXAMPLE_CONFIG" "$SETUP_CONFIG"
    else
        log_info "基本的な設定ファイル構造を作成します"
        create_basic_config
    fi
    
    if [[ -f "$SETUP_CONFIG" ]]; then
        log_success "設定ファイルを作成しました: $SETUP_CONFIG"
        log_info "📝 次にすること："
        echo "  1. $SETUP_CONFIG を開いて編集"
        echo "  2. YOUR_... で始まる項目を実際の値に変更"
        echo "  3. メールアドレスを実際のアドレスに変更"
        echo "  4. ファイルを保存"
        return 0
    else
        log_error "設定ファイルの作成に失敗しました"
        return 1
    fi
}

# 基本的な設定ファイル構造を作成
create_basic_config() {
    cat > "$SETUP_CONFIG" << 'EOF'
{
  "environments": {
    "development": {
      "aws": {
        "region": "ap-northeast-1",
        "s3": {
          "bucketName": "YOUR_S3_BUCKET_NAME_DEV",
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
}

# 設定ファイルの基本検証
validate_config() {
    log_info "設定ファイルを検証しています..."
    
    if [[ ! -f "$SETUP_CONFIG" ]]; then
        log_error "設定ファイルが見つかりません: $SETUP_CONFIG"
        return 1
    fi
    
    # JSON形式の検証
    if ! python3 -m json.tool "$SETUP_CONFIG" > /dev/null 2>&1; then
        log_error "設定ファイルのJSON形式が正しくありません"
        echo
        echo "🔧 JSON形式エラーの確認方法："
        echo "  python3 -m json.tool $SETUP_CONFIG"
        return 1
    fi
    
    log_success "JSON形式は正常です"
    
    # 基本的な内容検証
    local errors=0
    
    # 必須セクションの確認
    if ! grep -q '"environments"' "$SETUP_CONFIG"; then
        log_error "environments セクションが見つかりません"
        errors=$((errors + 1))
    fi
    
    # 各環境の確認
    for env in "development" "staging" "production"; do
        if ! grep -q "\"$env\"" "$SETUP_CONFIG"; then
            log_error "$env 環境の設定が見つかりません"
            errors=$((errors + 1))
        fi
    done
    
    # プレースホルダーの確認
    local placeholders=(
        "YOUR_S3_BUCKET_NAME"
        "YOUR_GOOGLE_CLIENT_ID"
        "YOUR_GOOGLE_CLIENT_SECRET"
        "YOUR_JWT_SECRET"
        "YOUR_SESSION_SECRET"
        "your-email@example.com"
    )
    
    for placeholder in "${placeholders[@]}"; do
        if grep -q "$placeholder" "$SETUP_CONFIG"; then
            log_warning "プレースホルダーが残っています: $placeholder"
            errors=$((errors + 1))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log_success "設定ファイルの検証が完了しました"
        return 0
    else
        log_error "$errors 個の問題が見つかりました"
        echo
        echo "🔧 修正が必要な項目："
        echo "  📝 プレースホルダー（YOUR_...）を実際の値に変更"
        echo "  📝 メールアドレスを実際のアドレスに変更"
        echo "  📝 必須セクションの追加"
        return 1
    fi
}

# 設定のバックアップ
backup_config() {
    log_info "設定ファイルをバックアップしています..."
    
    if [[ ! -f "$SETUP_CONFIG" ]]; then
        log_error "設定ファイルが見つかりません: $SETUP_CONFIG"
        return 1
    fi
    
    local backup_dir="$PROJECT_ROOT/config-backup"
    mkdir -p "$backup_dir"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/setup-config.${timestamp}.json"
    
    cp "$SETUP_CONFIG" "$backup_file"
    
    if [[ -f "$backup_file" ]]; then
        log_success "バックアップを作成しました: $backup_file"
        return 0
    else
        log_error "バックアップの作成に失敗しました"
        return 1
    fi
}

# 使用方法の表示
show_usage() {
    echo "使用方法: $0 <command>"
    echo
    echo "利用可能なコマンド:"
    echo "  init      - テンプレートから設定ファイルを作成"
    echo "  validate  - 設定ファイルの検証"
    echo "  backup    - 設定ファイルのバックアップ"
    echo "  help      - このヘルプを表示"
    echo
    echo "例:"
    echo "  $0 init"
    echo "  $0 validate"
    echo "  $0 backup"
}

# メイン処理
main() {
    local command="${1:-help}"
    
    case "$command" in
        "init")
            init_config
            ;;
        "validate")
            validate_config
            ;;
        "backup")
            backup_config
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "不明なコマンド: $command"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# スクリプトが直接実行された場合
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi