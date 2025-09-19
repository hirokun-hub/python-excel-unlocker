# 手作業参照ガイド - Excel Unlocker 完全セットアップ

## 📋 概要

このドキュメントは、Excel Unlocker アプリケーションを**手作業で**セットアップする際の完全な参照ガイドです。自動化スクリプトを使わずに、各サービス（Google/AWS/Vercel）の最新UIで設定を行う場合に参照してください。

### 🎯 対象読者
- 初めてクラウドサービスを設定する方
- 自動化スクリプトを使わずに手作業で設定したい方
- 設定ミスを防ぎたい方
- トラブルシューティングが必要な方

### ⏱️ 所要時間
- **事前準備**: 15分
- **Google OAuth設定**: 10分
- **AWS設定**: 15分
- **Vercel設定**: 10分
- **GitHub Actions設定**: 10分
- **動作確認**: 10分
- **統合テスト実行**: 5分
- **合計**: 約75分

---

## 🚀 クイックスタート（5分で概要把握）

### 必要なアカウント
- [ ] Googleアカウント（Google Cloud Console用）
- [ ] AWSアカウント（Lambda/S3用）
- [ ] Vercelアカウント（フロントエンド用）
- [ ] GitHubアカウント（ソースコード管理用）

### 取得する認証情報
| サービス | 取得する値 | 用途 |
|---------|-----------|------|
| Google | `GOOGLE_CLIENT_ID`<br>`GOOGLE_CLIENT_SECRET` | OAuth認証 |
| AWS | `AWS_ACCESS_KEY_ID`<br>`AWS_SECRET_ACCESS_KEY` | バックエンドデプロイ |
| Vercel | `VERCEL_TOKEN`<br>`VERCEL_ORG_ID`<br>`VERCEL_PROJECT_ID` | フロントエンドデプロイ |
| 自動生成 | `NEXTAUTH_SECRET` | セッション暗号化 |

### 設定する場所
- **GitHub Secrets**: CI/CDパイプライン用の認証情報
- **Vercel環境変数**: フロントエンド実行時の設定値
- **AWS IAM**: 最小権限のデプロイ用ユーザー

---

## 📝 事前準備チェックリスト

### 必要なツールのインストール

#### macOS
```bash
# Homebrew経由でインストール
brew install awscli
brew install aws-sam-cli
npm install -g vercel
npm install -g @vercel/cli

# バージョン確認
aws --version          # AWS CLI v2.0+
sam --version          # SAM CLI v1.50+
vercel --version       # Vercel CLI latest
node --version         # Node.js v18+
```

#### Windows
```powershell
# Chocolatey経由でインストール
choco install awscli
choco install aws-sam-cli
npm install -g vercel

# または公式インストーラーを使用
# AWS CLI: https://aws.amazon.com/cli/
# SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
```

### 環境変数テンプレート準備

以下のテンプレートをコピーして、値を埋めながら進めてください：

```bash
# === Google OAuth ===
GOOGLE_CLIENT_ID="取得予定"
GOOGLE_CLIENT_SECRET="取得予定"

# === AWS ===
AWS_ACCESS_KEY_ID="取得予定"
AWS_SECRET_ACCESS_KEY="取得予定"
AWS_REGION="ap-northeast-1"

# === Vercel ===
VERCEL_TOKEN="取得予定"
VERCEL_ORG_ID="取得予定"
VERCEL_PROJECT_ID="取得予定"

# === NextAuth ===
NEXTAUTH_SECRET="取得予定"
NEXTAUTH_URL="https://your-domain.com"  # 本番URL
NEXT_PUBLIC_API_URL="https://your-api-gateway-url"  # API Gateway URL

# === アプリケーション設定 ===
ALLOWED_USERS="your-email@example.com,user2@example.com"
S3_BUCKET_NAME="excel-unlocker-bucket-production"
```

---

## 🔐 Google OAuth 設定（詳細手順）

### ステップ1: Google Cloud Console にアクセス

1. **ブラウザで以下にアクセス**
   ```
   https://console.cloud.google.com/
   ```

2. **プロジェクト選択**
   - 画面上部のプロジェクトセレクタをクリック
   - 既存プロジェクトを選択、または「新しいプロジェクト」を作成
   - プロジェクト名例: `excel-unlocker-production`

### ステップ2: OAuth 同意画面の設定

1. **APIとサービスに移動**
   - 左上ハンバーガーメニュー（≡）をクリック
   - 「APIとサービス」→「OAuth 同意画面」を選択

