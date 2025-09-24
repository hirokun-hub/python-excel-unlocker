# CI/CDワークフロー実行パターン詳細

## 実行パターン一覧

### 1. 開発ブランチ（develop）へのプッシュ

**トリガー条件:**
- `git push origin develop`
- backend/またはfrontend/配下のファイル変更

**実行フロー:**

#### バックエンド変更時
```
deploy-backend.yml
├── 環境判定: develop → development
├── deploy-aws.yml呼び出し
│   ├── Python環境セットアップ
│   ├── pytest実行（backend/tests/unit/）
│   ├── SAMビルド・デプロイ（excel-unlocker-api-dev）
│   ├── API Gateway URL取得
│   ├── Vercel環境変数更新
│   └── 基本的な疎通確認
└── 完了サマリー生成
```

#### フロントエンド変更時
```
deploy-frontend.yml
├── 環境判定: develop → development
├── validate-frontend.yml呼び出し
│   ├── Node.js環境セットアップ
│   ├── TypeScript型チェック
│   ├── ESLint実行
│   └── Jest単体テスト
├── build-frontend.yml呼び出し
│   ├── 環境別API URL決定
│   ├── Vercel環境情報取得
│   ├── Vercelビルド実行
│   └── アーティファクトアップロード
├── deploy-vercel-reusable.yml呼び出し
│   ├── アーティファクトダウンロード
│   ├── Vercelデプロイ実行
│   └── デプロイURL出力
└── e2e-test-frontend.yml呼び出し
    ├── Playwright環境セットアップ
    ├── E2Eテスト実行
    └── テスト結果レポート
```

### 2. メインブランチ（main）へのプッシュ

**トリガー条件:**
- `git push origin main`（通常はdevelopからのマージ）
- backend/またはfrontend/配下のファイル変更

**実行フロー:**
- バックエンド: developと同様だが環境がstaging
- フロントエンド: developと同様だが**E2Eテストはスキップ**

**環境設定:**
- AWSスタック: excel-unlocker-api-staging
- Vercel環境: preview
- E2Eテスト: 実行されない（mainブランチ除外条件）

### 3. プルリクエスト作成時

**トリガー条件:**
- Pull Request → main
- backend/またはfrontend/配下のファイル変更

**実行フロー:**
```
deploy-backend.yml（テストのみ）
├── skip_deploy: true設定
└── deploy-aws.yml呼び出し
    ├── Python環境セットアップ
    ├── pytest実行
    └── デプロイ処理スキップ

deploy-frontend.yml（検証・ビルドのみ）
├── validate-frontend.yml呼び出し
├── build-frontend.yml呼び出し
└── デプロイ・E2Eテストスキップ
```

### 4. 手動本番デプロイ（deploy-full-stack.yml）

**トリガー条件:**
- GitHub Actions画面での手動実行
- environment: production選択

**実行フロー:**
```
deploy-full-stack.yml
├── deploy-aws.yml呼び出し
│   ├── 本番環境デプロイ（excel-unlocker-api-prod）
│   └── API Gateway URL出力
├── deploy-vercel-reusable.yml呼び出し
│   ├── 本番環境デプロイ（--prodフラグ）
│   └── 本番URL出力
├── integration-test実行
│   ├── 統合テストまたは疎通確認
│   ├── フロントエンド疎通確認
│   └── API疎通確認（認証エラー期待）
└── deployment-complete
    └── 完了サマリー生成
```

## 環境別実行マトリックス

| 実行パターン | 環境 | pytest | ESLint/TypeCheck | Jest | ビルド | デプロイ | E2E | 統合テスト |
|-------------|------|--------|------------------|------|--------|----------|-----|------------|
| develop push | development | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| main push | staging | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| PR作成 | - | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 手動本番 | production | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |

## 認証方式の実行パターン

### GitHub OIDC使用時
```yaml
# 環境変数設定
AWS_GITHUB_ACTIONS_ROLE_ARN: arn:aws:iam::ACCOUNT:role/GitHubActionsRole

# 実行フロー
1. permissions: id-token: write設定
2. aws-actions/configure-aws-credentials@v4でロール引き受け
3. 一時的なAWSクレデンシャル取得
4. SAM CLI実行
```

### アクセスキー使用時（フォールバック）
```yaml
# GitHub Secrets設定
AWS_ACCESS_KEY_ID: AKIA...
AWS_SECRET_ACCESS_KEY: ...

# 実行フロー
1. AWS_GITHUB_ACTIONS_ROLE_ARNが空の場合に実行
2. aws-actions/configure-aws-credentials@v4でアクセスキー設定
3. SAM CLI実行
```

## エラーハンドリングパターン

### 1. テスト失敗時
- **pytest失敗**: ワークフロー停止、デプロイ実行されない
- **ESLint/TypeCheck失敗**: ワークフロー停止、ビルド実行されない
- **Jest失敗**: ワークフロー停止、ビルド実行されない

### 2. デプロイ失敗時
- **SAMデプロイ失敗**: エラーログ出力、後続処理停止
- **Vercelデプロイ失敗**: エラーログ出力、E2Eテストスキップ

### 3. E2Eテスト失敗時
- **Playwright失敗**: エラーログ出力、デプロイは成功扱い
- **統合テスト失敗**: エラーログ出力、デプロイは成功扱い

## パフォーマンス特性

### 実行時間目安
- **バックエンドのみ**: 3-5分（pytest + SAMデプロイ）
- **フロントエンドのみ**: 8-12分（検証 + ビルド + デプロイ + E2E）
- **フルスタック手動**: 10-15分（統合テスト含む）

### キャッシュ活用
- **Node.js依存関係**: package-lock.jsonベースのキャッシュ
- **Python依存関係**: requirements.txtベースのキャッシュ
- **SAMビルド成果物**: template.yaml + backend/src/**ベースのキャッシュ

### 並列実行
- **backend/とfrontend/同時変更**: 2つのワークフローが並列実行
- **再利用可能ワークフロー内**: ジョブは順次実行（依存関係あり）

## 出力とアーティファクト

### GitHub Actions Summary
- **deploy-full-stack.yml**: 詳細な実行結果サマリー
- **deploy-aws.yml**: 環境情報とAPI URL
- **その他**: 基本的な実行ログのみ

### アーティファクト
- **vercel-build-output**: フロントエンドビルド成果物（1日保持）
- **coverage.xml**: バックエンドテストカバレッジ（Codecov連携）

### 環境変数更新
- **Vercel環境変数**: deploy-aws.ymlでNEXT_PUBLIC_API_URL自動更新
- **samconfig.toml**: 手動メンテナンス必要

この詳細な実行パターンにより、開発者は各シナリオでの動作を正確に把握し、適切な開発フローを選択できます。