# タスク自動化ガイド

タスクリストの作業完了時に自動的にコミット・プッシュを行う機能の使用方法を説明します。

## 🎯 概要

このシステムは以下の機能を提供します：

- **タスク完了の自動マーク**: タスクリストの `[ ]` を `[x]` に自動変更
- **自動コミット・プッシュ**: 適切なコミットメッセージで変更を自動コミット・プッシュ
- **安全性チェック**: 機密情報や大容量ファイルの検出
- **ドライラン機能**: 実際の操作前に内容確認

## 🚀 クイックスタート

### 1. エイリアス設定

```bash
# プロジェクトルートで実行
source scripts/task-aliases.sh
```

### 2. タスク一覧確認

```bash
# 未完了タスクの確認
task-list

# 全タスクの確認
task-list-all
```

### 3. タスク完了

```bash
# ドライランで確認（推奨）
task-complete-dry 17

# 実際にタスクを完了
task-complete 17
```

## 📋 利用可能なコマンド

### タスク確認コマンド

| コマンド | 説明 |
|---------|------|
| `task-list` | 未完了タスクの一覧表示 |
| `task-list-all` | 全タスクの一覧表示（完了済み含む） |

### タスク完了コマンド

| コマンド | 説明 |
|---------|------|
| `task-complete <番号>` | タスクを完了してコミット・プッシュ |
| `task-mark <番号>` | タスクを完了済みにマークのみ |
| `task-commit <番号> "<タイトル>"` | 手動でコミット・プッシュ |

### ドライランコマンド

| コマンド | 説明 |
|---------|------|
| `task-complete-dry <番号>` | タスク完了のドライラン |
| `task-mark-dry <番号>` | タスクマークのドライラン |
| `task-commit-dry <番号> "<タイトル>"` | コミット・プッシュのドライラン |

### Git便利コマンド

| コマンド | 説明 |
|---------|------|
| `git-status-clean` | 変更ファイルの簡潔表示 |
| `git-diff-staged` | ステージング済み変更の確認 |
| `git-log-recent` | 最近10件のコミット履歴 |

## 🔧 詳細な使用方法

### タスク完了の基本フロー

1. **現在の状況確認**
   ```bash
   task-list
   git-status-clean
   ```

2. **ドライランで確認**
   ```bash
   task-complete-dry 17
   ```

3. **実際に完了**
   ```bash
   task-complete 17
   ```

### 手動でのタスク管理

```bash
# タスクのマークのみ
task-mark 17

# 後でコミット・プッシュ
task-commit 17 "GitHub OIDC化"
```

## 🛡️ 安全性機能

### 自動チェック項目

- **機密情報検出**: パスワード、APIキー、トークンなどの検出
- **大容量ファイル検出**: 10MB以上のファイルの警告
- **環境変数ファイル検出**: `.env`、`.local`ファイルの警告

### 確認プロンプト

システムは以下の場合に確認を求めます：

- 機密情報の可能性があるファイルが検出された場合
- 大容量ファイルが検出された場合
- 最終的なコミット・プッシュ実行前

## 📝 生成されるコミットメッセージ

```
feat: タスク17完了 - GitHub OIDC化

- タスク17の実装を完了
- GitHub OIDC化に関する変更を適用
- 関連ファイルの更新とテスト実行

完了日時: 2025-01-19 14:30:00
Co-authored-by: Kiro AI Assistant <kiro@example.com>
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. タスクが見つからない

```bash
# タスク番号を確認
task-list-all

# 正確な番号で再実行
task-complete 17
```

#### 2. Git操作が失敗する

```bash
# Git状態を確認
git status
git-log-recent

# 必要に応じて手動で解決
git add .
git commit -m "手動コミット"
git push
```

#### 3. 機密情報の警告が出る

```bash
# 変更内容を確認
git-diff-staged

# 問題のあるファイルを除外
git reset HEAD <ファイル名>

# 再実行
task-complete 17
```

## 🎨 カスタマイズ

### タスクファイルの変更

デフォルトでは `.kiro/specs/secure-excel-unlock/tasks.md` を使用しますが、変更可能です：

```python
# scripts/task_manager.py の TaskManager クラス
task_manager = TaskManager("path/to/your/tasks.md")
```

### コミットメッセージのカスタマイズ

`scripts/task_manager.py` の `generate_commit_message` メソッドを編集してください。

### 安全性チェックの調整

`check_sensitive_content` と `check_large_files` メソッドでチェック内容を調整できます。

## 📚 スクリプトファイル構成

```
scripts/
├── auto-commit-task.sh      # Bashベースの自動コミットスクリプト
├── task_manager.py          # Pythonベースのタスク管理スクリプト
├── task-aliases.sh          # エイリアス設定スクリプト
└── README.md               # このドキュメント
```

## 🚀 高度な使用例

### 複数タスクの連続完了

```bash
# 複数のタスクを順次完了
for task in 17 18 19; do
    echo "タスク$task を完了中..."
    task-complete-dry $task
    read -p "実行しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        task-complete $task
    fi
done
```

### 自動化スクリプトとの連携

```bash
# 他のスクリプトから呼び出し
python3 scripts/task_manager.py complete 17 --dry-run
if [ $? -eq 0 ]; then
    python3 scripts/task_manager.py complete 17
fi
```

## 💡 ベストプラクティス

1. **必ずドライランから始める**: `task-complete-dry` で内容確認
2. **定期的なタスク確認**: `task-list` で進捗確認
3. **Git状態の確認**: `git-status-clean` で変更内容確認
4. **段階的な作業**: 大きなタスクは小分けして実行
5. **バックアップの習慣**: 重要な変更前はブランチ作成

## 🔗 関連ドキュメント

- [プロジェクト構成](../structure.md)
- [技術スタック](../.kiro/steering/tech.md)
- [Git操作のベストプラクティス](../.kiro/steering/tech.md#git操作のベストプラクティス)