2. **ユーザーの種類を選択**
   - 「外部」を選択（社内限定の場合は「内部」も可）
   - 「作成」をクリック

3. **アプリ情報を入力**
   ```
   アプリ名: Secure Excel Unlock
   ユーザーサポートメール: your-email@example.com
   アプリのロゴ: （任意）
   アプリドメイン: your-domain.com
   承認済みドメイン: your-domain.com, vercel.app
   デベロッパーの連絡先情報: your-email@example.com
   ```

4. **スコープの設定**
   - 「スコープを追加または削除」をクリック
   - 以下のスコープを選択：
     - `../auth/userinfo.email`
     - `../auth/userinfo.profile`
     - `openid`
     - `../auth/drive.file`（Google Drive連携用）

5. **テストユーザーの追加**
   - 「テストユーザー」セクションで「ユーザーを追加」
   - 利用予定のGoogleアカウントを追加
   ```
   your-email@example.com
   user2@example.com
   ```

### ステップ3: OAuth クライアントIDの作成

1. **認証情報ページに移動**
   - 左メニュー「認証情報」をクリック
   - 上部「+ 認証情報を作成」→「OAuth クライアントID」

2. **アプリケーションの種類を選択**
   - 「ウェブアプリケーション」を選択

3. **名前を入力**
   ```
   名前: secure-excel-unlock-web-client
   ```

4. **承認済みのJavaScript生成元を追加**
   - 「URIを追加」をクリックして以下を追加：
   ```
   https://your-domain.com
   https://*.vercel.app
   http://localhost:3000
   ```

5. **承認済みのリダイレクトURIを追加**
   - 「URIを追加」をクリックして以下を追加：
   ```
   https://your-domain.com/api/auth/callback/google
   https://*.vercel.app/api/auth/callback/google
   http://localhost:3000/api/auth/callback/google
   ```

6. **作成して認証情報を取得**
   - 「作成」をクリック
   - 表示されるダイアログから以下をコピー：
   ```
   クライアントID: 1234567890-abcdefghijklmnop.apps.googleusercontent.com
   クライアントシークレット: GOCSPX-abcdefghijklmnopqrstuvwxyz
   ```

### ⚠️ よくある間違いと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `redirect_uri_mismatch` | リダイレクトURIが未登録 | 承認済みリダイレクトURIに正確なURLを追加 |
| `origin_mismatch` | JavaScript生成元が未登録 | 承認済みJavaScript生成元にオリジンを追加 |
| `access_denied` | テストユーザー未登録 | OAuth同意画面でテストユーザーを追加 |

---

## ☁️ AWS 設定（詳細手順）

### ステップ1: IAMユーザーの作成

1. **AWS Management Console にアクセス**
   ```
   https://console.aws.amazon.com/iam/
   ```

2. **ユーザー作成**
   - 左メニュー「ユーザー」をクリック
   - 「ユーザーを追加」をクリック
   - ユーザー名: `github-deploy-bot`
   - 「次のステップ: アクセス許可」をクリック

3. **アクセス許可の設定**
   - 「既存のポリシーを直接アタッチ」を選択
   - 「ポリシーの作成」をクリック（新しいタブで開く）

### ステップ2: 最小権限ポリシーの作成

