# 段階的デプロイメントガイド

## 概要

Excel Unlocker アプリケーションの段階的デプロイメント手順を説明します。開発環境から本番環境まで、安全で確実なデプロイメントを実現します。

## 環境構成

### 環境一覧

| 環境 | 用途 | デプロイ方法 | 承認 |
|------|------|-------------|------|
| **Development** | 開発・テスト | 自動 (develop ブランチ) | 不要 |
| **Staging** | 本番前検証 | 自動 (main ブランチ) | 不要 |
| **Production** | 本番運用 | 手動 (workflow_dispatch) | 必要 |

### 環境別設定

#### Development
- **スタック名**: `excel-unlocker-api-dev`
- **S3バケット**: `excel-unlocker-bucket-development-{account-id}-ap-northeast-1`
- **許可ユーザー**: `hironomac2025@gmail.com`
- **ログレベル**: `INFO`

#### Staging
- **スタック名**: `excel-unlocker-api-staging`
- **S3バケット**: `excel-unlocker-bucket-staging-{account-id}-ap-northeast-1`
- **許可ユーザー**: `hironomac2025@gmail.com,staging-user@example.com`
- **ログレベル**: `INFO`

#### Production
- **スタック名**: `excel-unlocker-api-prod`
- **S3バケット**: `excel-unlocker-bucket-production-{account-id}-ap-northeast-1`
- **許可ユーザー**: `hironomac2025@gmail.com,user2@nsc.co.jp,user3@nsc.co.jp`
- **ログレベル**: `WARN`

## 前提条件

### 必要なツール

1. **AWS CLI** (v2.0+)
   ```bash
   aws --version
   aws configure list
   ```

2. **AWS SAM CLI** (v1.50+)
   ```bash
   sam --version
   ```

3. **Node.js** (v18+)
   ```bash
   node --version
   npm --version
   ```

4. **Vercel CLI** (フロントエンド用)
   ```bash
   npm install -g vercel
   vercel --version
   ```

### AWS認証設定

```bash
# AWS認証確認
aws sts get-caller-identity

# 必要に応じて設定
aws configure
```

### GitHub Secrets設定

以下のシークレットをGitHubリポジトリに設定してください：

#### AWS関連
- `AWS_ACCESS_KEY_ID`: AWSアクセスキーID
- `AWS_SECRET_ACCESS_KEY`: AWSシークレットアクセスキー

#### Vercel関連
- `VERCEL_TOKEN`: Vercelアクセストークン
- `VERCEL_ORG_ID`: Vercel組織ID
- `VERCEL_PROJECT_ID`: VercelプロジェクトID

#### 環境変数
- `NEXTAUTH_SECRET`: NextAuth.jsシークレット
- `GOOGLE_CLIENT_ID`: Google OAuth クライアントID
- `GOOGLE_CLIENT_SECRET`: Google OAuth クライアントシークレット

## デプロイメント手順

### 1. 開発環境デプロイ

#### 自動デプロイ（推奨）
```bash
# developブランチにプッシュ
git checkout develop
git add .
git commit -m "feat: 新機能追加"
git push origin develop
```

#### 手動デプロイ
```bash
# スクリプト使用
./scripts/deploy.sh development all

# または個別デプロイ
./scripts/deploy.sh development backend
./scripts/deploy.sh development frontend
```

#### SAM直接実行
```bash
# バックエンドのみ
sam build
sam deploy --config-env default --no-confirm-changeset
```

### 2. ステージング環境デプロイ

#### 自動デプロイ（推奨）
```bash
# mainブランチにマージ
git checkout main
git merge develop
git push origin main
```

#### 手動デプロイ
```bash
./scripts/deploy.sh staging all
```

### 3. 本番環境デプロイ

