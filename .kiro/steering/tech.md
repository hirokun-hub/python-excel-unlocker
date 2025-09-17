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

## 環境変数
- `NEXT_PUBLIC_API_URL`: バックエンドAPIエンドポイント
- `NEXT_PUBLIC_USE_MOCK_API`: 開発用モックモードを有効化
- `S3_BUCKET_NAME`: ファイル保存用S3バケット（Lambda用）
- `LOG_LEVEL`: Lambda関数のログレベル