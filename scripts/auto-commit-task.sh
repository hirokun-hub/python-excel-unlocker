#!/bin/bash

# タスク完了時の自動コミット・プッシュスクリプト
# 使用方法: ./scripts/auto-commit-task.sh "タスク番号" "タスクタイトル" [--dry-run]

set -euo pipefail

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 引数チェック
if [ $# -lt 2 ]; then
    log_error "使用方法: $0 \"タスク番号\" \"タスクタイトル\" [--dry-run]"
    log_error "例: $0 \"15\" \"JWT認証への移行\" --dry-run"
    exit 1
fi

TASK_NUMBER="$1"
TASK_TITLE="$2"
DRY_RUN=false

# オプション解析
if [ $# -ge 3 ] && [ "$3" = "--dry-run" ]; then
    DRY_RUN=true
    log_info "ドライランモードで実行します（実際のコミット・プッシュは行いません）"
fi

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

log_info "タスク完了時の自動コミット・プッシュを開始します"
log_info "タスク: $TASK_NUMBER. $TASK_TITLE"

# 1. Git状態の確認
log_info "Git状態を確認しています..."
if ! git status --porcelain > /dev/null 2>&1; then
    log_error "Gitリポジトリではありません"
    exit 1
fi

# 変更があるかチェック
if [ -z "$(git status --porcelain)" ]; then
    log_warning "コミットする変更がありません"
    exit 0
fi

# 2. 安全性チェック
log_info "安全性チェックを実行しています..."

# 機密情報チェック
SENSITIVE_PATTERNS=(
    "password"
    "secret"
    "key"
    "token"
    "credential"
    "aws_access_key"
    "aws_secret"
    "api_key"
    "private_key"
)

log_info "機密情報の検出チェック..."
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if git diff --cached --name-only | xargs grep -il "$pattern" 2>/dev/null; then
        log_warning "機密情報の可能性があるファイルが検出されました: $pattern"
        log_warning "手動で確認してください"
    fi
done

# 大容量ファイルチェック（10MB以上）
log_info "大容量ファイルのチェック..."
large_files=$(git diff --cached --name-only | xargs ls -la 2>/dev/null | awk '$5 > 10485760 {print $9}' || true)
if [ -n "$large_files" ]; then
    log_warning "大容量ファイルが検出されました:"
    echo "$large_files"
    log_warning "これらのファイルをコミットしますか？"
fi

# .env ファイルチェック
log_info "環境変数ファイルのチェック..."
if git diff --cached --name-only | grep -E "\.(env|local)$" > /dev/null 2>&1; then
    log_warning "環境変数ファイルが含まれています"
    log_warning "機密情報が含まれていないか確認してください"
fi

# 3. コミットメッセージ生成
COMMIT_MESSAGE="feat: タスク${TASK_NUMBER}完了 - ${TASK_TITLE}

- タスク${TASK_NUMBER}の実装を完了
- ${TASK_TITLE}に関する変更を適用
- 関連ファイルの更新とテスト実行

Co-authored-by: Kiro AI Assistant <kiro@example.com>"

log_info "生成されたコミットメッセージ:"
echo "----------------------------------------"
echo "$COMMIT_MESSAGE"
echo "----------------------------------------"

# 4. 変更内容の表示
log_info "コミット対象の変更内容:"
git status --short

# 5. 確認プロンプト（ドライランでない場合）
if [ "$DRY_RUN" = false ]; then
    echo ""
    read -p "この内容でコミット・プッシュを実行しますか？ (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作をキャンセルしました"
        exit 0
    fi
fi

# 6. コミット実行
if [ "$DRY_RUN" = false ]; then
    log_info "変更をステージングしています..."
    git add .
    
    log_info "コミットを実行しています..."
    git commit -m "$COMMIT_MESSAGE"
    
    # 7. プッシュ実行
    log_info "リモートリポジトリにプッシュしています..."
    current_branch=$(git branch --show-current)
    git push origin "$current_branch"
    
    log_success "タスク${TASK_NUMBER}の変更を正常にコミット・プッシュしました"
    log_success "ブランチ: $current_branch"
    log_success "コミットハッシュ: $(git rev-parse --short HEAD)"
else
    log_info "[ドライラン] 以下の操作が実行される予定です:"
    log_info "[ドライラン] 1. git add ."
    log_info "[ドライラン] 2. git commit -m \"$COMMIT_MESSAGE\""
    log_info "[ドライラン] 3. git push origin $(git branch --show-current)"
fi

# 8. タスクファイルの更新（完了マークを付ける）
TASK_FILE=".kiro/specs/secure-excel-unlock/tasks.md"
if [ -f "$TASK_FILE" ]; then
    log_info "タスクファイルを更新しています..."
    
    # タスクを完了済みにマーク
    if [ "$DRY_RUN" = false ]; then
        # "- [ ] ${TASK_NUMBER}." を "- [x] ${TASK_NUMBER}." に変更
        sed -i.bak "s/^- \[ \] ${TASK_NUMBER}\./- [x] ${TASK_NUMBER}./" "$TASK_FILE"
        rm -f "${TASK_FILE}.bak"
        
        log_success "タスク${TASK_NUMBER}を完了済みにマークしました"
    else
        log_info "[ドライラン] タスク${TASK_NUMBER}を完了済みにマークする予定です"
    fi
fi

log_success "自動コミット・プッシュ処理が完了しました"