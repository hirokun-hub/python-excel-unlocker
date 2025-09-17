# 技術スタック

## フロントエンド
- **フレームワーク**: Next.js 15.4.2 with React 19
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS with shadcn/ui components
- **認証**: NextAuth.js with Google OAuth
- **HTTPクライアント**: Axios
- **テスト**: Jest + React Testing Library, Playwright for E2E
- **ビルドツール**: Turbopack (Next.js built-in)

## バックエンド
- **ランタイム**: Python 3.9 on AWS Lambda
- **フレームワーク**: AWS SAM (Serverless Application Model)
- **ストレージ**: AWS S3 with CORS configuration
- **Excel処理**: msoffcrypto-tool, openpyxl
- **AWS SDK**: boto3
- **テスト**: pytest with moto for AWS mocking

## インフラストラクチャ
- **デプロイ**: AWS SAM CLI
- **リージョン**: ap-northeast-1 (Tokyo)
- **API**: AWS API Gateway with Lambda integration
- **ストレージ**: S3 bucket with presigned URLs for file operations

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

## 環境変数
- `NEXT_PUBLIC_API_URL`: バックエンドAPIエンドポイント
- `NEXT_PUBLIC_USE_MOCK_API`: 開発用モックモードを有効化
- `S3_BUCKET_NAME`: ファイル保存用S3バケット（Lambda用）
- `LOG_LEVEL`: Lambda関数のログレベル