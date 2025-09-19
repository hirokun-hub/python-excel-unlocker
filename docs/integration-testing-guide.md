# 統合テスト実行ガイド

## 📋 概要

このドキュメントでは、Secure Excel Unlockアプリケーションの統合テストの実行方法について詳しく説明します。統合テストは、フロントエンド・バックエンド間のAPI統合、実際のS3との連携、完全なワークフローのE2Eテストを含みます。

## 🧪 テスト構成

### 1. API統合テスト (`tests/integration/api/`)
- **署名付きURL生成APIテスト**: 正常系・異常系・パフォーマンステスト
- **Excel解除APIテスト**: 認証、エラーハンドリング、日本語メッセージ
- **認証・認可テスト**: ユーザーアクセス制御の確認
- **エラーハンドリングテスト**: 各種エラーケースの動作確認

### 2. S3連携テスト (`tests/integration/s3/`)
- **ファイルアップロード・ダウンロードテスト**: 実際のS3を使用
- **署名付きURL動作確認**: Upload/Download URL の有効性確認
- **S3バケット設定確認**: CORS設定、権限設定の確認
- **パフォーマンステスト**: ファイルサイズ別の処理時間測定

### 3. E2Eテスト (`tests/integration/e2e/`)
- **完全ワークフローテスト**: アップロード→解除→ダウンロード
- **複数ファイル並列処理テスト**: バッチ処理の動作確認
- **エラーハンドリングフローテスト**: 各種エラー時の動作確認
- **パフォーマンス測定**: 全体処理時間の測定

### 4. フロントエンド統合テスト (`frontend/__tests__/integration/`)
- **API統合テスト**: フロントエンドからのAPI呼び出し確認
- **Playwright E2Eテスト**: ブラウザでの実際の操作テスト

## 🚀 クイックスタート

### 全統合テスト実行（推奨）
```bash
# プロジェクトルートから実行
./tests/run-integration-tests.sh all cleanup
```

### 個別テスト実行
```bash
# API統合テストのみ
./tests/run-integration-tests.sh api

# S3連携テストのみ
./tests/run-integration-tests.sh s3

# E2Eテストのみ
./tests/run-integration-tests.sh e2e

# フロントエンドテストのみ
./tests/run-integration-tests.sh frontend
```

## 📋 事前準備

### 1. 必要なツール

#### macOS
```bash
# Homebrew経由でインストール
brew install awscli
brew install aws-sam-cli
npm install -g @playwright/test

# バージョン確認
aws --version          # AWS CLI v2.0+
sam --version          # SAM CLI v1.50+
node --version         # Node.js v18+
```

#### Windows
```powershell
# Chocolatey経由でインストール
choco install awscli
choco install aws-sam-cli
npm install -g @playwright/test
```

### 2. AWS環境設定

```bash
# AWS認証情報確認
aws configure list
aws sts get-caller-identity

# 必要に応じて設定
aws configure
```

### 3. 環境変数設定

#### テスト用環境変数ファイル作成
```bash
# tests/integration/.env.test を作成
cp tests/integration/.env.test.example tests/integration/.env.test
```

#### .env.test の設定例
```bash
# AWS設定
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=excel-unlocker-test-bucket

# API設定
API_BASE_URL=https://your-api-gateway-id.execute-api.ap-northeast-1.amazonaws.com/prod

# テストユーザー設定
TEST_USER_EMAIL=test@example.com
ALLOWED_USERS=test@example.com,user2@example.com

# ログレベル
LOG_LEVEL=INFO
```

### 4. S3テストバケット作成

```bash
# テスト用S3バケット作成
aws s3 mb s3://excel-unlocker-test-bucket --region ap-northeast-1

# バケット存在確認
aws s3 ls | grep excel-unlocker-test
```

### 5. Lambda関数デプロイ

```bash
# バックエンドデプロイ
sam build
sam deploy --config-env default
```

## 🧪 詳細テスト実行方法

### 統合テスト実行スクリプト

#### 基本的な使用方法
```bash
# 使用方法表示
./tests/run-integration-tests.sh --help

# 全テスト実行（クリーンアップ確認あり）
./tests/run-integration-tests.sh all

# 全テスト実行（自動クリーンアップ）
./tests/run-integration-tests.sh all cleanup

# 全テスト実行（クリーンアップなし）
./tests/run-integration-tests.sh all no-cleanup
```

#### 個別テスト実行
```bash
# バックエンド統合テストのみ
./tests/run-integration-tests.sh backend

# フロントエンド統合テストのみ
./tests/run-integration-tests.sh frontend

# API統合テストのみ
./tests/run-integration-tests.sh api

# S3連携テストのみ
./tests/run-integration-tests.sh s3

# E2Eテストのみ
./tests/run-integration-tests.sh e2e
```

