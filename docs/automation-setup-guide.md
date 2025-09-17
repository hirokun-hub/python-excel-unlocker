# 自動化セットアップガイド

## 概要

Excel Unlocker の本番運用環境を**最小限の手作業**で構築するための自動化ガイドです。従来の手作業による設定を大幅に削減し、約10分の事前準備 + 自動化処理で完全なデプロイメント環境を構築できます。

## 🎯 自動化の効果

### 従来の手作業（約60分）
- ❌ GitHub Secrets の個別設定（15分）
- ❌ AWS IAM ポリシーの手動作成（10分）
- ❌ Vercel 環境変数の個別設定（15分）
- ❌ 各種認証情報の手動入力（10分）
- ❌ 設定ミスによるトラブルシューティング（10分）

### 自動化後（約15分）
- ✅ 事前準備（Google/AWS/Vercel での認証情報取得）: 10分
- ✅ 自動化スクリプト実行: 5分
- ✅ 設定ミス防止・一貫性保証

## 📋 事前準備（手作業必須項目）

以下の3つのサービスで認証情報を取得する必要があります：

### 1. Google Cloud Console（5分）
```
目的: Google OAuth認証の設定
手順:
1. https://console.cloud.google.com/ にアクセス
2. プロジェクト選択 → APIとサービス → OAuth同意画面
3. 認証情報 → OAuth クライアントID作成
4. 承認済みのリダイレクトURI設定:
   - https://your-domain.com/api/auth/callback/google
   - https://*.vercel.app/api/auth/callback/google
5. 承認済みのJavaScript生成元設定:
   - https://your-domain.com
   - https://*.vercel.app

取得する値:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
```

### 2. AWS Console（3分）
```
目的: GitHub Actions用のAWSアクセス
手順:
1. https://console.aws.amazon.com/iam/ にアクセス
2. ユーザー → ユーザーを追加 → github-deploy-bot
3. プログラムによるアクセス有効化
4. 最小権限ポリシーをアタッチ（自動生成されます）
5. アクセスキー発行

取得する値:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
```

### 3. Vercel Dashboard（2分）
```
目的: GitHub ActionsからのVercelデプロイ
手順:
1. https://vercel.com/account/tokens にアクセス
2. トークン作成（名前: github-actions-token）
3. プロジェクト → Settings → General で ID確認

取得する値:
- VERCEL_TOKEN
- VERCEL_ORG_ID (自動取得)
- VERCEL_PROJECT_ID (自動取得)
```

## 🚀 自動化実行手順

### 方法1: 完全自動化（推奨）

```bash
# 1. 完全自動化スクリプト実行
./scripts/setup-complete-automation.sh
```

このスクリプトが以下を自動実行します：
1. 前提条件チェック
2. GitHub Secrets設定
3. AWS IAMポリシー生成
4. Vercel環境変数設定
5. 初回デプロイ実行
6. CI/CDパイプラインテスト

### 方法2: 段階的実行

```bash
# 1. シークレット設定
./scripts/setup-secrets-automation.sh

# 2. Vercel設定
./scripts/setup-vercel-automation.sh

# 3. 初回デプロイ
./scripts/setup-deployment.sh

# 4. 段階的デプロイテスト
./scripts/deploy.sh development all
```

## 📊 自動化スクリプト詳細

### setup-secrets-automation.sh
**目的**: GitHub Secrets と認証設定の自動化

**自動化内容**:
- ✅ NEXTAUTH_SECRET の自動生成
- ✅ AWS アカウント情報の自動取得
- ✅ GitHub Secrets の一括設定
- ✅ AWS IAM最小権限ポリシーの生成
- ✅ 設定ファイル（.deployment-config.json）の作成

**手作業部分**:
- Google OAuth認証情報の入力
- Vercel認証情報の入力
- AWS認証情報の入力

### setup-vercel-automation.sh
**目的**: Vercel環境設定の自動化

**自動化内容**:
- ✅ Vercel CLI認証確認
- ✅ プロジェクト情報の自動取得
- ✅ Production/Preview環境変数の一括設定
- ✅ テストデプロイの実行

