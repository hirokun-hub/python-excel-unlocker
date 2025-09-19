#!/bin/bash

# 緊急時ユーザー管理スクリプト
# セキュリティインシデント発生時の緊急対応用

set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/emergency-user-management.log"
AWS_REGION="ap-northeast-1"
SSM_PARAMETER_NAME="/excel-unlocker/allowed-users"

# 緊急時連絡先
EMERGENCY_CONTACTS="hironomac2025@gmail.com"
ADMIN_EMAIL="hironomac2025@gmail.com"

# ログ出力関数
emergency_log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [EMERGENCY] [$level] $message" | tee -a "$LOG_FILE"
}

# エラーハンドリング
emergency_error() {
    emergency_log "ERROR" "$1"
    send_emergency_alert "ERROR" "$1"
    exit 1
}

# 緊急アラートの送信
send_emergency_alert() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # CloudWatch Logsに緊急ログを送信
    aws logs put-log-events \
        --log-group-name "/excel-unlocker/emergency" \
        --log-stream-name "emergency-$(date +%Y%m%d)" \
        --log-events timestamp=$(date +%s)000,message="[EMERGENCY] $level: $message" \
        --region "$AWS_REGION" 2>/dev/null || true
    
    emergency_log "ALERT" "緊急アラート送信: $level - $message"
}

# 使用方法の表示
show_emergency_usage() {
    cat << EOF
緊急時ユーザー管理スクリプト - Secure Excel Unlock

⚠️  このスクリプトは緊急時のみ使用してください ⚠️

使用方法:
    $0 <command> [options]

緊急コマンド:
    lockdown                       全ユーザーアクセスを即座に停止
    disable-user <email>           特定ユーザーを即座に無効化
    admin-only                     管理者のみアクセス許可
    restore-emergency <backup>     緊急時バックアップから復元
    status                         現在の緊急時状態を確認
    unlock                         緊急ロックダウンを解除

オプション:
    --environment <env>            対象環境 (development|staging|production)
    --reason <reason>              緊急対応の理由
    --force                        確認プロンプトをスキップ
    --help                         このヘルプを表示

例:
    $0 lockdown --environment production --reason "security-incident"
    $0 disable-user "suspicious@example.com" --environment production --reason "unauthorized-access"
    $0 admin-only --environment production --force

⚠️  重要: 全ての緊急操作は自動的にログ記録され、アラートが送信されます

EOF
}

# 確認プロンプト
confirm_emergency_action() {
    local action="$1"
    local env="$2"
    local force="$3"
    
    if [[ "$force" == "true" ]]; then
        return 0
    fi
    
    echo "⚠️  緊急操作の確認 ⚠️"
    echo "操作: $action"
    echo "環境: $env"
    echo "時刻: $(date)"
    echo
    read -p "この緊急操作を実行しますか？ (yes/no): " -r
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        emergency_log "INFO" "緊急操作がキャンセルされました: $action"
        exit 0
    fi
}

# 緊急バックアップの作成
create_emergency_backup() {
    local env="$1"
    local reason="$2"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${SCRIPT_DIR}/../backups/emergency/emergency_backup_${env}_${timestamp}.json"
    
    mkdir -p "$(dirname "$backup_file")"
    
    emergency_log "INFO" "緊急バックアップを作成中: $backup_file"
    
    local current_users
    current_users=$(aws ssm get-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "")
    
    cat > "$backup_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$env",
    "backup_type": "emergency",
    "reason": "$reason",
    "operator": "$(whoami)",
    "allowed_users": "$current_users",
    "lambda_functions": {
$(get_lambda_env_backup "$env" | sed 's/^/        /')
    }
}
EOF
    
    emergency_log "INFO" "緊急バックアップ作成完了: $backup_file"
    echo "$backup_file"
}

