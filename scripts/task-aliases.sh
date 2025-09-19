#!/bin/bash

# タスク管理用のエイリアス設定
# 使用方法: source scripts/task-aliases.sh

# プロジェクトルートの設定
EXCEL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# タスク管理エイリアス
alias task-list="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' list"
alias task-list-all="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' list --all"
alias task-complete="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' complete"
alias task-mark="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' mark"
alias task-commit="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' commit"

# ドライラン版エイリアス
alias task-complete-dry="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' complete --dry-run"
alias task-mark-dry="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' mark --dry-run"
alias task-commit-dry="python3 '$EXCEL_PROJECT_ROOT/scripts/task_manager.py' commit --dry-run"

# 便利なGitエイリアス
alias git-status-clean="git status --porcelain"
alias git-diff-staged="git diff --cached"
alias git-log-recent="git log --oneline -10"

# 使用方法の表示
task-help() {
    echo "📋 タスク管理コマンド一覧"
    echo ""
    echo "🔍 タスク確認:"
    echo "  task-list          # 未完了タスクの一覧表示"
    echo "  task-list-all      # 全タスクの一覧表示"
    echo ""
    echo "✅ タスク完了:"
    echo "  task-complete 15   # タスク15を完了してコミット・プッシュ"
    echo "  task-mark 15       # タスク15を完了済みにマークのみ"
    echo ""
    echo "💾 コミット・プッシュ:"
    echo "  task-commit 15 \"JWT認証への移行\"  # 手動でコミット・プッシュ"
    echo ""
    echo "🧪 ドライラン（実行せずに確認）:"
    echo "  task-complete-dry 15"
    echo "  task-mark-dry 15"
    echo "  task-commit-dry 15 \"JWT認証への移行\""
    echo ""
    echo "🔧 Git便利コマンド:"
    echo "  git-status-clean   # 変更ファイルの簡潔表示"
    echo "  git-diff-staged    # ステージング済み変更の確認"
    echo "  git-log-recent     # 最近10件のコミット履歴"
    echo ""
    echo "💡 使用例:"
    echo "  task-list                    # 未完了タスクを確認"
    echo "  task-complete-dry 17         # タスク17の完了をドライラン"
    echo "  task-complete 17             # タスク17を実際に完了"
}

echo "✅ タスク管理エイリアスが設定されました"
echo "💡 使用方法を確認するには: task-help"