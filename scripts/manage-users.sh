#!/bin/bash

# ユーザー管理自動化スクリプト
# Secure Excel Unlockアプリケーションのユーザーアクセス権限を管理

set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/user-management.log"
BACKUP_DIR="${SCRIPT_DIR}/../backups/user-management"
AWS_REGION="ap-northeast-1"
SSM_PARAMETER_NAME="/excel-unlocker/allowed-users"

# ログ出力関数
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# エラーハンドリング
error_exit() {
    log "ERROR" "$1"
    exit 1
}

# 使用方法の表示
show_usage() {
    cat << EOF
ユーザー管理スクリプト - Secure Excel Unlock

使用方法:
    $0 <command> [options]

コマンド:
    add <email>                     新規ユーザーを追加
    remove <email>                  ユーザーを削除
    list                           現在のユーザー一覧を表示
    add-batch <emails>             複数ユーザーを一括追加（カンマ区切り）
    remove-batch <emails>          複数ユーザーを一括削除（カンマ区切り）
    list-all                       全環境のユーザー一覧を表示
    backup                         現在の設定をバックアップ
    restore <backup-file>          バックアップから復元
    validate                       設定の妥当性を検証
    audit                          監査レポートを生成

オプション:
    --environment <env>            対象環境 (development|staging|production)
    --dry-run                      実際の変更は行わない（テスト実行）
    --backup                       変更前にバックアップを作成
    --log-change                   変更履歴をログに記録
    --reason <reason>              変更理由を記録
    --format <format>              出力形式 (table|json|csv)
    --help                         このヘルプを表示

例:
    $0 add "user@example.com" --environment production --backup --reason "新規採用"
    $0 remove "user@example.com" --environment production --log-change
    $0 list --environment production --format table
    $0 add-batch "user1@example.com,user2@example.com" --environment staging --dry-run

EOF
}

# 環境の検証
validate_environment() {
    local env="$1"
    case "$env" in
        development|staging|production)
            return 0
            ;;
        *)
            error_exit "無効な環境: $env (development|staging|production のいずれかを指定してください)"
            ;;
    esac
}

# メールアドレスの検証
validate_email() {
    local email="$1"
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        error_exit "無効なメールアドレス形式: $email"
    fi
}

# AWS CLIの確認
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        error_exit "AWS CLIがインストールされていません"
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        error_exit "AWS認証が設定されていません。'aws configure'を実行してください"
    fi
}

# ディレクトリの作成
ensure_directories() {
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$BACKUP_DIR"
}

# 現在のユーザーリストを取得
get_current_users() {
    local env="$1"
    local param_name="${SSM_PARAMETER_NAME}"
    
    aws ssm get-parameter \
        --name "$param_name" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo ""
}

# ユーザーリストを更新
update_users() {
    local env="$1"
    local new_users="$2"
    local param_name="${SSM_PARAMETER_NAME}"
    
    log "INFO" "Parameter Store を更新中: $param_name"
    aws ssm put-parameter \
        --name "$param_name" \
        --value "$new_users" \
        --type "String" \
        --overwrite \
        --region "$AWS_REGION" > /dev/null
    
    log "INFO" "Lambda関数の環境変数を更新中"
    update_lambda_functions "$env" "$new_users"
}

# Lambda関数の環境変数を更新
update_lambda_functions() {
    local env="$1"
    local new_users="$2"
    
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    for function_name in "${functions[@]}"; do
        log "INFO" "Lambda関数を更新中: $function_name"
        
        # 現在の環境変数を取得
        local current_env
        current_env=$(aws lambda get-function-configuration \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Environment.Variables" \
            --output json 2>/dev/null) || {
            log "WARN" "Lambda関数が見つかりません: $function_name"
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
        
        log "INFO" "Lambda関数の更新完了: $function_name"
    done
}

# バックアップの作成
create_backup() {
    local env="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="${BACKUP_DIR}/users_${env}_${timestamp}.json"
    
    log "INFO" "バックアップを作成中: $backup_file"
    
    local current_users
    current_users=$(get_current_users "$env")
    
    cat > "$backup_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$env",
    "allowed_users": "$current_users",
    "backup_reason": "Automatic backup before user management operation"
}
EOF
    
    log "INFO" "バックアップ作成完了: $backup_file"
    echo "$backup_file"
}