# Lambda関数の環境変数バックアップ
get_lambda_env_backup() {
    local env="$1"
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    local first=true
    for function_name in "${functions[@]}"; do
        if [[ "$first" == "false" ]]; then
            echo ","
        fi
        first=false
        
        local lambda_env
        lambda_env=$(aws lambda get-function-configuration \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Environment.Variables" \
            --output json 2>/dev/null || echo "{}")
        
        echo "\"$function_name\": $lambda_env"
    done
}

# 全ユーザーアクセス停止（ロックダウン）
emergency_lockdown() {
    local env="$1"
    local reason="$2"
    local force="$3"
    
    confirm_emergency_action "LOCKDOWN - 全ユーザーアクセス停止" "$env" "$force"
    
    emergency_log "CRITICAL" "緊急ロックダウン開始: $env (理由: $reason)"
    send_emergency_alert "CRITICAL" "緊急ロックダウン開始: $env"
    
    # 緊急バックアップ作成
    local backup_file
    backup_file=$(create_emergency_backup "$env" "$reason")
    
    # 空のユーザーリストに設定（全アクセス拒否）
    emergency_log "INFO" "Parameter Store を空に設定中"
    aws ssm put-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --value "" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    # Lambda関数の環境変数を更新
    update_lambda_emergency "$env" ""
    
    # 緊急状態フラグを設定
    aws ssm put-parameter \
        --name "/excel-unlocker/emergency-status" \
        --value "LOCKDOWN" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    emergency_log "CRITICAL" "緊急ロックダウン完了: 全ユーザーアクセス停止"
    send_emergency_alert "CRITICAL" "緊急ロックダウン完了: 全ユーザーアクセス停止"
    
    echo "✅ 緊急ロックダウン完了"
    echo "📁 バックアップファイル: $backup_file"
    echo "🔓 解除コマンド: $0 unlock --environment $env"
}

# 特定ユーザーの緊急無効化
emergency_disable_user() {
    local email="$1"
    local env="$2"
    local reason="$3"
    local force="$4"
    
    confirm_emergency_action "ユーザー無効化: $email" "$env" "$force"
    
    emergency_log "CRITICAL" "緊急ユーザー無効化開始: $email (環境: $env, 理由: $reason)"
    send_emergency_alert "CRITICAL" "緊急ユーザー無効化: $email"
    
    # 緊急バックアップ作成
    create_emergency_backup "$env" "disable-user-$email"
    
    # 現在のユーザーリストを取得
    local current_users
    current_users=$(aws ssm get-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "")
    
    # 対象ユーザーを削除
    local new_users
    new_users=$(echo "$current_users" | sed "s/${email},//g" | sed "s/,${email}//g" | sed "s/^${email}$//g")
    
    # Parameter Store更新
    aws ssm put-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --value "$new_users" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    # Lambda関数更新
    update_lambda_emergency "$env" "$new_users"
    
    emergency_log "CRITICAL" "緊急ユーザー無効化完了: $email"
    send_emergency_alert "INFO" "緊急ユーザー無効化完了: $email"
    
    echo "✅ ユーザー無効化完了: $email"
}

# 管理者のみアクセス許可
emergency_admin_only() {
    local env="$1"
    local reason="$2"
    local force="$3"
    
    confirm_emergency_action "管理者のみアクセス許可" "$env" "$force"
    
    emergency_log "CRITICAL" "管理者のみアクセス設定開始: $env (理由: $reason)"
    send_emergency_alert "CRITICAL" "管理者のみアクセス設定: $env"
    
    # 緊急バックアップ作成
    create_emergency_backup "$env" "$reason"
    
    # 管理者のみに設定
    aws ssm put-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --value "$ADMIN_EMAIL" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    # Lambda関数更新
    update_lambda_emergency "$env" "$ADMIN_EMAIL"
    
    # 緊急状態フラグを設定
    aws ssm put-parameter \
        --name "/excel-unlocker/emergency-status" \
        --value "ADMIN_ONLY" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    emergency_log "CRITICAL" "管理者のみアクセス設定完了"
    send_emergency_alert "INFO" "管理者のみアクセス設定完了"
    
    echo "✅ 管理者のみアクセス設定完了"
    echo "👤 許可ユーザー: $ADMIN_EMAIL"
}

# Lambda関数の緊急更新
update_lambda_emergency() {
    local env="$1"
    local new_users="$2"
    
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    for function_name in "${functions[@]}"; do
        emergency_log "INFO" "Lambda関数緊急更新中: $function_name"
        
        # 現在の環境変数を取得
        local current_env
        current_env=$(aws lambda get-function-configuration \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Environment.Variables" \
            --output json 2>/dev/null) || {
            emergency_log "WARN" "Lambda関数が見つかりません: $function_name"
            continue
        }
        
        # ALLOWED_USERSを更新
        local updated_env
        updated_env=$(echo "$current_env" | jq --arg users "$new_users" '.ALLOWED_USERS = $users')
        
        # Lambda関数を更新
        aws lambda update-function-configuration \
            --function-name "$function_name" \
            --environment "Variables=$updated_env" \
            --region "$AWS_REGION" > /dev/null
        
        emergency_log "INFO" "Lambda関数緊急更新完了: $function_name"
    done
}

# 緊急状態の確認
check_emergency_status() {
    local env="$1"
    
    echo "🔍 緊急状態確認: $env"
    echo "時刻: $(date)"
    echo
    
    # 緊急状態フラグの確認
    local emergency_status
    emergency_status=$(aws ssm get-parameter \
        --name "/excel-unlocker/emergency-status" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "NORMAL")
    
    echo "緊急状態: $emergency_status"
    
    # 現在のユーザー設定確認
    local current_users
    current_users=$(aws ssm get-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$current_users" ]]; then
        echo "⚠️  ユーザー設定: 全アクセス拒否（ロックダウン状態）"
    elif [[ "$current_users" == "$ADMIN_EMAIL" ]]; then
        echo "⚠️  ユーザー設定: 管理者のみ ($ADMIN_EMAIL)"
    else
        local user_count
        user_count=$(echo "$current_users" | tr ',' '\n' | wc -l)
        echo "✅ ユーザー設定: 通常運用 ($user_count ユーザー)"
    fi
    
    # 最新の緊急ログ確認
    echo
    echo "📋 最新の緊急ログ:"
    tail -5 "$LOG_FILE" 2>/dev/null || echo "ログファイルが見つかりません"
}

# 緊急ロックダウンの解除
emergency_unlock() {
    local env="$1"
    local force="$2"
    
    confirm_emergency_action "緊急ロックダウン解除" "$env" "$force"
    
    emergency_log "INFO" "緊急ロックダウン解除開始: $env"
    
    # 最新のバックアップファイルを検索
    local latest_backup
    latest_backup=$(ls -t "${SCRIPT_DIR}/../backups/emergency/emergency_backup_${env}_"*.json 2>/dev/null | head -1)
    
    if [[ -z "$latest_backup" ]]; then
        emergency_error "緊急バックアップファイルが見つかりません"
    fi
    
    emergency_log "INFO" "バックアップから復元中: $latest_backup"
    
    # バックアップからユーザーリストを復元
    local backup_users
    backup_users=$(jq -r '.allowed_users' "$latest_backup")
    
    # Parameter Store復元
    aws ssm put-parameter \
        --name "$SSM_PARAMETER_NAME" \
        --value "$backup_users" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    # Lambda関数復元
    update_lambda_emergency "$env" "$backup_users"
    
    # 緊急状態フラグを解除
    aws ssm put-parameter \
        --name "/excel-unlocker/emergency-status" \
        --value "NORMAL" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    emergency_log "INFO" "緊急ロックダウン解除完了: $env"
    send_emergency_alert "INFO" "緊急ロックダウン解除完了: $env"
    
    echo "✅ 緊急ロックダウン解除完了"
    echo "📁 使用したバックアップ: $latest_backup"
    echo "👥 復元されたユーザー数: $(echo "$backup_users" | tr ',' '\n' | wc -l)"
}

# メイン処理
main() {
    local command=""
    local email=""
    local environment="production"
    local reason=""
    local force="false"
    
    # 引数の解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            lockdown|disable-user|admin-only|restore-emergency|status|unlock)
                command="$1"
                if [[ "$command" == "disable-user" ]] && [[ $# -gt 1 ]]; then
                    shift
                    email="$1"
                fi
                ;;
            --environment)
                shift
                environment="$1"
                ;;
            --reason)
                shift
                reason="$1"
                ;;
            --force)
                force="true"
                ;;
            --help)
                show_emergency_usage
                exit 0
                ;;
            *)
                emergency_error "不明なオプション: $1"
                ;;
        esac
        shift
    done
    
    # ログディレクトリの作成
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # AWS CLIの確認
    if ! command -v aws &> /dev/null; then
        emergency_error "AWS CLIがインストールされていません"
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        emergency_error "AWS認証が設定されていません"
    fi
    
    # コマンドの実行
    case "$command" in
        "lockdown")
            [[ -z "$reason" ]] && reason="emergency-lockdown"
            emergency_lockdown "$environment" "$reason" "$force"
            ;;
        "disable-user")
            [[ -z "$email" ]] && emergency_error "メールアドレスが指定されていません"
            [[ -z "$reason" ]] && reason="security-concern"
            emergency_disable_user "$email" "$environment" "$reason" "$force"
            ;;
        "admin-only")
            [[ -z "$reason" ]] && reason="admin-only-access"
            emergency_admin_only "$environment" "$reason" "$force"
            ;;
        "status")
            check_emergency_status "$environment"
            ;;
        "unlock")
            emergency_unlock "$environment" "$force"
            ;;
        "")
            show_emergency_usage
            exit 1
            ;;
        *)
            emergency_error "不明なコマンド: $command"
            ;;
    esac
}

# スクリプト実行
main "$@"