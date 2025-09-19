#!/bin/bash

# ユーザーアクセステストスクリプト
# 指定されたユーザーのアクセス権限をテスト

set -euo pipefail

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/user-access-test.log"
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
ユーザーアクセステストスクリプト - Secure Excel Unlock

使用方法:
    $0 <email> [options]

オプション:
    --environment <env>            対象環境 (development|staging|production)
    --expect-denied               アクセス拒否されることを期待（削除確認用）
    --api-endpoint <url>          APIエンドポイントURL（省略時は環境から自動取得）
    --verbose                     詳細なログ出力
    --help                        このヘルプを表示

例:
    $0 "user@example.com" --environment production
    $0 "removed-user@example.com" --environment production --expect-denied
    $0 "test@example.com" --environment development --verbose

EOF
}

# 環境からAPIエンドポイントを取得
get_api_endpoint() {
    local env="$1"
    
    case "$env" in
        "development")
            echo "https://localhost:3001"  # ローカル開発環境
            ;;
        "staging")
            # ステージング環境のAPI Gateway URLを取得
            aws cloudformation describe-stacks \
                --stack-name "excel-unlocker-api-staging" \
                --region "$AWS_REGION" \
                --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
                --output text 2>/dev/null || echo ""
            ;;
        "production")
            # 本番環境のAPI Gateway URLを取得
            aws cloudformation describe-stacks \
                --stack-name "excel-unlocker-api-production" \
                --region "$AWS_REGION" \
                --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
                --output text 2>/dev/null || echo ""
            ;;
        *)
            echo ""
            ;;
    esac
}

# テスト用JWTトークンの生成
generate_test_jwt_token() {
    local email="$1"
    echo "test-jwt-token-${email}"
}

# APIアクセステスト
test_api_access() {
    local email="$1"
    local api_endpoint="$2"
    local expect_denied="$3"
    local verbose="$4"
    
    log "INFO" "APIアクセステスト開始: $email -> $api_endpoint"
    
    # テスト用JWTトークンを生成
    local jwt_token
    jwt_token=$(generate_test_jwt_token "$email")
    
    # テストリクエストのペイロード
    local test_payload='{
        "fileName": "test.xlsx",
        "fileSize": 1024,
        "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }'
    
    # APIリクエストを実行
    local response
    local http_status
    local success=false
    
    if [[ "$verbose" == "true" ]]; then
        log "INFO" "リクエスト詳細:"
        log "INFO" "  URL: ${api_endpoint}/presigned-urls"
        log "INFO" "  Authorization: Bearer ${jwt_token}"
        log "INFO" "  Payload: $test_payload"
    fi
    
    # curlでAPIテスト実行
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${jwt_token}" \
        -d "$test_payload" \
        "${api_endpoint}/presigned-urls" 2>/dev/null || echo -e "\nERROR")
    
    # レスポンスとHTTPステータスを分離
    http_status=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [[ "$verbose" == "true" ]]; then
        log "INFO" "レスポンス詳細:"
        log "INFO" "  HTTPステータス: $http_status"
        log "INFO" "  レスポンスボディ: $response_body"
    fi
    
    # 結果の判定
    case "$http_status" in
        "200")
            success=true
            log "INFO" "✅ APIアクセス成功: $email (HTTP 200)"
            ;;
        "401"|"403")
            success=false
            log "INFO" "❌ APIアクセス拒否: $email (HTTP $http_status)"
            ;;
        "ERROR")
            log "ERROR" "🔥 APIリクエストエラー: $email (接続失敗)"
            return 2
            ;;
        *)
            log "WARN" "⚠️  予期しないHTTPステータス: $email (HTTP $http_status)"
            return 2
            ;;
    esac
    
    # 期待値との比較
    if [[ "$expect_denied" == "true" ]]; then
        if [[ "$success" == "false" ]]; then
            log "INFO" "✅ 期待通りアクセス拒否されました: $email"
            return 0
        else
            log "ERROR" "❌ アクセス拒否が期待されましたが、アクセスが許可されました: $email"
            return 1
        fi
    else
        if [[ "$success" == "true" ]]; then
            log "INFO" "✅ 期待通りアクセスが許可されました: $email"
            return 0
        else
            log "ERROR" "❌ アクセス許可が期待されましたが、アクセスが拒否されました: $email"
            return 1
        fi
    fi
}