# ユーザー追加
add_user() {
    local email="$1"
    local env="$2"
    local dry_run="$3"
    local create_backup="$4"
    local log_change="$5"
    local reason="$6"
    
    validate_email "$email"
    validate_environment "$env"
    
    local current_users
    current_users=$(get_current_users "$env")
    
    # 既に存在するかチェック
    if [[ "$current_users" == *"$email"* ]]; then
        log "WARN" "ユーザーは既に存在します: $email"
        return 0
    fi
    
    # 新しいユーザーリストを作成
    local new_users
    if [[ -z "$current_users" ]]; then
        new_users="$email"
    else
        new_users="${current_users},${email}"
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "[DRY RUN] ユーザーを追加予定: $email"
        log "INFO" "[DRY RUN] 新しいユーザーリスト: $new_users"
        return 0
    fi
    
    # バックアップ作成
    if [[ "$create_backup" == "true" ]]; then
        create_backup "$env"
    fi
    
    # ユーザーリストを更新
    update_users "$env" "$new_users"
    
    log "INFO" "ユーザー追加完了: $email (環境: $env)"
    
    # 変更履歴の記録
    if [[ "$log_change" == "true" ]]; then
        log_user_change "ADD" "$email" "$env" "$reason"
    fi
}

# ユーザー削除
remove_user() {
    local email="$1"
    local env="$2"
    local dry_run="$3"
    local create_backup="$4"
    local log_change="$5"
    local reason="$6"
    
    validate_email "$email"
    validate_environment "$env"
    
    local current_users
    current_users=$(get_current_users "$env")
    
    # 存在するかチェック
    if [[ "$current_users" != *"$email"* ]]; then
        log "WARN" "ユーザーが見つかりません: $email"
        return 0
    fi
    
    # ユーザーを削除した新しいリストを作成
    local new_users
    new_users=$(echo "$current_users" | sed "s/${email},//g" | sed "s/,${email}//g" | sed "s/^${email}$//g")
    
    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "[DRY RUN] ユーザーを削除予定: $email"
        log "INFO" "[DRY RUN] 新しいユーザーリスト: $new_users"
        return 0
    fi
    
    # バックアップ作成
    if [[ "$create_backup" == "true" ]]; then
        create_backup "$env"
    fi
    
    # ユーザーリストを更新
    update_users "$env" "$new_users"
    
    log "INFO" "ユーザー削除完了: $email (環境: $env)"
    
    # 変更履歴の記録
    if [[ "$log_change" == "true" ]]; then
        log_user_change "REMOVE" "$email" "$env" "$reason"
    fi
}

# ユーザー一覧表示
list_users() {
    local env="$1"
    local format="$2"
    
    validate_environment "$env"
    
    local current_users
    current_users=$(get_current_users "$env")
    
    if [[ -z "$current_users" ]]; then
        log "INFO" "環境 $env にはユーザーが登録されていません"
        return 0
    fi
    
    case "$format" in
        "table")
            echo "環境: $env"
            echo "----------------------------------------"
            echo "$current_users" | tr ',' '\n' | nl -w2 -s'. '
            echo "----------------------------------------"
            echo "合計: $(echo "$current_users" | tr ',' '\n' | wc -l) ユーザー"
            ;;
        "json")
            echo "$current_users" | tr ',' '\n' | jq -R . | jq -s "{environment: \"$env\", users: .}"
            ;;
        "csv")
            echo "environment,email"
            echo "$current_users" | tr ',' '\n' | sed "s/^/$env,/"
            ;;
        *)
            echo "環境: $env"
            echo "$current_users" | tr ',' '\n'
            ;;
    esac
}