1. **ポリシーエディタで以下のJSONを入力**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "cloudformation:CreateChangeSet",
           "cloudformation:CreateStack",
           "cloudformation:DeleteStack",
           "cloudformation:DescribeChangeSet",
           "cloudformation:DescribeStacks",
           "cloudformation:DescribeStackEvents",
           "cloudformation:DescribeStackResource",
           "cloudformation:DescribeStackResources",
           "cloudformation:ExecuteChangeSet",
           "cloudformation:GetTemplate",
           "cloudformation:UpdateStack",
           "cloudformation:ValidateTemplate"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "s3:CreateBucket",
           "s3:DeleteBucket",
           "s3:DeleteObject",
           "s3:GetBucketLocation",
           "s3:GetBucketPolicy",
           "s3:GetObject",
           "s3:ListBucket",
           "s3:PutBucketCORS",
           "s3:PutBucketPolicy",
           "s3:PutBucketPublicAccessBlock",
           "s3:PutObject"
         ],
         "Resource": [
           "arn:aws:s3:::excel-unlocker-*",
           "arn:aws:s3:::excel-unlocker-*/*"
         ]
       },
       {
         "Effect": "Allow",
         "Action": [
           "lambda:CreateFunction",
           "lambda:DeleteFunction",
           "lambda:GetFunction",
           "lambda:GetFunctionConfiguration",
           "lambda:ListTags",
           "lambda:TagResource",
           "lambda:UntagResource",
           "lambda:UpdateFunctionCode",
           "lambda:UpdateFunctionConfiguration"
         ],
         "Resource": "arn:aws:lambda:ap-northeast-1:*:function:excel-*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "apigateway:DELETE",
           "apigateway:GET",
           "apigateway:PATCH",
           "apigateway:POST",
           "apigateway:PUT"
         ],
         "Resource": "arn:aws:apigateway:ap-northeast-1::*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "iam:AttachRolePolicy",
           "iam:CreateRole",
           "iam:DeleteRole",
           "iam:DetachRolePolicy",
           "iam:GetRole",
           "iam:PassRole",
           "iam:TagRole"
         ],
         "Resource": "arn:aws:iam::*:role/excel-*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "logs:CreateLogGroup",
           "logs:DeleteLogGroup",
           "logs:DescribeLogGroups",
           "logs:PutRetentionPolicy"
         ],
         "Resource": "arn:aws:logs:ap-northeast-1:*:log-group:/aws/lambda/excel-*"
       }
     ]
   }
   ```

2. **ポリシーの保存**
   - 「次のステップ: タグ」→「次のステップ: 確認」
   - ポリシー名: `ExcelUnlockerDeployPolicy`
   - 説明: `Excel Unlocker deployment policy with minimal permissions`
   - 「ポリシーの作成」をクリック

### ステップ3: ユーザーにポリシーをアタッチ

1. **ユーザー作成画面に戻る**
   - 作成したポリシー `ExcelUnlockerDeployPolicy` を検索して選択
   - 「次のステップ: タグ」→「次のステップ: 確認」
   - 「ユーザーの作成」をクリック

2. **アクセスキーの取得**
   - 作成完了画面で以下をコピー：
   ```
   アクセスキーID: AKIAIOSFODNN7EXAMPLE
   シークレットアクセスキー: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```
   - ⚠️ **重要**: この画面を閉じると再表示できません

### ステップ4: S3バケットの作成

1. **S3コンソールにアクセス**
   ```
   https://console.aws.amazon.com/s3/
   ```

2. **バケット作成**
   - 「バケットを作成」をクリック
   - バケット名: `excel-unlocker-bucket-production-{account-id}-ap-northeast-1`
   - リージョン: `アジアパシフィック (東京) ap-northeast-1`
   - 「パブリックアクセスをすべてブロック」を有効のまま
   - 「バケットを作成」をクリック

### ⚠️ よくある間違いと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `AccessDenied` | IAM権限不足 | ポリシーの権限を確認・追加 |
| `BucketAlreadyExists` | バケット名重複 | アカウントIDを含む一意な名前に変更 |
| `InvalidUserID.NotFound` | ユーザーが見つからない | IAMユーザーの作成を確認 |

---

## 🚀 Vercel 設定（詳細手順）

### ステップ1: プロジェクトの作成・確認

1. **Vercel Dashboard にアクセス**
   ```
   https://vercel.com/dashboard
   ```

2. **プロジェクト作成（新規の場合）**
   - 「New Project」をクリック
   - 「Import Git Repository」でGitHubリポジトリを選択
   - プロジェクト名: `excel-unlocker`
   - Framework Preset: `Next.js`
   - Root Directory: `frontend`
   - 「Deploy」をクリック

### ステップ2: Git連携の解除

1. **プロジェクト設定**
   - プロジェクトダッシュボードで「Settings」をクリック
   - 左メニュー「Git」を選択

2. **連携解除**
   - 「Connected Git Repository」セクションで「Disconnect」をクリック
   - 確認ダイアログで「Disconnect」を選択
   - これでGitプッシュ時の自動デプロイが停止します

### ステップ3: API認証情報の取得

1. **Vercel Token の作成**
   ```
   https://vercel.com/account/tokens
   ```
   - 「Create Token」をクリック
   - Token Name: `github-actions-deploy`
   - Scope: `Full Account`
   - 「Create Token」をクリック
   - 表示されるトークンをコピー: `vc_1234567890abcdef...`

2. **組織IDとプロジェクトIDの取得**
   - プロジェクト「Settings」→「General」
   - 下部の「Project ID」をコピー: `prj_AbCdEfGhIj1234`
   - 「Team ID」または「User ID」をコピー: `team_XyZ789` または個人の場合は異なる形式

### ステップ4: 環境変数の設定

1. **環境変数ページ**
   - プロジェクト「Settings」→「Environment Variables」

2. **Production環境の設定**
   - 「Add New」をクリックして以下を追加：

   | Key | Value | Environment |
   |-----|-------|-------------|
   | `NEXT_PUBLIC_API_URL` | `https://your-api-gateway-url` | Production |
   | `NEXTAUTH_URL` | `https://your-domain.com` | Production |
   | `NEXTAUTH_SECRET` | `生成した長いランダム文字列` | Production |
   | `GOOGLE_CLIENT_ID` | `Google OAuth クライアントID` | Production |
   | `GOOGLE_CLIENT_SECRET` | `Google OAuth クライアントシークレット` | Production |

