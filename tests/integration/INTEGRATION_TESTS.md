# 統合テスト実行ガイド

## 概要

このドキュメントでは、Secure Excel Unlockアプリケーションの統合テストの実行方法について説明します。

## テスト構成

### 1. API統合テスト (`api/`)
- 署名付きURL生成APIのテスト
- Excel解除APIのテスト
- 認証・認可のテスト
- エラーハンドリングのテスト

### 2. S3連携テスト (`s3/`)
- ファイルアップロード・ダウンロードのテスト
- 署名付きURLの動作確認
- S3バケット設定の確認
- パフォーマンステスト

### 3. E2Eテスト (`e2e/`)
- 完全なワークフローテスト
- 複数ファイル並列処理テスト
- エラーハンドリングフローテスト
- パフォーマンス測定

## 事前準備

### 1. 環境変数設定

`.env.test.example`を`.env.test`にコピーして設定：

```bash
cp .env.test.example .env.test
```

`.env.test`を編集して実際の値を設定：

```bash
# AWS設定
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-excel-unlock-test-bucket

# API設定
API_BASE_URL=https://your-api-gateway-id.execute-api.ap-northeast-1.amazonaws.com/prod

# テストユーザー設定
TEST_USER_EMAIL=test@example.com
```

### 2. AWS環境準備

```bash
# AWS CLI設定確認
aws configure list
aws sts get-caller-identity

# S3バケット作成（まだ作成していない場合）
aws s3 mb s3://your-excel-unlock-test-bucket --region ap-northeast-1

# Lambda関数デプロイ確認
sam build
sam deploy
```

### 3. 依存関係インストール

```bash
# 統合テスト用依存関係
cd tests/integration
npm install

# フロントエンド依存関係
cd ../../frontend
npm install
```

## テスト実行方法

### 1. 全統合テスト実行

```bash
# プロジェクトルートから
./tests/run-integration-tests.sh all

# または個別に
cd tests/integration
./run-tests.sh all
```

### 2. 個別テスト実行

```bash
# API統合テストのみ
./tests/run-integration-tests.sh api

# S3連携テストのみ
./tests/run-integration-tests.sh s3

# E2Eテストのみ
./tests/run-integration-tests.sh e2e

# バックエンドテストのみ
./tests/run-integration-tests.sh backend

# フロントエンドテストのみ
./tests/run-integration-tests.sh frontend
```

### 3. 詳細オプション

```bash
# 自動クリーンアップ付き実行
./tests/run-integration-tests.sh all cleanup

# クリーンアップなし実行
./tests/run-integration-tests.sh all no-cleanup

# ヘルプ表示
./tests/run-integration-tests.sh --help
```

## テスト環境管理

### セットアップ

```bash
cd tests/integration
npm run setup
```

このコマンドは以下を実行します：
- S3バケットの存在確認
- テスト用ファイルのアップロード
- CORS設定の確認

### クリーンアップ

```bash
cd tests/integration
npm run cleanup

# 強制クリーンアップ（全ファイル削除）
node setup/cleanup-test-environment.js --force
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. AWS認証エラー

```bash
# AWS認証情報確認
aws sts get-caller-identity

# プロファイル設定
aws configure --profile test-profile
export AWS_PROFILE=test-profile
```

#### 2. S3バケットアクセスエラー

```bash
# バケット存在確認
aws s3 ls s3://your-bucket-name

# バケット作成
aws s3 mb s3://your-bucket-name --region ap-northeast-1

# CORS設定確認
aws s3api get-bucket-cors --bucket your-bucket-name
```

#### 3. API Gateway接続エラー

- `API_BASE_URL`が正しく設定されているか確認
- Lambda関数がデプロイされているか確認
- API Gatewayのエンドポイントが有効か確認

#### 4. テストタイムアウト

```bash
# タイムアウト時間を延長
export JEST_TIMEOUT=120000

# 個別テスト実行でデバッグ
npm run test:verbose
```

### ログ確認

```bash
# 統合テスト実行ログ
tail -f tests/integration/test-results.log

# Lambda関数ログ
aws logs tail /aws/lambda/your-function-name --follow

# S3アクセスログ
aws s3api get-bucket-logging --bucket your-bucket-name
```

## パフォーマンス基準

### 期待値

| テスト項目 | 期待値 | 備考 |
|-----------|--------|------|
| 署名付きURL生成 | < 5秒 | P95 |
| ファイルアップロード（1MB） | < 10秒 | 通常ネットワーク |
| Excel解除処理 | < 8秒 | 標準ファイル（P95） |
| ファイルダウンロード（1MB） | < 10秒 | 通常ネットワーク |
| 完全ワークフロー | < 15秒 | 統合テスト許容値 |

### パフォーマンス測定

```bash
# パフォーマンステストのみ実行
npm test -- --testNamePattern="パフォーマンス"

# 詳細測定
npm run test:verbose -- --testNamePattern="処理時間"
```

## CI/CD統合

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

## レポート生成

### テスト結果レポート

```bash
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
```

## セキュリティ考慮事項

### テストデータ

- 実際の機密データは使用しない
- テスト用の模擬データのみ使用
- テスト完了後は必ずクリーンアップ

### 認証情報

- AWS認証情報は環境変数で管理
- テスト用IAMユーザーは最小権限で設定
- 本番環境の認証情報は使用しない

### ネットワーク

- テスト環境専用のS3バケットを使用
- 本番APIエンドポイントへの接続は避ける
- VPC内でのテスト実行を推奨

## 継続的改善

### メトリクス収集

- テスト実行時間の追跡
- 成功率の監視
- パフォーマンス傾向の分析

### テスト拡張

- 新機能追加時のテストケース追加
- エッジケースの継続的発見と追加
- 負荷テストの定期実行

この統合テストガイドに従って、安定した品質の高いアプリケーションを維持してください。