# 一括ユーザー追加
add_batch_users() {
    local emails="$1"
    local env="$2"
    local dry_run="$3"
    local create_backup="$4"
    local log_change="$5"
    local reason="$6"
    
    validate_environment "$env"
    
    # バックアップ作成（一度だけ）
    if [[ "$create_backup" == "true" && "$dry_run" != "true" ]]; then
        create_backup "$env"
    fi
    
    # メールアドレスを分割して処理
    IFS=',' read -ra EMAIL_ARRAY <<< "$emails"
    local success_count=0
    local error_count=0
    
    for email in "${EMAIL_ARRAY[@]}"; do
        email=$(echo "$email" | xargs)  # 空白を除去
        
        if [[ -n "$email" ]]; then
            if add_user "$email" "$env" "$dry_run" "false" "$log_change" "$reason"; then
                ((success_count++))
            else
                ((error_count++))
            fi
        fi
    done
    
    log "INFO" "一括追加完了: 成功 $success_count 件, エラー $error_count 件"
}

# 一括ユーザー削除
remove_batch_users() {
    local emails="$1"
    local env="$2"
    local dry_run="$3"
    local create_backup="$4"
    local log_change="$5"
    local reason="$6"
    
    validate_environment "$env"
    
    # バックアップ作成（一度だけ）
    if [[ "$create_backup" == "true" && "$dry_run" != "true" ]]; then
        create_backup "$env"
    fi
    
    # メールアドレスを分割して処理
    IFS=',' read -ra EMAIL_ARRAY <<< "$emails"
    local success_count=0
    local error_count=0
    
    for email in "${EMAIL_ARRAY[@]}"; do
        email=$(echo "$email" | xargs)  # 空白を除去
        
        if [[ -n "$email" ]]; then
            if remove_user "$email" "$env" "$dry_run" "false" "$log_change" "$reason"; then
                ((success_count++))
            else
                ((error_count++))
            fi
        fi
    done
    
    log "INFO" "一括削除完了: 成功 $success_count 件, エラー $error_count 件"
}

# 全環境のユーザー一覧表示
list_all_users() {
    local format="$1"
    local environments=("development" "staging" "production")
    
    for env in "${environments[@]}"; do
        echo
        list_users "$env" "$format"
    done
}