3. **Preview環境の設定**
   - 同じキーで「Preview」環境用の値を設定：

   | Key | Value | Environment |
   |-----|-------|-------------|
   | `NEXT_PUBLIC_API_URL` | `https://staging-api-gateway-url` | Preview |
   | `NEXTAUTH_URL` | `https://*.vercel.app` | Preview |
   | `NEXTAUTH_SECRET` | `同じランダム文字列` | Preview |
   | `GOOGLE_CLIENT_ID` | `同じクライアントID` | Preview |
   | `GOOGLE_CLIENT_SECRET` | `同じクライアントシークレット` | Preview |

### ステップ5: ドメイン設定（任意）

1. **カスタムドメイン追加**
   - 「Settings」→「Domains」
   - 「Add」をクリック
   - ドメイン名を入力: `app.example.com`
   - 「Add」をクリック

2. **DNS設定**
   - 表示されるCNAMEレコードをドメインプロバイダーに設定
   ```
   app.example.com CNAME cname.vercel-dns.com
   ```

### ⚠️ よくある間違いと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `Build failed` | 環境変数未設定 | 必要な環境変数がすべて設定されているか確認 |
| `Domain verification failed` | DNS設定エラー | CNAMEレコードが正しく設定されているか確認 |
| `Token invalid` | Vercelトークンエラー | 新しいトークンを生成して再設定 |

---

## 🔧 GitHub Actions 設定（詳細手順）

### ステップ1: Repository Secrets の設定

1. **GitHub リポジトリにアクセス**
   - リポジトリページで「Settings」をクリック
   - 左メニュー「Secrets and variables」→「Actions」