# 設定確認テスト
test_configuration() {
    local email="$1"
    local env="$2"
    local verbose="$3"
    
    log "INFO" "設定確認テスト開始: $email (環境: $env)"
    
    # Parameter Storeの確認
    local allowed_users
    allowed_users=$(aws ssm get-parameter \
        --name "/excel-unlocker/allowed-users" \
        --region "$AWS_REGION" \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo "")
    
    if [[ "$verbose" == "true" ]]; then
        log "INFO" "Parameter Store設定: $allowed_users"
    fi
    
    # ユーザーが設定に含まれているかチェック
    if [[ "$allowed_users" == *"$email"* ]]; then
        log "INFO" "✅ Parameter Storeにユーザーが登録されています: $email"
        local config_success=true
    else
        log "INFO" "❌ Parameter Storeにユーザーが登録されていません: $email"
        local config_success=false
    fi
    
    # Lambda関数の環境変数確認
    local functions=(
        "excel-get-upload-url-function-${env}"
        "excel-unlock-function-${env}"
    )
    
    local lambda_success=true
    for function_name in "${functions[@]}"; do
        local lambda_users
        lambda_users=$(aws lambda get-function-configuration \
            --function-name "$function_name" \
            --region "$AWS_REGION" \
            --query "Environment.Variables.ALLOWED_USERS" \
            --output text 2>/dev/null || echo "")
        
        if [[ "$verbose" == "true" ]]; then
            log "INFO" "Lambda関数 $function_name 設定: $lambda_users"
        fi
        
        if [[ "$lambda_users" == *"$email"* ]]; then
            log "INFO" "✅ Lambda関数にユーザーが登録されています: $function_name"
        else
            log "INFO" "❌ Lambda関数にユーザーが登録されていません: $function_name"
            lambda_success=false
        fi
        
        # Parameter StoreとLambda関数の整合性確認
        if [[ "$lambda_users" != "$allowed_users" ]]; then
            log "WARN" "⚠️  Parameter StoreとLambda関数の設定が不一致: $function_name"
        fi
    done
    
    # 総合判定
    if [[ "$config_success" == "true" && "$lambda_success" == "true" ]]; then
        log "INFO" "✅ 設定確認テスト成功: $email"
        return 0
    else
        log "ERROR" "❌ 設定確認テスト失敗: $email"
        return 1
    fi
}

# 包括的なアクセステスト
comprehensive_test() {
    local email="$1"
    local env="$2"
    local api_endpoint="$3"
    local expect_denied="$4"
    local verbose="$5"
    
    log "INFO" "包括的アクセステスト開始: $email (環境: $env)"
    
    local test_results=()
    local overall_success=true
    
    # 1. 設定確認テスト
    echo "🔍 設定確認テスト実行中..."
    if test_configuration "$email" "$env" "$verbose"; then
        test_results+=("設定確認: ✅ 成功")
    else
        test_results+=("設定確認: ❌ 失敗")
        overall_success=false
    fi
    
    # 2. APIアクセステスト
    if [[ -n "$api_endpoint" ]]; then
        echo "🌐 APIアクセステスト実行中..."
        local api_result=0
        test_api_access "$email" "$api_endpoint" "$expect_denied" "$verbose" || api_result=$?
        
        case $api_result in
            0)
                test_results+=("APIアクセス: ✅ 成功")
                ;;
            1)
                test_results+=("APIアクセス: ❌ 失敗")
                overall_success=false
                ;;
            2)
                test_results+=("APIアクセス: ⚠️  エラー")
                overall_success=false
                ;;
        esac
    else
        test_results+=("APIアクセス: ⏭️  スキップ（エンドポイント不明）")
    fi
    
    # 結果サマリー
    echo
    echo "📊 テスト結果サマリー"
    echo "===================="
    echo "ユーザー: $email"
    echo "環境: $env"
    echo "時刻: $(date)"
    echo
    
    for result in "${test_results[@]}"; do
        echo "  $result"
    done
    
    echo
    if [[ "$overall_success" == "true" ]]; then
        echo "🎉 総合結果: ✅ 成功"
        log "INFO" "包括的アクセステスト成功: $email"
        return 0
    else
        echo "💥 総合結果: ❌ 失敗"
        log "ERROR" "包括的アクセステスト失敗: $email"
        return 1
    fi
}

# メイン処理
main() {
    local email=""
    local environment="development"
    local expect_denied="false"
    local api_endpoint=""
    local verbose="false"
    
    # 引数の解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                shift
                environment="$1"
                ;;
            --expect-denied)
                expect_denied="true"
                ;;
            --api-endpoint)
                shift
                api_endpoint="$1"
                ;;
            --verbose)
                verbose="true"
                ;;
            --help)
                show_usage
                exit 0
                ;;
            -*)
                echo "不明なオプション: $1" >&2
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$email" ]]; then
                    email="$1"
                else
                    echo "複数のメールアドレスが指定されました" >&2
                    show_usage
                    exit 1
                fi
                ;;
        esac
        shift
    done
    
    # 必須パラメータの確認
    if [[ -z "$email" ]]; then
        echo "メールアドレスが指定されていません" >&2
        show_usage
        exit 1
    fi
    
    # ログディレクトリの作成
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # AWS CLIの確認
    if ! command -v aws &> /dev/null; then
        echo "AWS CLIがインストールされていません" >&2
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "AWS認証が設定されていません。'aws configure'を実行してください" >&2
        exit 1
    fi
    
    # APIエンドポイントの自動取得
    if [[ -z "$api_endpoint" ]]; then
        api_endpoint=$(get_api_endpoint "$environment")
        if [[ -n "$api_endpoint" ]]; then
            log "INFO" "APIエンドポイントを自動取得: $api_endpoint"
        else
            log "WARN" "APIエンドポイントを取得できませんでした（環境: $environment）"
        fi
    fi
    
    # 包括的テストの実行
    comprehensive_test "$email" "$environment" "$api_endpoint" "$expect_denied" "$verbose"
}

# スクリプト実行
main "$@"