# 設定の妥当性検証
validate_configuration() {
    local env="$1"
    local errors=0
    
    log "INFO" "設定の妥当性を検証中: $env"
    
    # Parameter Storeの確認
    local current_users
    current_users=$(get_current_users "$env")
    
    if [[ -z "$current_users" ]]; then
        log "WARN" "ユーザーが設定されていません (環境: $env)"
        ((errors++))
    else
        # メールアドレス形式の検証
        IFS=',' read -ra EMAIL_ARRAY <<< "$current_users"
        for email in "${EMAIL_ARRAY[@]}"; do
            email=$(echo "$email" | xargs)
            if ! [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                log "ERROR" "無効なメールアドレス形式: $email (環境: $env)"
                ((errors++))
            fi
        done
    fi
    
    # Lambda関数の環境変数確認
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    for function_name in "${functions[@]}"; do
        local lambda_users
        lambda_users=$(aws lambda get-function-configuration \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Environment.Variables.ALLOWED_USERS" \
            --output text 2>/dev/null) || {
            log "ERROR" "Lambda関数が見つかりません: $function_name"
            ((errors++))
            continue
        }
        
        if [[ "$lambda_users" != "$current_users" ]]; then
            log "ERROR" "Parameter StoreとLambda関数の設定が不一致: $function_name"
            log "ERROR" "Parameter Store: $current_users"
            log "ERROR" "Lambda関数: $lambda_users"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log "INFO" "設定の妥当性検証完了: エラーなし (環境: $env)"
    else
        log "ERROR" "設定の妥当性検証完了: $errors 件のエラー (環境: $env)"
    fi
    
    return $errors
}

# 変更履歴の記録
log_user_change() {
    local action="$1"
    local email="$2"
    local env="$3"
    local reason="$4"
    
    local change_log="${SCRIPT_DIR}/../logs/user-changes.log"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local user=$(whoami)
    
    cat >> "$change_log" << EOF
{
    "timestamp": "$timestamp",
    "action": "$action",
    "email": "$email",
    "environment": "$env",
    "reason": "$reason",
    "operator": "$user",
    "source": "manage-users.sh"
}
EOF
    
    log "INFO" "変更履歴を記録: $action $email (環境: $env, 理由: $reason)"
}

# 監査レポートの生成
generate_audit_report() {
    local env="$1"
    local output_file="${SCRIPT_DIR}/../reports/user-audit-$(date +%Y%m%d_%H%M%S).json"
    
    mkdir -p "$(dirname "$output_file")"
    
    log "INFO" "監査レポートを生成中: $output_file"
    
    local current_users
    current_users=$(get_current_users "$env")
    
    local user_count=0
    if [[ -n "$current_users" ]]; then
        user_count=$(echo "$current_users" | tr ',' '\n' | wc -l)
    fi
    
    cat > "$output_file" << EOF
{
    "audit_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$env",
    "total_users": $user_count,
    "users": [
$(echo "$current_users" | tr ',' '\n' | sed 's/.*/"&"/' | paste -sd ',' -)
    ],
    "configuration_status": "$(validate_configuration "$env" &>/dev/null && echo "valid" || echo "invalid")",
    "last_backup": "$(ls -t "$BACKUP_DIR"/users_${env}_*.json 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo "none")"
}
EOF
    
    log "INFO" "監査レポート生成完了: $output_file"
    echo "$output_file"
}

# メイン処理
main() {
    local command=""
    local email=""
    local environment="development"
    local dry_run="false"
    local create_backup="false"
    local log_change="false"
    local reason=""
    local format="table"
    
    # 引数の解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            add|remove|list|add-batch|remove-batch|list-all|backup|restore|validate|audit)
                command="$1"
                if [[ "$command" =~ ^(add|remove|add-batch|remove-batch|restore)$ ]] && [[ $# -gt 1 ]]; then
                    shift
                    email="$1"
                fi
                ;;
            --environment)
                shift
                environment="$1"
                ;;
            --dry-run)
                dry_run="true"
                ;;
            --backup)
                create_backup="true"
                ;;
            --log-change)
                log_change="true"
                ;;
            --reason)
                shift
                reason="$1"
                ;;
            --format)
                shift
                format="$1"
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                error_exit "不明なオプション: $1"
                ;;
        esac
        shift
    done
    
    # 必要なツールの確認
    check_aws_cli
    ensure_directories
    
    # コマンドの実行
    case "$command" in
        "add")
            [[ -z "$email" ]] && error_exit "メールアドレスが指定されていません"
            add_user "$email" "$environment" "$dry_run" "$create_backup" "$log_change" "$reason"
            ;;
        "remove")
            [[ -z "$email" ]] && error_exit "メールアドレスが指定されていません"
            remove_user "$email" "$environment" "$dry_run" "$create_backup" "$log_change" "$reason"
            ;;
        "list")
            list_users "$environment" "$format"
            ;;
        "add-batch")
            [[ -z "$email" ]] && error_exit "メールアドレスリストが指定されていません"
            add_batch_users "$email" "$environment" "$dry_run" "$create_backup" "$log_change" "$reason"
            ;;
        "remove-batch")
            [[ -z "$email" ]] && error_exit "メールアドレスリストが指定されていません"
            remove_batch_users "$email" "$environment" "$dry_run" "$create_backup" "$log_change" "$reason"
            ;;
        "list-all")
            list_all_users "$format"
            ;;
        "backup")
            create_backup "$environment"
            ;;
        "validate")
            validate_configuration "$environment"
            ;;
        "audit")
            generate_audit_report "$environment"
            ;;
        "")
            show_usage
            exit 1
            ;;
        *)
            error_exit "不明なコマンド: $command"
            ;;
    esac
}

# スクリプト実行
main "$@"