#!/bin/bash

# ユーザー監査スクリプト
# ユーザーアクセス権限の監査レポートを生成

set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/user-audit.log"
REPORT_DIR="${SCRIPT_DIR}/../reports"
AWS_REGION="ap-northeast-1"

# ログ出力関数
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# 使用方法の表示
show_usage() {
    cat << EOF
ユーザー監査スクリプト - Secure Excel Unlock

使用方法:
    $0 [options]

オプション:
    --environment <env>            対象環境 (development|staging|production|all)
    --output-format <format>       出力形式 (json|html|csv|text)
    --detailed                     詳細な監査レポートを生成
    --start-date <date>            監査期間開始日 (YYYY-MM-DD)
    --end-date <date>              監査期間終了日 (YYYY-MM-DD)
    --include-logs                 CloudWatchログ分析を含める
    --output-file <file>           出力ファイル名（省略時は自動生成）
    --help                         このヘルプを表示

例:
    $0 --environment production --output-format html --detailed
    $0 --environment all --start-date 2025-01-01 --end-date 2025-01-31
    $0 --environment production --include-logs --output-file audit-report.json

EOF
}

# 現在のユーザー設定を取得
get_user_configuration() {
    local env="$1"
    
    log "INFO" "ユーザー設定を取得中: $env"
    
    # Parameter Storeから取得
    local allowed_users
    allowed_users=$(aws ssm get-parameter \
        --name "/excel-unlocker/allowed-users" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "")
    
    # Lambda関数の設定も取得
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    local lambda_configs=()
    for function_name in "${functions[@]}"; do
        local lambda_users
        lambda_users=$(aws lambda get-function-configuration \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Environment.Variables.ALLOWED_USERS" \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        lambda_configs+=("$function_name:$lambda_users")
    done
    
    # JSON形式で返却
    cat << EOF
{
    "environment": "$env",
    "parameter_store": "$allowed_users",
    "lambda_functions": [
$(printf '%s\n' "${lambda_configs[@]}" | sed 's/\(.*\):\(.*\)/        {"function": "\1", "allowed_users": "\2"}/' | paste -sd ',' -)
    ],
    "user_count": $(echo "$allowed_users" | tr ',' '\n' | grep -v '^$' | wc -l),
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# CloudWatchログの分析
analyze_access_logs() {
    local env="$1"
    local start_date="$2"
    local end_date="$3"
    
    log "INFO" "アクセスログを分析中: $env ($start_date - $end_date)"
    
    # 日付をエポック時間に変換
    local start_time
    local end_time
    start_time=$(date -d "$start_date" +%s)000
    end_time=$(date -d "$end_date 23:59:59" +%s)000
    
    # Lambda関数のログを分析
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    local access_summary=()
    local error_summary=()
    
    for function_name in "${functions[@]}"; do
        local log_group="/aws/lambda/$function_name"
        
        # アクセス成功ログの取得
        local access_logs
        access_logs=$(aws logs filter-log-events \
            --log-group-name "$log_group" \
            --start-time "$start_time" \
            --end-time "$end_time" \
            --filter-pattern "Access granted" \
            --region "$AWS_REGION" \
            --query "events[*].message" \
            --output text 2>/dev/null || echo "")
        
        # アクセス拒否ログの取得
        local denied_logs
        denied_logs=$(aws logs filter-log-events \
            --log-group-name "$log_group" \
            --start-time "$start_time" \
            --end-time "$end_time" \
            --filter-pattern "Access denied" \
            --region "$AWS_REGION" \
            --query "events[*].message" \
            --output text 2>/dev/null || echo "")
        
        # エラーログの取得
        local error_logs
        error_logs=$(aws logs filter-log-events \
            --log-group-name "$log_group" \
            --start-time "$start_time" \
            --end-time "$end_time" \
            --filter-pattern "ERROR" \
            --region "$AWS_REGION" \
            --query "events[*].message" \
            --output text 2>/dev/null || echo "")
        
        # 統計情報の計算
        local access_count
        local denied_count
        local error_count
        access_count=$(echo "$access_logs" | grep -c "Access granted" || echo "0")
        denied_count=$(echo "$denied_logs" | grep -c "Access denied" || echo "0")
        error_count=$(echo "$error_logs" | grep -c "ERROR" || echo "0")
        
        access_summary+=("$function_name:$access_count:$denied_count:$error_count")
    done
    
    # JSON形式で返却
    cat << EOF
{
    "analysis_period": {
        "start_date": "$start_date",
        "end_date": "$end_date"
    },
    "functions": [
$(printf '%s\n' "${access_summary[@]}" | sed 's/\(.*\):\(.*\):\(.*\):\(.*\)/        {"function": "\1", "access_granted": \2, "access_denied": \3, "errors": \4}/' | paste -sd ',' -)
    ],
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# セキュリティ分析
analyze_security() {
    local env="$1"
    
    log "INFO" "セキュリティ分析を実行中: $env"
    
    local security_issues=()
    local recommendations=()
    
    # 1. 空のユーザーリストチェック
    local allowed_users
    allowed_users=$(aws ssm get-parameter \
        --name "/excel-unlocker/allowed-users" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$allowed_users" ]]; then
        security_issues+=("空のユーザーリスト: 全アクセス拒否状態")
        recommendations+=("適切なユーザーを設定してください")
    fi
    
    # 2. Parameter StoreとLambda関数の整合性チェック
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
            --output text 2>/dev/null || echo "")
        
        if [[ "$lambda_users" != "$allowed_users" ]]; then
            security_issues+=("設定不一致: $function_name")
            recommendations+=("$function_name の環境変数を Parameter Store と同期してください")
        fi
    done
    
    # 3. 緊急状態フラグのチェック
    local emergency_status
    emergency_status=$(aws ssm get-parameter \
        --name "/excel-unlocker/emergency-status" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "NORMAL")
    
    if [[ "$emergency_status" != "NORMAL" ]]; then
        security_issues+=("緊急状態: $emergency_status")
        recommendations+=("緊急状態を解除するか、適切な対応を実施してください")
    fi
    
    # 4. 過度に多いユーザー数のチェック
    local user_count
    user_count=$(echo "$allowed_users" | tr ',' '\n' | grep -v '^$' | wc -l)
    
    if [[ $user_count -gt 50 ]]; then
        security_issues+=("ユーザー数過多: $user_count ユーザー")
        recommendations+=("ユーザー数を見直し、不要なユーザーを削除してください")
    fi
    
    # JSON形式で返却
    cat << EOF
{
    "environment": "$env",
    "security_issues": [
$(printf '%s\n' "${security_issues[@]}" | sed 's/.*/        "&"/' | paste -sd ',' -)
    ],
    "recommendations": [
$(printf '%s\n' "${recommendations[@]}" | sed 's/.*/        "&"/' | paste -sd ',' -)
    ],
    "risk_level": "$([ ${#security_issues[@]} -eq 0 ] && echo "LOW" || [ ${#security_issues[@]} -le 2 ] && echo "MEDIUM" || echo "HIGH")",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

# 包括的な監査レポートの生成
generate_comprehensive_report() {
    local env="$1"
    local detailed="$2"
    local include_logs="$3"
    local start_date="$4"
    local end_date="$5"
    
    log "INFO" "包括的監査レポートを生成中: $env"
    
    # 基本情報の取得
    local user_config
    user_config=$(get_user_configuration "$env")
    
    # セキュリティ分析
    local security_analysis
    security_analysis=$(analyze_security "$env")
    
    # ログ分析（オプション）
    local log_analysis="{}"
    if [[ "$include_logs" == "true" ]]; then
        log_analysis=$(analyze_access_logs "$env" "$start_date" "$end_date")
    fi
    
    # 詳細情報（オプション）
    local detailed_info="{}"
    if [[ "$detailed" == "true" ]]; then
        # バックアップ情報
        local backup_files
        backup_files=$(ls -t "${SCRIPT_DIR}/../backups/user-management/users_${env}_"*.json 2>/dev/null | head -5 || echo "")
        
        # 最近の変更履歴
        local recent_changes
        recent_changes=$(tail -10 "${SCRIPT_DIR}/../logs/user-changes.log" 2>/dev/null | grep "\"environment\": \"$env\"" || echo "")
        
        detailed_info=$(cat << EOF
{
    "recent_backups": [
$(echo "$backup_files" | sed 's/.*/        "&"/' | paste -sd ',' -)
    ],
    "recent_changes_count": $(echo "$recent_changes" | wc -l),
    "system_info": {
        "aws_region": "$AWS_REGION",
        "audit_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "auditor": "$(whoami)"
    }
}
EOF
)
    fi
    
    # 統合レポートの生成
    cat << EOF
{
    "audit_report": {
        "version": "1.0",
        "environment": "$env",
        "audit_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "audit_period": {
            "start_date": "$start_date",
            "end_date": "$end_date"
        }
    },
    "user_configuration": $user_config,
    "security_analysis": $security_analysis,
    "log_analysis": $log_analysis,
    "detailed_information": $detailed_info
}
EOF
}

# HTMLレポートの生成
generate_html_report() {
    local json_data="$1"
    local output_file="$2"
    
    log "INFO" "HTMLレポートを生成中: $output_file"
    
    # JSONからデータを抽出
    local env
    local audit_timestamp
    local user_count
    local risk_level
    
    env=$(echo "$json_data" | jq -r '.audit_report.environment')
    audit_timestamp=$(echo "$json_data" | jq -r '.audit_report.audit_timestamp')
    user_count=$(echo "$json_data" | jq -r '.user_configuration.user_count')
    risk_level=$(echo "$json_data" | jq -r '.security_analysis.risk_level')
    
    # HTMLテンプレート
    cat > "$output_file" << EOF
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ユーザー監査レポート - $env</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { color: #007bff; margin: 0; }
        .header .meta { color: #666; font-size: 14px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #333; border-left: 4px solid #007bff; padding-left: 10px; }
        .card { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 15px; margin-bottom: 15px; }
        .status-ok { color: #28a745; font-weight: bold; }
        .status-warning { color: #ffc107; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        .user-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; }
        .user-item { background-color: #e9ecef; padding: 8px; border-radius: 4px; font-family: monospace; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #dee2e6; padding: 8px; text-align: left; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 ユーザー監査レポート</h1>
            <div class="meta">
                環境: <strong>$env</strong> | 
                監査日時: <strong>$audit_timestamp</strong> | 
                ユーザー数: <strong>$user_count</strong> | 
                リスクレベル: <span class="status-$(echo "$risk_level" | tr '[:upper:]' '[:lower:]')">$risk_level</span>
            </div>
        </div>

        <div class="section">
            <h2>📊 概要</h2>
            <div class="card">
                <p><strong>監査対象環境:</strong> $env</p>
                <p><strong>登録ユーザー数:</strong> $user_count</p>
                <p><strong>セキュリティリスクレベル:</strong> 
                    <span class="status-$(echo "$risk_level" | tr '[:upper:]' '[:lower:]')">$risk_level</span>
                </p>
                <p><strong>監査実行者:</strong> $(whoami)</p>
            </div>
        </div>

        <div class="section">
            <h2>👥 ユーザー設定</h2>
            <div class="card">
                <h3>登録ユーザー一覧</h3>
                <div class="user-list">
$(echo "$json_data" | jq -r '.user_configuration.parameter_store' | tr ',' '\n' | sed 's/^/                    <div class="user-item">/' | sed 's/$/<\/div>/')
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔒 セキュリティ分析</h2>
            <div class="card">
                <h3>検出された問題</h3>
$(echo "$json_data" | jq -r '.security_analysis.security_issues[]' 2>/dev/null | sed 's/^/                <p class="status-error">❌ /' | sed 's/$/<\/p>/' || echo '                <p class="status-ok">✅ 問題は検出されませんでした</p>')
                
                <h3>推奨事項</h3>
$(echo "$json_data" | jq -r '.security_analysis.recommendations[]' 2>/dev/null | sed 's/^/                <p>💡 /' | sed 's/$/<\/p>/' || echo '                <p>特に推奨事項はありません</p>')
            </div>
        </div>

        <div class="section">
            <h2>⚙️ システム設定</h2>
            <div class="card">
                <table>
                    <tr>
                        <th>項目</th>
                        <th>値</th>
                        <th>状態</th>
                    </tr>
                    <tr>
                        <td>Parameter Store</td>
                        <td>$(echo "$json_data" | jq -r '.user_configuration.parameter_store' | cut -c1-50)...</td>
                        <td><span class="status-ok">✅ 正常</span></td>
                    </tr>
$(echo "$json_data" | jq -r '.user_configuration.lambda_functions[] | "<tr><td>" + .function + "</td><td>" + (.allowed_users | tostring | .[0:50]) + "...</td><td><span class=\"status-ok\">✅ 正常</span></td></tr>"')
                </table>
            </div>
        </div>

        <div class="footer">
            <p>このレポートは自動生成されました。最新の情報については、システム管理者にお問い合わせください。</p>
            <p>生成時刻: $(date) | スクリプト: audit-users.sh</p>
        </div>
    </div>
</body>
</html>
EOF
    
    log "INFO" "HTMLレポート生成完了: $output_file"
}

# CSVレポートの生成
generate_csv_report() {
    local json_data="$1"
    local output_file="$2"
    
    log "INFO" "CSVレポートを生成中: $output_file"
    
    # CSVヘッダー
    cat > "$output_file" << EOF
Environment,User Email,Status,Last Updated,Risk Level
EOF
    
    # ユーザーデータの抽出
    local env
    local users
    local risk_level
    local timestamp
    
    env=$(echo "$json_data" | jq -r '.audit_report.environment')
    users=$(echo "$json_data" | jq -r '.user_configuration.parameter_store')
    risk_level=$(echo "$json_data" | jq -r '.security_analysis.risk_level')
    timestamp=$(echo "$json_data" | jq -r '.audit_report.audit_timestamp')
    
    # ユーザーごとの行を追加
    echo "$users" | tr ',' '\n' | while read -r user; do
        if [[ -n "$user" ]]; then
            echo "$env,$user,Active,$timestamp,$risk_level" >> "$output_file"
        fi
    done
    
    log "INFO" "CSVレポート生成完了: $output_file"
}

# メイン処理
main() {
    local environment="production"
    local output_format="json"
    local detailed="false"
    local start_date=$(date -d '30 days ago' +%Y-%m-%d)
    local end_date=$(date +%Y-%m-%d)
    local include_logs="false"
    local output_file=""
    
    # 引数の解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                shift
                environment="$1"
                ;;
            --output-format)
                shift
                output_format="$1"
                ;;
            --detailed)
                detailed="true"
                ;;
            --start-date)
                shift
                start_date="$1"
                ;;
            --end-date)
                shift
                end_date="$1"
                ;;
            --include-logs)
                include_logs="true"
                ;;
            --output-file)
                shift
                output_file="$1"
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "不明なオプション: $1" >&2
                show_usage
                exit 1
                ;;
        esac
        shift
    done
    
    # ディレクトリの作成
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$REPORT_DIR"
    
    # AWS CLIの確認
    if ! command -v aws &> /dev/null; then
        echo "AWS CLIがインストールされていません" >&2
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "AWS認証が設定されていません" >&2
        exit 1
    fi
    
    # 出力ファイル名の自動生成
    if [[ -z "$output_file" ]]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        case "$output_format" in
            "html")
                output_file="${REPORT_DIR}/user-audit-${environment}-${timestamp}.html"
                ;;
            "csv")
                output_file="${REPORT_DIR}/user-audit-${environment}-${timestamp}.csv"
                ;;
            "json")
                output_file="${REPORT_DIR}/user-audit-${environment}-${timestamp}.json"
                ;;
            *)
                output_file="${REPORT_DIR}/user-audit-${environment}-${timestamp}.txt"
                ;;
        esac
    fi
    
    # 全環境の処理
    if [[ "$environment" == "all" ]]; then
        local environments=("development" "staging" "production")
        for env in "${environments[@]}"; do
            echo "🔍 監査実行中: $env"
            local env_output_file="${output_file%.*}-${env}.${output_file##*.}"
            
            # 個別環境のレポート生成
            local json_report
            json_report=$(generate_comprehensive_report "$env" "$detailed" "$include_logs" "$start_date" "$end_date")
            
            case "$output_format" in
                "html")
                    generate_html_report "$json_report" "$env_output_file"
                    ;;
                "csv")
                    generate_csv_report "$json_report" "$env_output_file"
                    ;;
                "json")
                    echo "$json_report" | jq . > "$env_output_file"
                    ;;
                *)
                    echo "$json_report" | jq . > "$env_output_file"
                    ;;
            esac
            
            echo "✅ 監査完了: $env -> $env_output_file"
        done
    else
        # 単一環境の処理
        echo "🔍 監査実行中: $environment"
        
        local json_report
        json_report=$(generate_comprehensive_report "$environment" "$detailed" "$include_logs" "$start_date" "$end_date")
        
        case "$output_format" in
            "html")
                generate_html_report "$json_report" "$output_file"
                ;;
            "csv")
                generate_csv_report "$json_report" "$output_file"
                ;;
            "json")
                echo "$json_report" | jq . > "$output_file"
                ;;
            *)
                echo "$json_report" | jq . > "$output_file"
                ;;
        esac
        
        echo "✅ 監査完了: $environment -> $output_file"
    fi
    
    log "INFO" "ユーザー監査完了"
}

# スクリプト実行
main "$@"