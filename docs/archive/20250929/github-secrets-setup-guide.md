# GitHub Secrets 環境変数設定ガイド

## 概要

このガイドでは、Excel解除ツールに必要な環境変数をGitHub Secretsに安全に設定する方法を説明します。
このガイドでは、本プロジェクトのCI/CDパイプライン（GitHub Actions）に必要な環境変数をGitHub Secretsに安全に設定する方法を説明します。
**AWS認証には、安全なOIDC認証を強く推奨します。**

## 🎯 このガイドの目的

- **環境変数設定の簡素化**: 複雑な設定を廃止し、必要最小限の7つの環境変数のみに特化
- **設定の明確化**: 必要なシークレットを網羅し、推奨設定を明記
- **初心者サポート**: 技術的な知識がなくても安全に設定できる
- **機密情報保護**: GitHubにのみ保存し、ローカルには残さない徹底した保護
- **自動化**: GitHub Actionsでの自動デプロイメントを実現

## 📋 必要な環境変数一覧

| 環境変数名 | 説明 | 取得場所 |
|-----------|------|----------|
|-----------|------|:----------|
| `GOOGLE_CLIENT_ID` | Google OAuth認証用クライアントID | Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google OAuth認証用クライアントシークレット | Google Cloud Console |
| `VERCEL_TOKEN` | Vercelデプロイ用個人アクセストークン | Vercel Dashboard |
| `VERCEL_ORG_ID` | Vercelチーム/組織ID | .vercel/project.json |
| `VERCEL_PROJECT_ID` | Vercelプロジェクト固有ID | .vercel/project.json |
| `AWS_ACCESS_KEY_ID` | AWSリソースアクセス用アクセスキーID | AWS Console |
| `AWS_SECRET_ACCESS_KEY` | AWSリソースアクセス用シークレットアクセスキー | AWS Console |
| `AWS_GITHUB_ACTIONS_ROLE_ARN` | **[推奨]** AWS OIDC認証用のIAMロールARN | AWS Console (IAM) |
| `AWS_ACCESS_KEY_ID` | **[非推奨]** AWSアクセスキーID (OIDCが使えない場合) | AWS Console (IAM) |
| `AWS_SECRET_ACCESS_KEY` | **[非推奨]** AWSシークレットアクセスキー (OIDCが使えない場合) | AWS Console (IAM) |

## 🚀 クイックスタート

### 方法1: 自動スクリプト（推奨）

```bash
# 1. Python環境のセットアップ
./scripts/setup-python-env.sh

# 2. GitHub Secrets設定スクリプトの実行
./scripts/setup-github-secrets.sh
```

### 方法2: 手動設定

各環境変数を個別に設定する場合は、以下の詳細手順を参照してください。

## 📝 詳細な設定手順

### 1. Google OAuth設定

#### Google Cloud Consoleでの設定

1. **Google Cloud Console** (https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択または新規作成
3. **「認証情報」** → **「認証情報を作成」** → **「OAuth 2.0 クライアント ID」**
4. アプリケーションの種類: **「ウェブアプリケーション」**
5. 承認済みのリダイレクト URI:
   - 開発環境: `http://localhost:3000/api/auth/callback/google`
   - 本番環境: `https://your-app.vercel.app/api/auth/callback/google`

#### 取得する値

- **Client ID**: `123456789-abcdefg.apps.googleusercontent.com` 形式
- **Client Secret**: `GOCSPX-abcdefghijklmnopqrstuvwxyz` 形式

### 2. Vercel設定

#### Vercel Personal Access Tokenの取得

1. **Vercel Dashboard** (https://vercel.com/dashboard) にアクセス
2. **Settings** → **Tokens**
3. **「Create Token」** をクリック
4. トークン名を入力（例: `excel-unlocker-deploy`）
5. 適切なスコープを選択
6. **「Create」** をクリック

#### Vercel Organization ID と Project ID の取得

```bash
# プロジェクトルートで実行
vercel link

# .vercel/project.json ファイルを確認
cat .vercel/project.json
```

出力例:
```json
{
  "projectId": "prj_1234567890abcdef",
  "orgId": "team_1234567890abcdef"
}
```

### 3. AWS設定

#### AWS Access Keyの作成
#### 方法1: OIDC認証の設定 (推奨)

セキュリティと管理の観点から、永続的なアクセスキーの代わりにOIDC認証を使用することを強く推奨します。設定方法は以下のガイドを参照してください。

- **GitHub OIDC移行ガイド**

#### 方法2: アクセスキーの作成 (フォールバック)

1. **AWS Console** → **IAM** → **Users**
2. ユーザーを選択 → **Security credentials**
3. **「Create access key」** をクリック
4. 用途: **「Command Line Interface (CLI)」**
5. Access Key ID と Secret Access Key をコピー

#### 必要な権限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "iam:*",
        "cloudformation:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🔧 GitHub Secretsへの登録

### GitHub CLI を使用した登録

```bash
# GitHub CLIでログイン
gh auth login

# 各環境変数を設定
gh secret set GOOGLE_CLIENT_ID
gh secret set GOOGLE_CLIENT_SECRET
gh secret set AWS_GITHUB_ACTIONS_ROLE_ARN # 推奨
gh secret set VERCEL_TOKEN
gh secret set VERCEL_ORG_ID
gh secret set VERCEL_PROJECT_ID
gh secret set AWS_ACCESS_KEY_ID
gh secret set AWS_SECRET_ACCESS_KEY
# 非推奨: gh secret set AWS_ACCESS_KEY_ID
# 非推奨: gh secret set AWS_SECRET_ACCESS_KEY

# 登録確認
gh secret list
```

### GitHub Web UIでの登録

1. GitHubリポジトリページにアクセス
2. **Settings** → **Secrets and variables** → **Actions**
3. **「New repository secret」** をクリック
4. Name と Value を入力
5. **「Add secret」** をクリック

## ✅ 検証とテスト

### 環境変数の検証

```bash
# 検証スクリプトの実行
python3 scripts/validate-env-vars.py --interactive

# または対話式検証
python3 scripts/validate-env-vars.py -i
```

### GitHub Actionsでの動作確認

1. リポジトリに変更をプッシュ
2. **Actions** タブで実行状況を確認
3. デプロイメントが成功することを確認

## 🛡️ セキュリティのベストプラクティス

### 機密情報の保護

- ✅ **GitHub Secretsのみに保存**: ローカルファイルには保存しない
- ✅ **最小権限の原則**: 必要最小限の権限のみ付与
- ✅ **定期的な更新**: アクセスキーを定期的にローテーション
- ✅ **監査ログ**: アクセス履歴を定期的に確認

### .gitignore設定

以下のパターンが.gitignoreに含まれていることを確認:

```gitignore
# 環境変数ファイル
.env*
**/.env*
!.env.example

# 設定ファイル
setup-config.json
setup-config.*.json
config-backup/
.config-encryption-key

# OAuth認証情報
client_secret_*.json
*_credentials.json
service-account*.json
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. GitHub CLI認証エラー

```bash
# 再認証
gh auth logout
gh auth login
```

#### 2. Python環境エラー（macOS）

```bash
# 仮想環境の再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

#### 3. 環境変数形式エラー

| 環境変数 | 正しい形式 | よくある間違い |
|---------|-----------|---------------|
| `GOOGLE_CLIENT_ID` | `*.apps.googleusercontent.com` | ドメインなし |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-*` | プレフィックスなし |
| `VERCEL_ORG_ID` | `team_*` | `user_*` を使用 |
| `AWS_ACCESS_KEY_ID` | `AKIA*` | 他のプレフィックス |
| `AWS_GITHUB_ACTIONS_ROLE_ARN` | `arn:aws:iam::...` | ARN形式でない |

#### 4. GitHub Actions失敗

1. **Secrets確認**: 全ての必要な環境変数が設定されているか
2. **権限確認**: AWSアクセスキーに適切な権限があるか
3. **ログ確認**: Actions タブでエラーログを確認

## 📞 サポート

### 困ったときの連絡先

- **技術サポート**: 管理者にお問い合わせください
- **ドキュメント**: このガイドを参照
- **GitHub Issues**: バグ報告や機能要求

### 参考リンク

- [Google Cloud Console](https://console.cloud.google.com/)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [AWS Console](https://console.aws.amazon.com/)
- [GitHub CLI](https://cli.github.com/)

## 📊 設定完了チェックリスト

- [ ] Google OAuth設定完了
- [ ] Vercel設定完了
- [ ] AWS設定完了
- [ ] GitHub Secrets登録完了
- [ ] 環境変数検証完了
- [ ] GitHub Actions動作確認完了
- [ ] セキュリティ設定確認完了

## 🎉 次のステップ

環境変数の設定が完了したら:

1. **GitHub Actionsの実行**: 自動デプロイメントが開始されます
2. **動作確認**: デプロイされたアプリケーションをテスト
3. **ユーザー招待**: 必要に応じて他のユーザーを招待
4. **運用開始**: 本格的な運用を開始

---

**注意**: このガイドの内容は定期的に更新されます。最新版を確認してください。