2. **Secrets の追加**
   - 「New repository secret」をクリックして以下を追加：

   | Name | Value | 説明 |
   |------|-------|------|
   | `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | AWS IAMアクセスキー |
   | `AWS_SECRET_ACCESS_KEY` | `wJalrXUtnFEMI/K7MDENG...` | AWS IAMシークレットキー |
   | `VERCEL_TOKEN` | `vc_1234567890abcdef...` | Vercel APIトークン |
   | `VERCEL_ORG_ID` | `team_XyZ789` | Vercel組織ID |
   | `VERCEL_PROJECT_ID` | `prj_AbCdEfGhIj1234` | VercelプロジェクトID |
   | `GOOGLE_CLIENT_ID` | `1234567890-abc...` | Google OAuth クライアントID |
   | `GOOGLE_CLIENT_SECRET` | `GOCSPX-abc...` | Google OAuth クライアントシークレット |
   | `NEXTAUTH_SECRET` | `生成したランダム文字列` | NextAuth暗号化キー |

### ステップ2: NEXTAUTH_SECRET の生成

1. **ランダム文字列生成**
   ```bash
   # macOS/Linux
   openssl rand -base64 32
   
   # または
   node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
   ```

2. **生成例**
   ```
   s3cure-secret-please-change-this-to-random-string-32-chars-long
   ```

### ステップ3: ワークフローファイルの確認

1. **ワークフローファイルの場所**
   ```
   .github/workflows/deploy-backend.yml
   .github/workflows/deploy-frontend.yml
   .github/workflows/deploy-full-stack.yml
   ```

2. **ワークフローの動作確認**
   - 「Actions」タブで過去の実行履歴を確認
   - エラーがある場合はログを確認して修正

### ⚠️ よくある間違いと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `Secret not found` | Secret名の typo | 正確なSecret名を確認 |
| `AWS credentials not found` | AWS認証エラー | AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY を確認 |
| `Vercel deployment failed` | Vercel認証エラー | VERCEL_TOKEN の有効性を確認 |

---

## ✅ 動作確認チェックリスト

### ローカル開発環境の確認

1. **フロントエンド起動**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   - http://localhost:3000 でアプリが表示されることを確認

2. **Google OAuth ログイン**
   - 「ログイン」ボタンをクリック
   - Google認証画面が表示されることを確認
   - ログイン後、ユーザー情報が表示されることを確認

3. **バックエンド接続**
   ```bash
   cd backend
   sam build
   sam local start-api --port 3001
   ```
   - API エンドポイントが起動することを確認

### デプロイメント確認

1. **GitHub Actions 実行**
   - 「Actions」タブで手動実行
   - すべてのステップが成功することを確認

2. **本番環境確認**
   - デプロイされたURLでアプリが動作することを確認
   - Google OAuth ログインが機能することを確認
   - ファイルアップロード・解除機能が動作することを確認

### 統合テスト実行

1. **統合テスト環境確認**
   ```bash
   # 全統合テスト実行
   ./tests/run-integration-tests.sh all cleanup
   ```

2. **個別テスト確認**
   ```bash
   # API統合テスト
   ./tests/run-integration-tests.sh api
   
   # S3連携テスト
   ./tests/run-integration-tests.sh s3
   
   # E2Eテスト
   ./tests/run-integration-tests.sh e2e
   
   # フロントエンド統合テスト
   ./tests/run-integration-tests.sh frontend
   ```

3. **テスト結果確認**
   - すべてのテストが成功することを確認
   - パフォーマンス基準を満たすことを確認
   - エラーハンドリングが正常に動作することを確認

### 設定確認チェックリスト

- [ ] Google OAuth 設定完了
  - [ ] OAuth同意画面設定
  - [ ] クライアントID作成
  - [ ] リダイレクトURI設定
  - [ ] JavaScript生成元設定
- [ ] AWS 設定完了
  - [ ] IAMユーザー作成
  - [ ] 最小権限ポリシー適用
  - [ ] アクセスキー取得
  - [ ] S3バケット作成
- [ ] Vercel 設定完了
  - [ ] プロジェクト作成
  - [ ] Git連携解除
  - [ ] 環境変数設定
  - [ ] ドメイン設定（任意）
- [ ] GitHub Actions 設定完了
  - [ ] Repository Secrets設定
  - [ ] ワークフロー動作確認
- [ ] 動作確認完了
  - [ ] ローカル開発環境
  - [ ] 本番環境デプロイ
  - [ ] 全機能動作確認
- [ ] 統合テスト実行完了
  - [ ] API統合テスト
  - [ ] S3連携テスト
  - [ ] E2Eテスト
  - [ ] フロントエンド統合テスト

---

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. Google OAuth エラー

**エラー**: `redirect_uri_mismatch`
```
原因: リダイレクトURIが Google Cloud Console に登録されていない
解決方法:
1. Google Cloud Console → APIとサービス → 認証情報
2. OAuth クライアントIDを編集
3. 承認済みのリダイレクトURIに以下を追加:
   - https://your-domain.com/api/auth/callback/google
   - https://*.vercel.app/api/auth/callback/google
```

**エラー**: `origin_mismatch`
```
原因: JavaScript生成元が登録されていない
解決方法:
1. OAuth クライアントIDを編集
2. 承認済みのJavaScript生成元に以下を追加:
   - https://your-domain.com
   - https://*.vercel.app
```

#### 2. AWS デプロイエラー

**エラー**: `AccessDenied`
```
原因: IAM権限不足
解決方法:
1. IAMユーザーのポリシーを確認
2. 必要な権限が含まれているか確認
3. 不足している場合は追加のポリシーをアタッチ
```

**エラー**: `BucketAlreadyExists`
```
原因: S3バケット名が既に使用されている
解決方法:
1. template.yaml のバケット名を変更
2. アカウントIDやタイムスタンプを含む一意な名前に変更
```

#### 3. Vercel デプロイエラー

**エラー**: `Build failed`
```
原因: 環境変数が設定されていない
解決方法:
1. Vercel プロジェクト → Settings → Environment Variables
2. 必要な環境変数がすべて設定されているか確認
3. Production と Preview 両方に設定されているか確認
```

**エラー**: `Domain verification failed`
```
原因: DNS設定が正しくない
解決方法:
1. ドメインプロバイダーでCNAMEレコードを確認
2. 設定が反映されるまで最大48時間待機
3. DNS伝播チェックツールで確認
```

#### 4. GitHub Actions エラー

**エラー**: `Secret not found`
```
原因: Repository Secret の名前が間違っている
解決方法:
1. GitHub リポジトリ → Settings → Secrets and variables → Actions
2. Secret名を正確に確認
3. 大文字小文字、アンダースコアの有無を確認
```

### 診断フロー

#### 問題発生時の確認手順

1. **エラーメッセージの確認**
   - 正確なエラーメッセージをコピー
   - エラーが発生した場所（ローカル/GitHub Actions/本番環境）を特定

2. **設定値の確認**
   - 環境変数が正しく設定されているか確認
   - 認証情報が有効期限内か確認
   - URLやドメイン名に typo がないか確認

3. **ログの確認**
   - GitHub Actions のログを確認
   - Vercel のデプロイログを確認
   - AWS CloudWatch ログを確認

4. **段階的な切り分け**
   - ローカル環境で動作するか確認
   - 各サービス単体で動作するか確認
   - 統合時の問題か特定

### サポートリソース

#### 公式ドキュメント
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [AWS IAM ベストプラクティス](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Vercel デプロイメント](https://vercel.com/docs/concepts/deployments/overview)
- [GitHub Actions](https://docs.github.com/en/actions)

#### コミュニティサポート
- [Stack Overflow](https://stackoverflow.com/)
- [GitHub Discussions](https://github.com/discussions)
- [Discord コミュニティ](https://discord.com/)

---

## 📚 設定値テンプレート集

### GitHub Secrets テンプレート

```bash
# AWS関連
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=ap-northeast-1

# Vercel関連
VERCEL_TOKEN=vc_1234567890abcdef_example_only
VERCEL_ORG_ID=team_7g8h9i0j_example
VERCEL_PROJECT_ID=prj_KLMNoP123_example

# Google OAuth関連
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz

# NextAuth関連
NEXTAUTH_SECRET=s3cure-secret-please-change-this-to-random-string-32-chars-long
```

### Vercel 環境変数テンプレート

#### Production環境
```bash
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/prod
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=s3cure-secret-please-change-this-to-random-string-32-chars-long
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

#### Preview環境
```bash
NEXT_PUBLIC_API_URL=https://staging-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/staging
NEXTAUTH_URL=https://your-project-git-branch-username.vercel.app
NEXTAUTH_SECRET=s3cure-secret-please-change-this-to-random-string-32-chars-long
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

### AWS IAM ポリシーテンプレート

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:CreateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeChangeSet",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:GetTemplate",
        "cloudformation:UpdateStack",
        "cloudformation:ValidateTemplate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:DeleteObject",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutBucketCORS",
        "s3:PutBucketPolicy",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::excel-unlocker-*",
        "arn:aws:s3:::excel-unlocker-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListTags",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:*:function:excel-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:DELETE",
        "apigateway:GET",
        "apigateway:PATCH",
        "apigateway:POST",
        "apigateway:PUT"
      ],
      "Resource": "arn:aws:apigateway:ap-northeast-1::*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:AttachRolePolicy",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:DetachRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "iam:TagRole"
      ],
      "Resource": "arn:aws:iam::*:role/excel-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "arn:aws:logs:ap-northeast-1:*:log-group:/aws/lambda/excel-*"
    }
  ]
}
```

---

## 🎯 次のステップ

### セットアップ完了後の推奨フロー

1. **ローカル開発環境の確認**
   ```bash
   cd frontend && npm run dev
   cd backend && sam local start-api
   ```

2. **ステージング環境へのデプロイ**
   ```bash
   # GitHub Actions で手動実行
   # Environment: staging を選択
   ```

3. **本番環境へのデプロイ**
   ```bash
   # GitHub Actions で手動実行
   # Environment: production を選択
   # 承認プロセスを経てデプロイ
   ```

4. **継続的デプロイの設定**
   - develop ブランチ → 開発環境自動デプロイ
   - main ブランチ → ステージング環境自動デプロイ
   - 手動実行 → 本番環境デプロイ

### 運用・保守

1. **定期メンテナンス**
   - 月次: CloudWatch メトリクス確認
   - 四半期: 依存関係の更新
   - 半年: セキュリティ監査

2. **モニタリング**
   - CloudWatch Dashboard での監視
   - アラート設定の確認
   - ログの定期確認

3. **バックアップ・復旧**
   - 設定値のバックアップ
   - 復旧手順の確認
   - 災害復旧計画の策定

---

**🎉 これで Excel Unlocker の完全な手作業セットアップが完了しました！**

何か問題が発生した場合は、このドキュメントのトラブルシューティングセクションを参照するか、各サービスの公式ドキュメントを確認してください。