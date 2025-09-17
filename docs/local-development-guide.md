# ローカル開発環境ガイド

## 概要

このガイドでは、Secure Excel Unlockアプリケーションのローカル開発環境の設定と使用方法について説明します。

## 前提条件

- AWS CLI設定済み（`aws configure list`で確認）
- AWS SAM CLI インストール済み
- Node.js 18+ インストール済み
- Python 3.9 インストール済み

## 環境設定

### 1. AWS CLI設定確認

```bash
aws configure list
aws sts get-caller-identity
```

### 2. S3バケット確認

```bash
aws s3 ls | grep excel
```

### 3. 環境変数設定

バックエンド用（`backend/.env.local`）:
```bash
S3_BUCKET_NAME=excel-unlocker-bucket-101271927126-ap-northeast-1
ALLOWED_USERS=user1@example.com,user2@example.com
LOG_LEVEL=DEBUG
AWS_DEFAULT_REGION=ap-northeast-1
```

フロントエンド用（`frontend/.env.local`）:
```bash
# 本番API使用時
NEXT_PUBLIC_USE_MOCK_API=false
NEXT_PUBLIC_API_URL=https://your-api-gateway-url

# ローカルバックエンド使用時
NEXT_PUBLIC_USE_MOCK_API=false
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_LOCAL_BACKEND_TEST=true
```

## ローカルテスト実行

### 1. 自動テストスクリプト実行

```bash
./scripts/test-local-api.sh
```

### 2. 手動テスト

#### SAMビルド
```bash
sam build
```

#### 個別Lambda関数テスト
```bash
# GetUploadUrlFunction テスト
sam local invoke GetUploadUrlFunction --event events/get-upload-url-event.json

# UnlockFunction テスト
sam local invoke UnlockFunction --event events/unlock-event.json
```

#### ローカルAPIサーバー起動
```bash
sam local start-api --port 3001
```

#### APIエンドポイントテスト
```bash
# 署名付きURL生成テスト
curl -X POST http://localhost:3001/presigned-urls \
  -H "Content-Type: application/json" \
  -H "X-User-Email: user1@example.com" \
  -d '{"fileName": "test.xlsx", "fileSize": 1024, "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}'

# Excel解除テスト（テストファイルが必要）
curl -X POST http://localhost:3001/unlock \
  -H "Content-Type: application/json" \
  -H "X-User-Email: user1@example.com" \
  -d '{"fileKey": "uploads/test-file.xlsx", "passwords": ["password1", "password2"]}'
```

### 3. フロントエンド・バックエンド連携テスト

#### ターミナル1: バックエンドAPI起動
```bash
sam local start-api --port 3001
```

#### ターミナル2: フロントエンド起動
```bash
cd frontend
# ローカルバックエンド使用設定に変更
export NEXT_PUBLIC_USE_MOCK_API=false
export NEXT_PUBLIC_API_URL=http://localhost:3001
npm run dev
```

#### ブラウザでテスト
1. http://localhost:3000 にアクセス
2. Google OAuth でログイン（hironomac2025@gmail.com でログイン）
3. ExcelUnlockerコンポーネントでファイルアップロード機能をテスト
4. ブラウザの開発者ツールでネットワークタブを確認し、以下を確認：
   - `/presigned-urls` エンドポイントが呼び出されている
   - `X-User-Email` ヘッダーが送信されている
   - `/unlock` エンドポイントが呼び出されている

#### 認証テスト
- 許可されたユーザー（hironomac2025@gmail.com）でログイン → 正常動作
- 許可されていないユーザーでログイン → アクセス拒否エラー

#### ブラウザでテスト
1. http://localhost:3000 にアクセス
2. Google OAuth でログイン
3. ファイルアップロード機能をテスト
4. ブラウザの開発者ツールでネットワークタブを確認し、ローカルAPIが呼び出されていることを確認

## トラブルシューティング

### よくある問題

#### 1. SAMビルドエラー
```bash
# ビルドディレクトリをクリーンアップ
rm -rf .aws-sam/build
sam build
```

#### 2. Lambda関数の環境変数エラー
- `backend/.env.local`ファイルが正しく設定されているか確認
- AWS認証情報が正しく設定されているか確認

#### 3. CORS エラー
- `template.yaml`のCORS設定を確認
- フロントエンドのAPIエンドポイントURLが正しいか確認

#### 4. S3アクセスエラー
- AWS認証情報の権限を確認
- S3バケットが存在するか確認
- リージョン設定が正しいか確認

### ログ確認

#### Lambda関数ログ
```bash
# ローカル実行時のログは標準出力に表示されます
sam local invoke FunctionName --event events/test-event.json
```

#### APIサーバーログ
```bash
# APIサーバー起動時のログは標準出力に表示されます
sam local start-api --port 3001
```

## デプロイ

### 開発環境へのデプロイ
```bash
sam deploy --guided
```

### 本番環境へのデプロイ
```bash
sam deploy --parameter-overrides Environment=production
```

## 参考資料

- [AWS SAM CLI ドキュメント](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
- [Next.js ドキュメント](https://nextjs.org/docs)
- [プロジェクト要件定義書](.kiro/specs/secure-excel-unlock/requirements.md)
- [プロジェクト設計書](.kiro/specs/secure-excel-unlock/design.md)