#!/bin/bash
# =============================================================================
# パフォーマンススモークテスト
# 
# 目的: 20MB以下のファイルをN=4並列で処理し、10秒以内に完了することを確認
# 合否基準: 全リクエストがHTTP 200で成功し、10秒以内に完了すること
# =============================================================================

set -uo pipefail

# 設定
BASE_URL="${BASE_URL:-http://localhost:3000}"
PARALLEL_COUNT="${PARALLEL_COUNT:-4}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-10}"
PASSWORD="test1234"
DATA_DIR="data"
TMP_DIR="/tmp/perf_smoke_$$"

# ログ関数
log_info() { echo "[INFO] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }
log_success() { echo "[OK] $*" >&2; }
log_fail() { echo "[NG] $*" >&2; }

# クリーンアップ
cleanup() {
    rm -rf "$TMP_DIR" 2>/dev/null || true
}
trap cleanup EXIT

# ヘルスチェック
check_health() {
    log_info "サーバーのヘルスチェックを実行中..."
    local code
    code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE_URL}/health" || echo "000")
    if [ "$code" != "200" ]; then
        log_error "サーバーが応答しません (HTTP: $code)"
        exit 1
    fi
    log_info "ヘルスチェック成功"
}

# テストファイルの取得
get_test_file() {
    local file
    file=$(find "$DATA_DIR" -name "*.xlsx" 2>/dev/null | head -1)
    if [ -z "$file" ]; then
        log_error "テストファイルが見つかりません: $DATA_DIR/*.xlsx"
        exit 1
    fi
    echo "$file"
}

# 単一リクエスト実行（バックグラウンド用）
run_single_request() {
    local index="$1"
    local file="$2"
    
    local code
    code=$(curl -s -o "${TMP_DIR}/response_${index}.json" \
        -w '%{http_code}' \
        -X POST "${BASE_URL}/unlock" \
        -F "file=@${file}" \
        -F "password1=${PASSWORD}" 2>/dev/null || echo "000")
    
    echo "$code" > "${TMP_DIR}/result_${index}.txt"
}

# 並列リクエストの実行
run_parallel_requests() {
    local file="$1"
    local pids=()
    
    log_info "並列リクエストを開始 (N=$PARALLEL_COUNT)"
    
    for i in $(seq 1 "$PARALLEL_COUNT"); do
        log_info "  [$i/$PARALLEL_COUNT] リクエスト送信中..."
        run_single_request "$i" "$file" &
        pids+=($!)
    done
    
    # 全プロセスの完了を待機
    local exit_status=0
    for pid in "${pids[@]}"; do
        wait "$pid" || exit_status=$?
    done
    
    return 0
}

# 結果の検証
validate_results() {
    local elapsed="$1"
    local success=0
    local fail=0
    
    log_info "========== テスト結果 =========="
    
    for i in $(seq 1 "$PARALLEL_COUNT"); do
        local code_file="${TMP_DIR}/result_${i}.txt"
        local resp_file="${TMP_DIR}/response_${i}.json"
        
        if [ -f "$code_file" ]; then
            local code
            code=$(cat "$code_file")
            local status="unknown"
            
            if [ -f "$resp_file" ]; then
                status=$(jq -r '.status // "unknown"' "$resp_file" 2>/dev/null || echo "unknown")
            fi
            
            if [ "$code" = "200" ] && [ "$status" = "success" ]; then
                log_success "リクエスト $i: HTTP $code, status=$status"
                ((success++)) || true
            else
                log_fail "リクエスト $i: HTTP $code, status=$status"
                ((fail++)) || true
            fi
        else
            log_fail "リクエスト $i: 結果ファイルなし"
            ((fail++)) || true
        fi
    done
    
    log_info "========== サマリー =========="
    log_info "並列数: $PARALLEL_COUNT"
    log_info "成功: $success"
    log_info "失敗: $fail"
    log_info "処理時間: ${elapsed}秒"
    log_info "タイムアウト閾値: ${TIMEOUT_SECONDS}秒"
    
    if [ "$fail" -gt 0 ]; then
        log_error "========== 不合格 =========="
        log_error "理由: $fail 件のリクエストが失敗"
        return 1
    fi
    
    if [ "$elapsed" -gt "$TIMEOUT_SECONDS" ]; then
        log_error "========== 不合格 =========="
        log_error "理由: 処理時間 (${elapsed}秒) がタイムアウト (${TIMEOUT_SECONDS}秒) を超過"
        return 1
    fi
    
    log_success "========== 合格 =========="
    log_success "全 $success 件が ${elapsed}秒 で完了"
    return 0
}

# メイン処理
main() {
    log_info "=========================================="
    log_info "  パフォーマンススモークテスト"
    log_info "=========================================="
    log_info "設定:"
    log_info "  BASE_URL: $BASE_URL"
    log_info "  並列数: $PARALLEL_COUNT"
    log_info "  タイムアウト: ${TIMEOUT_SECONDS}秒"
    
    for cmd in curl jq; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "$cmd コマンドが見つかりません"
            exit 1
        fi
    done
    
    mkdir -p "$TMP_DIR"
    check_health
    
    local test_file
    test_file=$(get_test_file)
    local file_size
    file_size=$(du -h "$test_file" 2>/dev/null | cut -f1)
    log_info "テストファイル: $(basename "$test_file") ($file_size)"
    
    local start_time
    start_time=$(date +%s)
    
    run_parallel_requests "$test_file"
    
    local end_time
    end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    
    if validate_results "$elapsed"; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