#### GitHub Actions経由（推奨）
1. GitHubリポジトリの「Actions」タブを開く
2. 「Deploy Backend to AWS」または「Deploy Frontend to Vercel」を選択
3. 「Run workflow」をクリック
4. Environment: `production` を選択
5. 「Run workflow」を実行
6. 手動承認後にデプロイ実行

#### 手動デプロイ
```bash
# 確認プロンプト付き
./scripts/deploy.sh production all

# SAM直接実行（バックエンドのみ）
sam build
sam deploy --config-env production --confirm-changeset
```

## モニタリング・アラート

### CloudWatch Dashboard

各環境にCloudWatchダッシュボードが自動作成されます：

- **Development**: `ExcelUnlocker-Dashboard-development`
- **Staging**: `ExcelUnlocker-Dashboard-staging`
- **Production**: `ExcelUnlocker-Dashboard-production`

### アラート設定

以下のアラートが自動設定されます：

1. **高エラー率アラート**
   - 条件: 5分間で5回以上のエラー
   - 通知: SNS経由でメール送信

2. **高レイテンシアラート**
   - 条件: 平均処理時間が10秒を超過
   - 通知: SNS経由でメール送信

### ログ確認

```bash
# Lambda関数ログ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/excel"

# 最新ログ取得
aws logs tail /aws/lambda/excel-unlock-function-production --follow
```

## トラブルシューティング

### よくある問題

#### 1. デプロイ失敗: IAM権限不足
```bash
# 現在の権限確認
aws iam get-user
aws sts get-caller-identity

# 必要な権限
# - CloudFormation: Full Access
# - Lambda: Full Access
# - S3: Full Access
# - IAM: Create/Update Roles
```

#### 2. S3バケット名重複エラー
```bash
# バケット名確認
aws s3 ls | grep excel-unlocker

# 既存バケット削除（注意：データ消失）
aws s3 rb s3://excel-unlocker-bucket-development-{account-id}-ap-northeast-1 --force
```

#### 3. Lambda関数タイムアウト
```bash
# 関数設定確認
aws lambda get-function-configuration --function-name excel-unlock-function-production

# タイムアウト値調整（template.yamlで設定）
# Timeout: 900  # 15分
```

#### 4. API Gateway CORS エラー
```bash
# CORS設定確認
aws apigateway get-rest-apis

# フロントエンドからのテスト
curl -X OPTIONS https://your-api-url/presigned-urls \
  -H "Origin: https://your-frontend-url" \
  -H "Access-Control-Request-Method: POST"
```

### ログ分析

#### エラーパターン確認
```bash
# エラーログ検索
aws logs filter-log-events \
  --log-group-name "/aws/lambda/excel-unlock-function-production" \
  --filter-pattern "ERROR"

# 特定期間のログ
aws logs filter-log-events \
  --log-group-name "/aws/lambda/excel-unlock-function-production" \
  --start-time $(date -d "1 hour ago" +%s)000
```

## セキュリティ考慮事項

### 本番環境での注意点

1. **アクセス制御**
   - 許可ユーザーリストの定期見直し
   - 不要なアカウントの削除

2. **ログ管理**
   - 機密情報のログ出力禁止
   - ログ保持期間の設定

3. **ネットワークセキュリティ**
   - API Gateway の適切なCORS設定
   - S3バケットのパブリックアクセス禁止

### 定期メンテナンス

#### 月次作業
- [ ] CloudWatchメトリクス確認
- [ ] S3ストレージ使用量確認
- [ ] Lambda関数パフォーマンス確認
- [ ] セキュリティアラート確認

#### 四半期作業
- [ ] 依存関係の更新
- [ ] セキュリティパッチ適用
- [ ] アクセス権限の見直し
- [ ] バックアップ・復旧テスト

## 参考リンク

- [AWS SAM CLI ユーザーガイド](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
- [Vercel デプロイメントガイド](https://vercel.com/docs/concepts/deployments/overview)
- [GitHub Actions ワークフロー構文](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [CloudWatch アラーム設定](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)