**手作業部分**:
- 本番/ステージングURL の入力
- Git連携解除の確認
- ドメイン設定（オプション）

### setup-complete-automation.sh
**目的**: 全体統合とオーケストレーション

**自動化内容**:
- ✅ 全スクリプトの順次実行
- ✅ 進捗表示とエラーハンドリング
- ✅ 最終確認と次のステップ案内
- ✅ 設定サマリーの出力

## 🔧 生成されるファイル

### .deployment-config.json
```json
{
  "project_name": "excel-unlocker",
  "aws_region": "ap-northeast-1",
  "environments": {
    "development": { "stack_name": "excel-unlocker-api-dev" },
    "staging": { "stack_name": "excel-unlocker-api-staging" },
    "production": { "stack_name": "excel-unlocker-api-prod" }
  },
  "secrets": {
    "generated": { "NEXTAUTH_SECRET": "auto-generated" },
    "manual": { "GOOGLE_CLIENT_ID": "user-input" }
  },
  "vercel": {
    "project_id": "prj_xxx",
    "org_id": "team_xxx"
  }
}
```

### aws-iam-policy.json
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["cloudformation:*", "s3:*", "lambda:*"],
      "Resource": "arn:aws:*:ap-northeast-1:account-id:*"
    }
  ]
}
```

## ✅ 自動化チェックリスト

### 事前準備
- [ ] Google Cloud Console でOAuth設定完了
- [ ] AWS Console でIAMユーザー作成完了
- [ ] Vercel でAPIトークン作成完了
- [ ] 必要なツールのインストール確認
  - [ ] AWS CLI
  - [ ] GitHub CLI
  - [ ] Vercel CLI
  - [ ] jq
  - [ ] openssl

### 自動化実行
- [ ] `./scripts/setup-complete-automation.sh` 実行
- [ ] GitHub Secrets設定確認
- [ ] Vercel環境変数設定確認
- [ ] 初回デプロイ成功確認
- [ ] CI/CDパイプライン動作確認

### 事後確認
- [ ] 開発環境での動作確認
- [ ] Google OAuth ログイン確認
- [ ] ファイルアップロード・解除確認
- [ ] GitHub Actions自動デプロイ確認

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. GitHub CLI認証エラー
```bash
# 解決方法
gh auth login
gh auth status
```

#### 2. AWS認証エラー
```bash
# 解決方法
aws configure
aws sts get-caller-identity
```

#### 3. Vercel認証エラー
```bash
# 解決方法
vercel login
vercel whoami
```

#### 4. 権限不足エラー
```bash
# AWS IAMポリシーの確認
cat aws-iam-policy.json
# 生成されたポリシーをIAMユーザーにアタッチ
```

#### 5. 環境変数設定エラー
```bash
# Vercel環境変数確認
cd frontend
vercel env ls

# GitHub Secrets確認
gh secret list
```

## 📚 関連ドキュメント

- [deployment-guide.md](deployment-guide.md) - 詳細デプロイ手順
- [runbook/github-actions_secrets-and-iam-for-aws_and-vercel.md](runbook/github-actions_secrets-and-iam-for-aws_and-vercel.md) - GitHub Actions設定
- [runbook/google-oauth-setup.md](runbook/google-oauth-setup.md) - Google OAuth設定
- [runbook/vercel-project-setup_and-detach-github.md](runbook/vercel-project-setup_and-detach-github.md) - Vercel設定

## 🎯 次のステップ

自動化完了後の推奨フロー：

1. **ローカル開発確認**
   ```bash
   cd frontend && npm run dev
   ```

2. **ステージング環境デプロイ**
   ```bash
   ./scripts/deploy.sh staging all
   ```

3. **本番環境デプロイ**
   ```bash
   ./scripts/deploy.sh production all
   ```

4. **継続的デプロイ**
   - develop ブランチ → 開発環境自動デプロイ
   - main ブランチ → ステージング環境自動デプロイ
   - 手動実行 → 本番環境デプロイ

---

**🎉 これで手作業を最小限に抑えた本番運用環境の構築が完了します！**