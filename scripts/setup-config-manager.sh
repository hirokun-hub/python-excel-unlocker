#!/bin/bash

# 設定情報管理システム - Bashラッパースクリプト
# Python設定管理スクリプトの便利なラッパー

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_MANAGER="$SCRIPT_DIR/config_manager.py"

# 色付きメッセージ用の関数
print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 依存関係のチェック
check_dependencies() {
    print_info "依存関係をチェックしています..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3が見つかりません。インストールしてください。"
        exit 1
    fi
    
    # 必要なPythonパッケージのインストール
    if ! python3 -c "import jsonschema, cryptography" &> /dev/null; then
        print_info "必要なPythonパッケージをインストールしています..."
        pip3 install -r "$SCRIPT_DIR/requirements.txt" || {
            print_error "依存関係のインストールに失敗しました"
            exit 1
        }
    fi
    
    print_success "依存関係のチェックが完了しました"
}

# 設定ファイルの初期化
init_config() {
    print_info "設定ファイルを初期化しています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "setup-config.json" ]]; then
        print_warning "設定ファイルが既に存在します"
        read -p "上書きしますか？ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "初期化をキャンセルしました"
            return 0
        fi
    fi
    
    python3 "$CONFIG_MANAGER" create
    
    print_success "設定ファイルの初期化が完了しました"
    print_warning "setup-config.json を編集して、機密情報を設定してください"
}

# 設定ファイルの検証
validate_config() {
    print_info "設定ファイルを検証しています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "setup-config.json" ]]; then
        print_error "設定ファイルが見つかりません。'init' コマンドで作成してください。"
        exit 1
    fi
    
    python3 "$CONFIG_MANAGER" validate
}

# 環境変数の生成
generate_env() {
    local environment="$1"
    local format="${2:-bash}"
    local output_file="${3:-}"
    
    print_info "${environment}環境の環境変数を生成しています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "setup-config.json" ]]; then
        print_error "設定ファイルが見つかりません。'init' コマンドで作成してください。"
        exit 1
    fi
    
    if [[ -n "$output_file" ]]; then
        python3 "$CONFIG_MANAGER" generate-env "$environment" --format "$format" --output "$output_file"
        print_success "環境変数を $output_file に出力しました"
    else
        python3 "$CONFIG_MANAGER" generate-env "$environment" --format "$format"
    fi
}

# 設定ファイルのバックアップ
backup_config() {
    print_info "設定ファイルをバックアップしています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "setup-config.json" ]]; then
        print_error "設定ファイルが見つかりません。"
        exit 1
    fi
    
    python3 "$CONFIG_MANAGER" backup
}

# 設定ファイルの暗号化
encrypt_config() {
    print_info "設定ファイルを暗号化しています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "setup-config.json" ]]; then
        print_error "設定ファイルが見つかりません。"
        exit 1
    fi
    
    python3 "$CONFIG_MANAGER" encrypt
    print_warning "暗号化キー (.config-encryption-key) を安全に保管してください"
}

# 設定ファイルの復号化
decrypt_config() {
    local encrypted_file="$1"
    
    print_info "設定ファイルを復号化しています..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f "$encrypted_file" ]]; then
        print_error "暗号化ファイルが見つかりません: $encrypted_file"
        exit 1
    fi
    
    python3 "$CONFIG_MANAGER" decrypt "$encrypted_file"
}

# 環境別設定の自動適用
apply_env_config() {
    local environment="$1"
    
    print_info "${environment}環境の設定を適用しています..."
    
    # 環境変数ファイルの生成
    local env_file=".env.${environment}"
    generate_env "$environment" "dotenv" "$env_file"
    
    # AWS SAM設定の更新
    if [[ -f "samconfig.toml" ]]; then
        print_info "SAM設定を更新しています..."
        # samconfig.tomlの環境別パラメータを更新
        # （実装は環境に応じてカスタマイズ）
    fi
    
    print_success "${environment}環境の設定適用が完了しました"
}

# 使用方法の表示
show_usage() {
    cat << EOF
設定情報管理システム

使用方法:
  $0 <command> [options]

コマンド:
  init                    設定ファイルの初期化
  validate               設定ファイルの検証
  generate-env <env>     環境変数の生成 (development|staging|production)
  backup                 設定ファイルのバックアップ
  encrypt                設定ファイルの暗号化
  decrypt <file>         設定ファイルの復号化
  apply <env>            環境別設定の自動適用
  help                   このヘルプを表示

例:
  $0 init                                    # 設定ファイルの初期化
  $0 validate                                # 設定ファイルの検証
  $0 generate-env development                # 開発環境の環境変数を表示
  $0 generate-env production bash prod.env  # 本番環境の環境変数をファイル出力
  $0 backup                                  # 設定ファイルのバックアップ
  $0 encrypt                                 # 設定ファイルの暗号化
  $0 apply staging                           # ステージング環境設定の適用

EOF
}

# メイン処理
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    # 依存関係のチェック（helpコマンド以外）
    if [[ "$command" != "help" ]]; then
        check_dependencies
    fi
    
    case "$command" in
        "init")
            init_config
            ;;
        "validate")
            validate_config
            ;;
        "generate-env")
            if [[ $# -lt 1 ]]; then
                print_error "環境名を指定してください (development|staging|production)"
                exit 1
            fi
            generate_env "$@"
            ;;
        "backup")
            backup_config
            ;;
        "encrypt")
            encrypt_config
            ;;
        "decrypt")
            if [[ $# -lt 1 ]]; then
                print_error "暗号化ファイルのパスを指定してください"
                exit 1
            fi
            decrypt_config "$1"
            ;;
        "apply")
            if [[ $# -lt 1 ]]; then
                print_error "環境名を指定してください (development|staging|production)"
                exit 1
            fi
            apply_env_config "$1"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "不明なコマンド: $command"
            show_usage
            exit 1
            ;;
    esac
}

# スクリプトが直接実行された場合のみmain関数を呼び出す
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi