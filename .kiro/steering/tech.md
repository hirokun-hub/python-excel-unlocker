# 技術スタック

## フロントエンド
- **フレームワーク**: Next.js 15.4 with React 19（全ドキュメント統一）
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS with shadcn/ui components
- **認証**: Auth.js（旧 NextAuth.js）with Google OAuth + X-User-Emailヘッダー認証
- **HTTPクライアント**: Axios
- **API呼び出し**: フロントエンドから API Gateway を直接呼び出す。Next.js API ルートは開発・デバッグ用途のみ
- **認証連携**: セッション情報からX-User-Emailヘッダーを自動付与してバックエンドAPI呼び出し
- **テスト**: Jest + React Testing Library, Playwright for E2E
- **ビルドツール**: Turbopack (Next.js built-in)

## バックエンド
- **ランタイム**: Python 3.9 on AWS Lambda
- **フレームワーク**: AWS SAM (Serverless Application Model)
- **ストレージ**: AWS S3 with CORS configuration
- **Excel処理**: msoffcrypto-tool, openpyxl
- **AWS SDK**: boto3
- **認証**: 環境変数ベースのユーザー許可リスト + メールアドレス正規化
- **テスト**: pytest with moto for AWS mocking

## インフラストラクチャ
- **デプロイ**: AWS SAM CLI
- **リージョン**: ap-northeast-1 (Tokyo)
- **API**: AWS API Gateway with Lambda integration
- **ストレージ**: S3 bucket with presigned URLs for file operations

## GitHub Actions実装指針

### 再利用可能ワークフロー設計
- **分離原則**: 呼び出し側（ci.yml）と呼び出され側（ai-artifacts.yml）を明確に分離
- **パラメータ化**: `workflow_call`でinputsを定義し、柔軟な実行制御を実現
- **視覚的明確性**: ワークフロー名とジョブ名で何をしているかを明確に表示

### 堅牢性の確保
- **`if: always()`**: アーティファクト生成は必ず実行（テスト失敗時でも）
- **`continue-on-error: true`**: 依存インストール等のベストエフォート処理
- **差分限定実行**: `tj-actions/changed-files`で変更ファイルのみ処理

### 軽量化戦略
- **重いテスト停止**: CodeQL、フルE2E、統合テストは週1または手動実行
- **差分限定**: TypeScript型チェック、ESLint、テスト実行を変更ファイルに限定
- **AI向け特化**: 原因特定に必要な「事実と文脈」の収集に集中

## よく使うコマンド

### フロントエンド開発
```bash
cd frontend
npm run dev          # 開発サーバーをポート3000で起動
npm run dev:3001     # ポート3001で起動
npm run build        # プロダクションビルド
npm run test         # ユニットテスト実行
npm run test:e2e     # Playwright E2Eテスト実行
npm run lint         # ESLintチェック
```

### バックエンド開発
```bash
cd backend
pip install -r src/requirements.txt  # 依存関係をインストール
pytest                               # テスト実行
pytest --cov                        # カバレッジ付きテスト実行
```

### AWSデプロイ
```bash
sam build                    # アプリケーションをビルド
sam deploy --guided         # プロンプト付きデプロイ（初回）
sam deploy                   # 保存済み設定でデプロイ
sam local start-api          # APIをローカルで実行
```

## Git操作のベストプラクティス

### GitHubにプッシュする前の必須確認手順
```bash
# 1. 現在のgit状態を確認
git status

# 2. 変更内容を詳細確認
git diff

# 3. ステージングされた変更を確認（addした後）
git diff --cached

# 4. コミット履歴を確認
git log --oneline -5

# 5. リモートとの差分を確認
git fetch
git log HEAD..origin/main --oneline
```

### 安全なプッシュ手順
```bash
# 1. 状態確認
git status

# 2. 必要なファイルのみをステージング
git add <specific-files>

# 3. ステージング内容を再確認
git diff --cached

# 4. コミット
git commit -m "適切なコミットメッセージ"

# 5. プッシュ前にリモートの最新状態を取得
git fetch

# 6. 必要に応じてリベースまたはマージ
git rebase origin/main  # または git merge origin/main

# 7. プッシュ
git push origin <branch-name>
```

### 重要な注意事項
- **絶対に `git add .` や `git add -A` を使用する前に `git status` で確認する**
- **機密情報（API キー、パスワード等）が含まれていないか確認する**
- **`.env.local` や設定ファイルが意図せずコミットされていないか確認する**
- **大きなファイルやビルド成果物が含まれていないか確認する**

## タスク自動化システム

### タスク完了時の自動コミット・プッシュ機能
プロジェクトには、タスクリストの作業完了時に自動的にコミット・プッシュを行う機能が実装されています。

#### 利用可能なコマンド
```bash
# エイリアス設定（初回のみ）
source scripts/task-aliases.sh

# タスク確認
task-list              # 未完了タスクの一覧
task-list-all          # 全タスクの一覧（完了済み含む）

# タスク完了
task-complete-dry 17   # ドライラン（推奨）
task-complete 17       # 実際にタスクを完了

# 個別操作
task-mark 17           # タスクを完了済みにマークのみ
task-commit 17 "タイトル"  # コミット・プッシュのみ
```

#### 自動化される処理
1. **タスクファイル更新**: `[ ]` を `[x]` に自動変更
2. **安全性チェック**: 機密情報・大容量ファイルの検出
3. **自動コミット**: 統一されたコミットメッセージで実行
4. **自動プッシュ**: 現在のブランチにプッシュ

#### 生成されるコミットメッセージ形式
```
feat: タスク17完了 - GitHub OIDC化

- タスク17の実装を完了
- GitHub OIDC化に関する変更を適用
- 関連ファイルの更新とテスト実行

完了日時: 2025-01-19 14:30:00
Co-authored-by: Kiro AI Assistant <kiro@example.com>
```

#### 安全性機能
- **機密情報検出**: パスワード、APIキー、トークン等の自動検出
- **大容量ファイルチェック**: 10MB以上のファイルの警告
- **確認プロンプト**: 実行前の最終確認
- **ドライラン**: 実際の操作前の内容確認

#### ベストプラクティス
1. **必ずドライランから始める**: `task-complete-dry` で内容確認
2. **定期的なタスク確認**: `task-list` で進捗確認
3. **段階的な作業**: 大きなタスクは小分けして実行

#### 関連ファイル
- `scripts/task_manager.py`: メインのタスク管理スクリプト
- `scripts/auto-commit-task.sh`: Bashベースの自動コミットスクリプト
- `scripts/task-aliases.sh`: エイリアス設定スクリプト
- `docs/task-automation-guide.md`: 詳細な使用方法ガイド

## 環境変数
- `NEXT_PUBLIC_API_URL`: バックエンドAPIエンドポイント
- `NEXT_PUBLIC_USE_MOCK_API`: 開発用モックモードを有効化
- `S3_BUCKET_NAME`: ファイル保存用S3バケット（Lambda用）
- `LOG_LEVEL`: Lambda関数のログレベル