### 手動テスト実行

#### バックエンド統合テスト
```bash
cd tests/integration

# 依存関係インストール
npm install

# テスト環境セットアップ
npm run setup

# 全テスト実行
npm test

# 個別テスト実行
npm run test:api
npm run test:s3
npm run test:e2e

# クリーンアップ
npm run cleanup
```

#### フロントエンド統合テスト
```bash
cd frontend

# 依存関係確認
npm install

# API統合テスト
npm run test -- __tests__/integration/

# Playwright E2Eテスト
npx playwright install  # 初回のみ
npm run test:e2e -- e2e/integration.spec.ts
```

## 📊 パフォーマンス基準

### 期待値

| テスト項目 | 期待値 | 測定条件 |
|-----------|--------|----------|
| 署名付きURL生成 | < 5秒 | P95 |
| ファイルアップロード（1MB） | < 10秒 | 通常ネットワーク |
| Excel解除処理 | < 8秒 | 標準ファイル（P95） |
| ファイルダウンロード（1MB） | < 10秒 | 通常ネットワーク |
| 完全ワークフロー | < 15秒 | 統合テスト許容値 |

### パフォーマンス測定

```bash
# パフォーマンステストのみ実行
cd tests/integration
npm test -- --testNamePattern="パフォーマンス"

# 詳細測定結果出力
npm run test:verbose -- --testNamePattern="処理時間"
```

## 🔧 テスト環境管理

### 自動セットアップ

```bash
cd tests/integration

# テスト環境の自動セットアップ
npm run setup
```

このコマンドは以下を実行します：
- S3バケットの存在確認・作成
- テスト用ファイルのアップロード
- CORS設定の確認・適用
- Lambda関数の動作確認

### 自動クリーンアップ

```bash
cd tests/integration

# 通常のクリーンアップ
npm run cleanup

# 強制クリーンアップ（全ファイル削除）
node setup/cleanup-test-environment.js --force
```

### 手動環境確認

```bash
# S3バケット確認
aws s3 ls s3://excel-unlocker-test-bucket

# Lambda関数確認
aws lambda list-functions --query 'Functions[?contains(FunctionName, `excel`)]'

# API Gateway確認
aws apigateway get-rest-apis --query 'items[?contains(name, `excel`)]'
```

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. AWS認証エラー

**エラー**: `Unable to locate credentials`
```bash
# 解決方法
aws configure
# または
export AWS_PROFILE=your-profile-name
```

**エラー**: `AccessDenied`
```bash
# IAM権限確認
aws iam get-user
aws sts get-caller-identity

# 必要な権限
# - S3: Full Access (テストバケット)
# - Lambda: Read Access
# - API Gateway: Read Access
```

#### 2. S3バケットエラー

**エラー**: `NoSuchBucket`
```bash
# バケット作成
aws s3 mb s3://excel-unlocker-test-bucket --region ap-northeast-1

# バケット存在確認
aws s3 ls | grep excel-unlocker
```

**エラー**: `CORSConfigurationNotFound`
```bash
# CORS設定確認
aws s3api get-bucket-cors --bucket excel-unlocker-test-bucket

# CORS設定適用
cd tests/integration
npm run setup
```

#### 3. Lambda関数エラー

**エラー**: `Function not found`
```bash
# Lambda関数デプロイ確認
sam build
sam deploy

# 関数一覧確認
aws lambda list-functions --query 'Functions[?contains(FunctionName, `excel`)]'
```

#### 4. API Gateway接続エラー

**エラー**: `ECONNREFUSED`
```bash
# API_BASE_URL確認
echo $API_BASE_URL

# API Gateway URL取得
aws apigateway get-rest-apis --query 'items[?contains(name, `excel`)].{id:id,name:name}'
```

#### 5. フロントエンドテストエラー

**エラー**: `Playwright browser not found`
```bash
# Playwrightブラウザインストール
cd frontend
npx playwright install
```

**エラー**: `getSession is not defined`
```bash
# Next.js認証モック確認
cd frontend
npm run test -- --verbose __tests__/integration/
```

### ログ確認方法

#### 統合テストログ
```bash
# テスト実行ログ
tail -f tests/integration/test-results.log

# 詳細ログ出力
cd tests/integration
npm run test:verbose
```

#### AWS サービスログ
```bash
# Lambda関数ログ
aws logs tail /aws/lambda/excel-unlock-function --follow

# API Gateway ログ
aws logs describe-log-groups --log-group-name-prefix "/aws/apigateway"
```

### デバッグモード

```bash
# デバッグモードでテスト実行
cd tests/integration
DEBUG=* npm test

# 特定のテストのみデバッグ
npm test -- --testNamePattern="署名付きURL" --verbose
```

## 📈 CI/CD統合

### GitHub Actions設定例

```yaml
name: Integration Tests
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # 毎日2時に実行

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
          
      - name: Run Integration Tests
        run: ./tests/run-integration-tests.sh all cleanup
        env:
          S3_BUCKET_NAME: ${{ secrets.TEST_S3_BUCKET }}
          API_BASE_URL: ${{ secrets.TEST_API_URL }}
          TEST_USER_EMAIL: ${{ secrets.TEST_USER_EMAIL }}
```

### 定期実行設定

```bash
# crontabで定期実行設定
crontab -e

# 毎日午前2時に実行
0 2 * * * cd /path/to/project && ./tests/run-integration-tests.sh all cleanup > /tmp/integration-test.log 2>&1
```

## 📊 レポート生成

### テスト結果レポート

```bash
cd tests/integration

# カバレッジ付きテスト実行
npm run test:coverage

# JUnit形式レポート生成
npm test -- --reporters=jest-junit

# HTML形式レポート生成
npm test -- --reporters=jest-html-reporter
```

### パフォーマンスレポート

```bash
# パフォーマンス測定結果をJSON出力
npm test -- --testNamePattern="パフォーマンス" --json > performance-results.json

# 結果の可視化
node utils/generate-performance-report.js performance-results.json
```

### カスタムレポート

```bash
# テスト結果サマリー生成
npm run test:summary

# 失敗テストの詳細レポート
npm run test:failures
```

## 🔒 セキュリティ考慮事項

### テストデータ管理

- **実際の機密データは使用しない**: テスト用の模擬データのみ使用
- **テスト完了後は必ずクリーンアップ**: 一時ファイルの確実な削除
- **認証情報の適切な管理**: 環境変数での管理、本番認証情報の分離

### 権限管理

```bash
# テスト用IAMユーザーの最小権限設定例
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::excel-unlocker-test-*",
        "arn:aws:s3:::excel-unlocker-test-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:*:function:excel-*-test"
    }
  ]
}
```

### ネットワークセキュリティ

- **テスト環境専用のリソース使用**: 本番環境との分離
- **VPC内でのテスト実行推奨**: セキュアなネットワーク環境
- **アクセスログの監視**: 不正アクセスの検出

## 🔄 継続的改善

### メトリクス収集

```bash
# テスト実行時間の追跡
npm run test:metrics

# 成功率の監視
npm run test:success-rate

# パフォーマンス傾向の分析
npm run test:performance-trend
```

### テスト拡張

- **新機能追加時のテストケース追加**: 機能追加と同時にテスト追加
- **エッジケースの継続的発見**: 実運用での問題をテストケース化
- **負荷テストの定期実行**: パフォーマンス劣化の早期発見

### 品質向上

```bash
# テストカバレッジの向上
npm run test:coverage-report

# テストコードの品質チェック
npm run lint:test

# テストの実行時間最適化
npm run test:optimize
```

## 📚 参考資料

### 公式ドキュメント
- [Jest Testing Framework](https://jestjs.io/docs/getting-started)
- [Playwright Testing](https://playwright.dev/docs/intro)
- [AWS SDK for JavaScript](https://docs.aws.amazon.com/sdk-for-javascript/)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)

### 関連ドキュメント
- [ローカル開発環境ガイド](local-development-guide.md)
- [段階的デプロイメントガイド](deployment-guide.md)
- [認証・API統合ガイド](authentication-integration-guide.md)
- [実装完了サマリー](implementation-complete-summary.md)

---

## 🎯 まとめ

この統合テストガイドに従って、以下を実現できます：

- ✅ **包括的なテスト実行**: API・S3・E2E・フロントエンドの全統合テスト
- ✅ **自動化されたテスト環境**: セットアップ・実行・クリーンアップの自動化
- ✅ **パフォーマンス監視**: 処理時間・成功率の継続的監視
- ✅ **CI/CD統合**: GitHub Actionsでの自動テスト実行
- ✅ **品質保証**: 高品質なアプリケーションの継続的な維持

統合テストを定期的に実行することで、安定した品質の高いSecure Excel Unlockアプリケーションを維持できます。

---

**📞 サポート**: 問題が発生した場合は、このドキュメントのトラブルシューティングセクションを参照するか、関連ドキュメントを確認してください。