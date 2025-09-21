# 🔰 初心者向け完全セットアップガイド - Excel Unlocker

## 📋 このガイドについて

**Excel Unlocker** を初めて使う方のための、完全初心者向けセットアップガイドです。技術的な前提知識は一切不要で、画面の指示に従って進めるだけで環境構築が完了します。

### 🎯 対象者
- **初めてクラウドサービスを使う方**
- **技術的な知識がない方**
- **確実に設定を完了させたい方**
- **社内でExcel Unlockerを導入したい方**

### ⏱️ 所要時間の目安
| ステップ | 作業内容 | 所要時間 | 難易度 |
|---------|---------|---------|--------|
| **事前準備** | アカウント作成・確認 | 20分 | ⭐ |
| **Google設定** | OAuth認証設定 | 15分 | ⭐⭐ |
| **AWS設定** | クラウド環境設定 | 20分 | ⭐⭐⭐ |
| **Vercel設定** | Webサイト公開設定 | 10分 | ⭐⭐ |
| **GitHub設定** | 自動化設定 | 15分 | ⭐⭐ |
| **動作確認** | 全体テスト | 10分 | ⭐ |
| **合計** | | **約90分** | |

### 🎁 完了後に得られるもの
- ✅ 社内限定のExcel解除Webアプリ
- ✅ 複数ファイルの一括処理機能
- ✅ Google Driveへの自動保存機能
- ✅ 全デバイス（iPhone/Android/PC）対応
- ✅ セキュアな認証システム

---

## 🚀 ステップ0: 事前準備（20分）

### 必要なアカウントの確認・作成

以下のアカウントが必要です。まだお持ちでない場合は、先に作成してください。

#### 1. Googleアカウント（必須）
- **用途**: ユーザー認証・Google Drive連携
- **作成方法**: [accounts.google.com](https://accounts.google.com) で「アカウントを作成」
- **注意点**: 会社のGoogleアカウントを使用することを推奨

#### 2. AWSアカウント（必須）
- **用途**: Excel解除処理・ファイル保存
- **作成方法**: [aws.amazon.com](https://aws.amazon.com) で「無料アカウントを作成」
- **注意点**: クレジットカード登録が必要（無料利用枠内なら課金されません）
- **費用目安**: 月額100円程度（軽い利用の場合）

#### 3. Vercelアカウント（必須）
- **用途**: Webサイトの公開
- **作成方法**: [vercel.com](https://vercel.com) で「Sign Up」
- **注意点**: GitHubアカウントでの登録を推奨

#### 4. GitHubアカウント（必須）
- **用途**: ソースコード管理・自動デプロイ
- **作成方法**: [github.com](https://github.com) で「Sign up」
- **注意点**: 無料プランで十分です

### アカウント作成チェックリスト

- [ ] Googleアカウント作成完了（ログイン確認済み）
- [ ] AWSアカウント作成完了（ログイン確認済み）
- [ ] Vercelアカウント作成完了（ログイン確認済み）
- [ ] GitHubアカウント作成完了（ログイン確認済み）

### 📝 メモ帳の準備

設定中に取得する情報を記録するため、以下のテンプレートをコピーしてメモ帳に貼り付けてください：

💡 **使い方**: 各項目の「（後で記入）」部分に、設定手順で取得した値を記入してください。

```
=== Excel Unlocker 設定情報 ===

【Google OAuth設定】
クライアントID: （後で記入）
クライアントシークレット: （後で記入）

【AWS設定】
アクセスキーID: （後で記入）
シークレットアクセスキー: （後で記入）
S3バケット名: （後で記入）

【Vercel設定】
トークン: （後で記入）
組織ID (VERCEL_ORG_ID): （後で記入） ※個人:ランダム文字列、チーム:team_xxx形式
プロジェクトID (VERCEL_PROJECT_ID): （後で記入） ※prj_xxx形式

【GitHub Secrets用】
- AWS_ACCESS_KEY_ID: 上記のアクセスキーID
- AWS_SECRET_ACCESS_KEY: 上記のシークレットアクセスキー
- VERCEL_TOKEN: 上記のトークン
- VERCEL_ORG_ID: 上記の組織ID
- VERCEL_PROJECT_ID: 上記のプロジェクトID
- GOOGLE_CLIENT_ID: 上記のクライアントID
- GOOGLE_CLIENT_SECRET: 上記のクライアントシークレット
- NEXTAUTH_SECRET: （後で生成）

【その他】
本番URL: （後で記入）
```

---

## 🔐 ステップ1: Google設定（15分）

### 1-1. Google Cloud Consoleにアクセス

1. **ブラウザで以下のURLを開く**
   ```
   https://console.cloud.google.com/
   ```

2. **Googleアカウントでログイン**
   - 作成したGoogleアカウントでログインしてください

3. **利用規約に同意**
   - 初回アクセス時は利用規約への同意が求められます

### 1-2. プロジェクトの作成

1. **画面上部のプロジェクト選択をクリック**
   - 「プロジェクトを選択」と書かれた部分をクリック

2. **「新しいプロジェクト」をクリック**

3. **プロジェクト情報を入力**
   ```
   プロジェクト名: excel-unlocker-production
   組織: （空欄のまま）
   場所: （空欄のまま）
   ```

4. **「作成」をクリック**
   - 作成完了まで1-2分待ちます

### 1-3. OAuth同意画面の設定

1. **左上のメニュー（≡）をクリック**

2. **「APIとサービス」→「OAuth同意画面」を選択**

3. **ユーザーの種類を選択**
   - 「外部」を選択（社内限定でも「外部」を選択してください）
   - 「作成」をクリック

4. **アプリ情報を入力**
   ```
   アプリ名: Secure Excel Unlock
   ユーザーサポートメール: （あなたのメールアドレス）
   アプリのロゴ: （空欄のまま）
   アプリドメイン: （空欄のまま）
   承認済みドメイン: vercel.app
   デベロッパーの連絡先情報: （あなたのメールアドレス）
   ```

5. **「保存して次へ」をクリック**

6. **スコープの設定**
   - 「スコープを追加または削除」をクリック
   - 以下にチェックを入れる：
     - `../auth/userinfo.email`
     - `../auth/userinfo.profile`
     - `openid`
     - `../auth/drive.file`
   - 「更新」をクリック
   - 「保存して次へ」をクリック

7. **テストユーザーの追加**
   - 「ユーザーを追加」をクリック
   - 利用予定のGoogleアカウントを入力
   - 「追加」をクリック
   - 「保存して次へ」をクリック

### 1-4. OAuth認証情報の作成

1. **左メニュー「認証情報」をクリック**

2. **「+ 認証情報を作成」→「OAuth クライアントID」をクリック**

3. **アプリケーションの種類を選択**
   - 「ウェブアプリケーション」を選択

4. **名前を入力**
   ```
   名前: secure-excel-unlock-web-client
   ```

5. **承認済みのJavaScript生成元を追加**
   - 「URIを追加」をクリック
   - 以下を1つずつ追加：
   ```
   https://localhost:3000
   https://excel-unlocker.vercel.app
   ```
   - ※ 実際のドメインが決まったら後で追加します

6. **承認済みのリダイレクトURIを追加**
   - 「URIを追加」をクリック
   - 以下を1つずつ追加：
   ```
   http://localhost:3000/api/auth/callback/google
   https://excel-unlocker.vercel.app/api/auth/callback/google
   ```

7. **「作成」をクリック**

8. **認証情報をメモ帳にコピー**
   - 表示されるダイアログから以下をコピーしてメモ帳に保存：
   ```
   クライアントID: 1234567890-abcdefghijklmnop.apps.googleusercontent.com
   クライアントシークレット: GOCSPX-abcdefghijklmnopqrstuvwxyz
   ```

### ✅ Google設定完了チェック

- [ ] Google Cloud Consoleにログインできた
- [ ] プロジェクトを作成できた
- [ ] OAuth同意画面を設定できた
- [ ] OAuth認証情報を作成できた
- [ ] クライアントIDとシークレットをメモ帳に保存した

---

## ☁️ ステップ2: AWS設定（20分）

### 2-1. AWS Management Consoleにアクセス

1. **ブラウザで以下のURLを開く**
   ```
   https://console.aws.amazon.com/
   ```

2. **AWSアカウントでログイン**
   - 「ルートユーザー」を選択
   - 作成したAWSアカウントでログイン

3. **リージョンを東京に変更**
   - 画面右上のリージョン表示をクリック
   - 「アジアパシフィック（東京）ap-northeast-1」を選択

### 2-2. IAMユーザーの作成

1. **検索バーに「IAM」と入力してEnter**

2. **左メニュー「ユーザー」をクリック**

3. **「ユーザーを追加」をクリック**

4. **ユーザー詳細を入力**
   ```
   ユーザー名: excel-unlocker-deploy-user
   AWSマネジメントコンソールへのアクセス: チェックしない
   ```
   
   💡 **推奨**: プロジェクト専用のユーザー名を使用することで、セキュリティと管理性が向上します。

5. **「次へ」をクリック**

6. **「ポリシーを直接アタッチする」を選択**

7. **「ポリシーの作成」をクリック（新しいタブで開く）**

### 2-3. 最小権限ポリシーの作成（セキュリティ強化版）

1. **新しいタブで「JSON」タブをクリック**

2. **以下の修正版JSONをコピーして貼り付け**
   
   ⚠️ **重要**: 以下のポリシーはセキュリティ警告を解決した修正版です。
   
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "ExcelUnlockerS3Access",
               "Effect": "Allow",
               "Action": [
                   "s3:CreateBucket",
                   "s3:DeleteBucket",
                   "s3:GetBucketLocation",
                   "s3:ListBucket",
                   "s3:GetObject",
                   "s3:PutObject",
                   "s3:DeleteObject",
                   "s3:PutBucketCORS",
                   "s3:PutBucketPublicAccessBlock",
                   "s3:GetBucketCORS",
                   "s3:GetBucketPublicAccessBlock"
               ],
               "Resource": [
                   "arn:aws:s3:::excel-unlock-*",
                   "arn:aws:s3:::excel-unlock-*/*"
               ]
           },
           {
               "Sid": "ExcelUnlockerLambdaAccess",
               "Effect": "Allow",
               "Action": [
                   "lambda:CreateFunction",
                   "lambda:UpdateFunctionCode",
                   "lambda:UpdateFunctionConfiguration",
                   "lambda:DeleteFunction",
                   "lambda:GetFunction",
                   "lambda:ListFunctions",
                   "lambda:InvokeFunction",
                   "lambda:AddPermission",
                   "lambda:RemovePermission",
                   "lambda:TagResource",
                   "lambda:UntagResource"
               ],
               "Resource": "arn:aws:lambda:*:*:function:excel-unlocker-*"
           },
           {
               "Sid": "ExcelUnlockerAPIGatewayAccess",
               "Effect": "Allow",
               "Action": [
                   "apigateway:GET",
                   "apigateway:POST",
                   "apigateway:PUT",
                   "apigateway:DELETE",
                   "apigateway:PATCH"
               ],
               "Resource": [
                   "arn:aws:apigateway:*::/restapis",
                   "arn:aws:apigateway:*::/restapis/*"
               ]
           },
           {
               "Sid": "ExcelUnlockerCloudFormationAccess",
               "Effect": "Allow",
               "Action": [
                   "cloudformation:CreateStack",
                   "cloudformation:UpdateStack",
                   "cloudformation:DeleteStack",
                   "cloudformation:DescribeStacks",
                   "cloudformation:DescribeStackEvents",
                   "cloudformation:DescribeStackResources",
                   "cloudformation:DescribeStackResource",
                   "cloudformation:GetTemplate",
                   "cloudformation:ValidateTemplate",
                   "cloudformation:ListStackResources"
               ],
               "Resource": "arn:aws:cloudformation:*:*:stack/excel-unlocker-*/*"
           },
           {
               "Sid": "ExcelUnlockerIAMRoleAccess",
               "Effect": "Allow",
               "Action": [
                   "iam:CreateRole",
                   "iam:DeleteRole",
                   "iam:GetRole",
                   "iam:UpdateRole",
                   "iam:AttachRolePolicy",
                   "iam:DetachRolePolicy",
                   "iam:PutRolePolicy",
                   "iam:DeleteRolePolicy",
                   "iam:GetRolePolicy",
                   "iam:ListRolePolicies",
                   "iam:ListAttachedRolePolicies",
                   "iam:TagRole",
                   "iam:UntagRole"
               ],
               "Resource": "arn:aws:iam::*:role/excel-unlocker-*"
           },
           {
               "Sid": "ExcelUnlockerIAMPassRole",
               "Effect": "Allow",
               "Action": "iam:PassRole",
               "Resource": "arn:aws:iam::*:role/excel-unlocker-*",
               "Condition": {
                   "StringEquals": {
                       "iam:PassedToService": [
                           "lambda.amazonaws.com",
                           "apigateway.amazonaws.com"
                       ]
                   }
               }
           },
           {
               "Sid": "ExcelUnlockerLogsAccess",
               "Effect": "Allow",
               "Action": [
                   "logs:CreateLogGroup",
                   "logs:CreateLogStream",
                   "logs:PutLogEvents",
                   "logs:DescribeLogGroups",
                   "logs:DescribeLogStreams"
               ],
               "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/excel-unlocker-*"
           }
       ]
   }
   ```

   💡 **セキュリティ改善点**:
   - PassRole権限を特定のAWSサービス（Lambda、API Gateway）のみに制限
   - ワイルドカード（*）の使用を最小限に抑制
   - リソース名にプレフィックス（excel-unlock-*）を付けて制限

3. **「次へ」をクリック**

3. **セキュリティ警告について**
   
   ポリシー貼り付け時に以下の警告が表示される場合がありますが、上記のポリシーは既に対策済みです：
   - "Create SLR With Star In Action And Resource"
   - "PassRole With Star In Action And Resource"
   
   これらの警告は修正版ポリシーで解決されているため、安全に使用できます。

4. **「次へ」をクリック**

5. **ポリシー詳細を入力**
   ```
   ポリシー名: ExcelUnlockerDeployPolicy
   説明: Excel Unlocker deployment policy
   ```

5. **「ポリシーの作成」をクリック**

### 2-4. ユーザーにポリシーをアタッチ

1. **元のタブに戻る**

2. **検索バーに「ExcelUnlockerDeployPolicy」と入力**

3. **作成したポリシーにチェックを入れる**

4. **「次へ」をクリック**

5. **「ユーザーの作成」をクリック**

### 2-5. アクセスキーの作成

1. **作成したユーザー「github-deploy-bot」をクリック**

2. **「セキュリティ認証情報」タブをクリック**

3. **「アクセスキーを作成」をクリック**

4. **「その他」を選択**

5. **「次へ」をクリック**

6. **説明を入力**
   ```
   説明タグ: GitHub Actions deployment key
   ```

7. **「アクセスキーを作成」をクリック**

8. **認証情報をメモ帳にコピー**
   ```
   アクセスキーID: AKIAIOSFODNN7EXAMPLE
   シークレットアクセスキー: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```
   - ⚠️ **重要**: この画面を閉じると再表示できません

### 2-6. S3バケットの作成

1. **検索バーに「S3」と入力してEnter**

2. **「バケットを作成」をクリック**

3. **バケット設定を入力**
   ```
   バケット名: excel-unlocker-bucket-production-20250119
   リージョン: アジアパシフィック (東京) ap-northeast-1
   ```
   - ※ 日付部分は今日の日付に変更してください

4. **「パブリックアクセスをすべてブロック」はチェックしたまま**

5. **「バケットを作成」をクリック**

6. **バケット名をメモ帳に保存**

### ✅ AWS設定完了チェック

- [ ] AWS Management Consoleにログインできた
- [ ] リージョンを東京に設定した
- [ ] IAMユーザーを作成できた
- [ ] 最小権限ポリシーを作成できた
- [ ] アクセスキーを作成できた
- [ ] アクセスキー情報をメモ帳に保存した
- [ ] S3バケットを作成できた
- [ ] バケット名をメモ帳に保存した

---

## 🚀 ステップ3: Vercel設定（10分）

### 3-1. Vercel Dashboardにアクセス

1. **ブラウザで以下のURLを開く**
   ```
   https://vercel.com/dashboard
   ```

2. **GitHubアカウントでログイン**
   - 「Continue with GitHub」をクリック

### 3-2. プロジェクトの作成

1. **「New Project」をクリック**

2. **「Import Git Repository」で以下を入力**
   ```
   Git Repository URL: https://github.com/your-username/excel-unlocker
   ```
   - ※ 実際のGitHubリポジトリURLに変更してください

3. **プロジェクト設定**
   ```
   Project Name: excel-unlocker
   Framework Preset: Next.js
   Root Directory: frontend
   ```

4. **「Deploy」をクリック**
   - 初回デプロイが開始されます（5-10分程度）

### 3-3. Git連携の解除

1. **デプロイ完了後、「Settings」をクリック**

2. **左メニュー「Git」を選択**

3. **「Disconnect」をクリック**

4. **確認ダイアログで「Disconnect」をクリック**

### 3-4. API認証情報の取得

1. **新しいタブで以下のURLを開く**
   ```
   https://vercel.com/account/tokens
   ```

2. **「Create Token」をクリック**

3. **トークン設定**
   ```
   Token Name: excel-unlocker-deploy-token
   Scope: Full Account
   Expiration: No expiration (または適切な期限を設定)
   ```
   
   💡 **セキュリティ推奨**: プロジェクト専用のトークン名を使用することで、用途が明確になり管理しやすくなります。

4. **「Create Token」をクリック**

5. **トークンをメモ帳にコピー**
   ```
   トークン: vc_1234567890abcdef...
   ```

### 3-5. 組織IDとプロジェクトIDの取得

⚠️ **重要**: 現在、組織ID（ORG_ID）はWebダッシュボードから取得できません。**Vercel CLIを使用する必要があります**。

#### **Step 1: Vercel CLIのインストール**

1. **ターミナル/コマンドプロンプトを開く**
   - **Windows**: スタートメニュー → 「cmd」または「PowerShell」
   - **Mac**: アプリケーション → ユーティリティ → ターミナル

2. **Vercel CLIをインストール**
   ```bash
   npm install -g vercel
   ```
   
   💡 **注意**: Node.jsがインストールされている必要があります。

#### **Step 2: Vercel CLIでログイン**

1. **Vercelにログイン**
   ```bash
   vercel login
   ```

2. **ブラウザが開くので、Vercelアカウントでログイン**

3. **ログイン成功の確認**
   ```bash
   vercel whoami
   ```

#### **Step 3: 組織IDとプロジェクトIDの取得**

**方法1: プロジェクトリンク経由（推奨・最も確実）**

1. **frontendディレクトリに移動**
   ```bash
   cd path/to/excel-unlocker/frontend
   ```
   
   💡 **注意**: GitHubからクローンしたプロジェクトのfrontendフォルダに移動してください。

2. **プロジェクトをVercelにリンク**
   ```bash
   vercel link
   ```
   
   **対話式の質問に答える**:
   ```
   ? Set up "~/path/to/frontend"? [Y/n] y
   ? Which scope should contain your project? [Use arrows to move, type to filter]
   > Your Personal Account (個人アカウントの場合)
   > Your Team Name (チームアカウントの場合)
   
   ? Link to existing project? [y/N] y
   ? What's the name of your existing project? excel-unlocker
   ```

3. **プロジェクト情報を確認**
   ```bash
   vercel project ls
   ```
   
   **出力例**:
   ```
   Project: excel-unlocker
   ID: prj_AbCdEfGhIj1234
   Team: Your Team Name (team_abc123def456) または Personal Account (QmVyY2VsVGVhbQ)
   ```

4. **取得した情報をメモ帳にコピー**
   ```
   組織ID (VERCEL_ORG_ID): team_abc123def456 (または QmVyY2VsVGVhbQ)
   プロジェクトID (VERCEL_PROJECT_ID): prj_AbCdEfGhIj1234
   ```

**方法2: 直接コマンド（参考）**

組織IDのみを確認したい場合：

1. **現在のユーザー情報を確認**
   ```bash
   vercel whoami
   ```

2. **チーム一覧を確認**
   ```bash
   vercel teams list
   ```

#### **`vercel link`の安全性について**

✅ **完全に安全です**:
- **非破壊的**: 既存のコードやファイルを変更しません
- **設定のみ**: ローカルの`.vercel`フォルダに設定ファイルを作成するだけ
- **リバーシブル**: いつでも`.vercel`フォルダを削除して元に戻せます
- **推奨方法**: Vercel公式の推奨する正しい方法です

💡 **トラブルシューティング**:
- **コマンドが見つからない**: Node.jsとnpmが正しくインストールされているか確認
- **ログインできない**: ブラウザでVercelにログインしているか確認
- **プロジェクトが見つからない**: Vercelダッシュボードでプロジェクトが作成済みか確認
- **権限エラー**: 管理者権限でターミナルを実行

### ✅ Vercel設定完了チェック

- [ ] Vercel Dashboardにログインできた
- [ ] プロジェクトを作成できた
- [ ] Git連携を解除できた
- [ ] APIトークンを作成できた
- [ ] トークン情報をメモ帳に保存した
- [ ] プロジェクトIDと組織IDをメモ帳に保存した

---

## 🔧 ステップ4: GitHub設定（15分）

### 4-1. GitHubリポジトリにアクセス

1. **ブラウザで以下のURLを開く**
   ```
   https://github.com/your-username/excel-unlocker
   ```
   - ※ 実際のリポジトリURLに変更してください

2. **「Settings」をクリック**

### 4-2. NextAuthシークレットの生成

1. **新しいタブで以下のURLを開く**
   ```
   https://generate-secret.vercel.app/32
   ```

2. **生成されたランダム文字列をメモ帳にコピー**
   ```
   NextAuthシークレット: s3cure-secret-please-change-this-to-random-string-32-chars-long
   ```

### 4-3. Repository Secretsの設定

1. **左メニュー「Secrets and variables」→「Actions」をクリック**

2. **「New repository secret」をクリックして以下を1つずつ追加**

   | Name | Value（メモ帳から転記） | 説明 |
   |------|----------------------|------|
   | `AWS_ACCESS_KEY_ID` | AWSのアクセスキーID | AWS認証用 |
   | `AWS_SECRET_ACCESS_KEY` | AWSのシークレットアクセスキー | AWS認証用 |
   | `VERCEL_TOKEN` | Vercelのトークン | Vercelデプロイ認証用 |
   | `VERCEL_ORG_ID` | VercelのTeam ID/User ID | **必須**: プロジェクト所有者識別用 |
   | `VERCEL_PROJECT_ID` | VercelのプロジェクトID | デプロイ対象プロジェクト識別用 |
   | `GOOGLE_CLIENT_ID` | GoogleのクライアントID | Google OAuth認証用 |
   | `GOOGLE_CLIENT_SECRET` | Googleのクライアントシークレット | Google OAuth認証用 |
   | `NEXTAUTH_SECRET` | 生成したNextAuthシークレット | セッション暗号化用 |

3. **各Secretの追加手順**
   - 「Name」に上記の名前を正確に入力
   - 「Secret」にメモ帳の対応する値を入力
   - 「Add secret」をクリック
   - 次のSecretの追加に進む

### 4-4. GitHub Actionsの動作確認

1. **「Actions」タブをクリック**

2. **「Deploy Full Stack」ワークフローをクリック**

3. **「Run workflow」をクリック**

4. **設定を選択**
   ```
   Use workflow from: main
   Environment: development
   Deploy backend: チェック
   Deploy frontend: チェック
   Run tests: チェック
   ```

5. **「Run workflow」をクリック**

6. **実行状況を確認**
   - 実行が開始されるまで1-2分待ちます
   - 全ステップが緑色（成功）になることを確認

### ✅ GitHub設定完了チェック

- [ ] GitHubリポジトリにアクセスできた
- [ ] NextAuthシークレットを生成できた
- [ ] 8個のRepository Secretsを設定できた
- [ ] GitHub Actionsワークフローを実行できた
- [ ] ワークフローが成功した（全ステップが緑色）

---

## ✅ ステップ5: 動作確認（10分）

### 5-1. デプロイされたアプリの確認

1. **Vercel Dashboardに戻る**
   ```
   https://vercel.com/dashboard
   ```

2. **プロジェクト「excel-unlocker」をクリック**

3. **「Visit」をクリック**
   - 新しいタブでアプリが開きます

4. **アプリの表示確認**
   - Excel Unlockerのトップページが表示されることを確認

### 5-2. Google OAuth認証の確認

1. **「ログイン」ボタンをクリック**

2. **Google認証画面の確認**
   - Googleの認証画面が表示されることを確認
   - 設定したGoogleアカウントでログイン

3. **認証後の画面確認**
   - ログイン後、ユーザー情報が表示されることを確認
   - 「ログアウト」ボタンが表示されることを確認

### 5-3. 基本機能の確認

1. **ファイルアップロード機能**
   - ファイル選択エリアが表示されることを確認
   - ドラッグ&ドロップエリアが表示されることを確認

2. **パスワード入力フォーム**
   - パスワード入力欄が表示されることを確認
   - 「解除開始」ボタンが表示されることを確認

3. **Google Drive連携**
   - 「Google Driveに保存」オプションが表示されることを確認

### 5-4. エラーがないことの確認

1. **ブラウザの開発者ツールを開く**
   - Windows: F12キー
   - Mac: Command + Option + I

2. **「Console」タブを確認**
   - 赤色のエラーメッセージがないことを確認
   - 警告（黄色）は無視して構いません

### ✅ 動作確認完了チェック

- [ ] デプロイされたアプリにアクセスできた
- [ ] トップページが正常に表示された
- [ ] Google OAuth認証が機能した
- [ ] ログイン・ログアウトができた
- [ ] 基本的なUI要素が表示された
- [ ] ブラウザコンソールにエラーがない

---

## 🎉 セットアップ完了！

### 🏆 達成したこと

おめでとうございます！以下の機能を持つExcel Unlockerアプリが完成しました：

- ✅ **セキュアな認証システム**: Googleアカウントでの安全なログイン
- ✅ **複数ファイル一括処理**: 複数のExcelファイルを同時に解除
- ✅ **Google Drive連携**: 解除済みファイルを直接Google Driveに保存
- ✅ **全デバイス対応**: iPhone、Android、PC、Macで利用可能
- ✅ **自動デプロイ**: コード変更時の自動更新機能
- ✅ **社内限定アクセス**: 招待されたユーザーのみ利用可能

### 📱 アプリの使い方

1. **アクセス**: デプロイされたURLにアクセス
2. **ログイン**: Googleアカウントでログイン
3. **ファイル選択**: 解除したいExcelファイルを選択
4. **パスワード入力**: 候補パスワードを入力
5. **解除実行**: 「解除開始」ボタンをクリック
6. **結果確認**: 解除済みファイルをダウンロードまたはGoogle Driveに保存

### 🔧 管理者向け情報

#### ユーザーの追加方法
新しいユーザーを追加する場合：

1. **Google Cloud Console**でOAuth同意画面のテストユーザーに追加
2. **AWS Lambda**の環境変数`ALLOWED_USERS`にメールアドレスを追加

#### 設定変更方法
- **フロントエンド設定**: Vercelの環境変数を変更
- **バックエンド設定**: AWS Lambdaの環境変数を変更
- **認証設定**: Google Cloud Consoleで変更

---

## 📚 よくある質問（FAQ）

### Q1. ログインできません
**A1.** 以下を確認してください：
- Google Cloud ConsoleのOAuth同意画面でテストユーザーに追加されているか
- リダイレクトURIが正しく設定されているか
- ブラウザのCookieが有効になっているか

### Q2. ファイルアップロードでエラーが出ます
**A2.** 以下を確認してください：
- ファイルサイズが20MB以下か
- ファイル形式が.xlsxまたは.xlsか
- インターネット接続が安定しているか

### Q3. パスワード解除に失敗します
**A3.** 以下を確認してください：
- 入力したパスワードが正しいか
- ファイルが破損していないか
- 複数のパスワード候補を試してみる

### Q4. Google Driveに保存できません
**A4.** 以下を確認してください：
- Google Driveのスコープが正しく設定されているか
- Google Driveの容量に余裕があるか
- ブラウザでGoogle Driveへのアクセス許可を与えているか

### Q5. 設定を変更したいです
**A5.** 以下の手順で変更できます：
- **ユーザー追加**: Google Cloud ConsoleとAWS Lambdaで設定
- **ドメイン変更**: Vercel、Google Cloud Console、GitHub Secretsで設定
- **機能追加**: 開発者に相談してください

---

## 🚨 トラブルシューティング

### 問題発生時の診断フロー

```mermaid
flowchart TD
    A[問題発生] --> B{どこで問題？}
    B -->|ログイン時| C[Google OAuth設定確認]
    B -->|ファイル処理時| D[AWS設定確認]
    B -->|画面表示時| E[Vercel設定確認]
    B -->|デプロイ時| F[GitHub Actions確認]
    
    C --> G[OAuth同意画面設定]
    C --> H[リダイレクトURI設定]
    C --> I[テストユーザー設定]
    
    D --> J[IAM権限確認]
    D --> K[S3バケット確認]
    D --> L[Lambda関数確認]
    
    E --> M[環境変数確認]
    E --> N[ドメイン設定確認]
    E --> O[ビルド設定確認]
    
    F --> P[Repository Secrets確認]
    F --> Q[ワークフロー設定確認]
    F --> R[権限設定確認]
```

### 緊急時の対処法

#### 1. アプリが全く動かない場合
```bash
# GitHub Actionsで再デプロイを実行
1. GitHubリポジトリの「Actions」タブ
2. 「Deploy Full Stack」を選択
3. 「Run workflow」で再実行
```

#### 2. ログインできない場合
```bash
# Google OAuth設定を確認
1. Google Cloud Console → APIとサービス → 認証情報
2. OAuth クライアントIDの設定を確認
3. リダイレクトURIが正しいか確認
```

#### 3. ファイル処理でエラーが出る場合
```bash
# AWS設定を確認
1. AWS Management Console → Lambda
2. 関数のログを確認
3. IAM権限を確認
```

### サポート連絡先

技術的な問題で解決できない場合：

1. **社内IT部門**に連絡
2. **開発者**に連絡（設定ファイルを共有）
3. **このドキュメント**を参照して再設定

---

## 📖 参考資料

### 公式ドキュメント
- [Google OAuth 2.0 ガイド](https://developers.google.com/identity/protocols/oauth2)
- [AWS 入門ガイド](https://aws.amazon.com/jp/getting-started/)
- [Vercel デプロイメントガイド](https://vercel.com/docs)
- [GitHub Actions ガイド](https://docs.github.com/ja/actions)

### 追加学習リソース
- [Next.js 公式チュートリアル](https://nextjs.org/learn)
- [AWS Lambda 入門](https://aws.amazon.com/jp/lambda/getting-started/)
- [React 基礎学習](https://ja.reactjs.org/tutorial/tutorial.html)

### コミュニティサポート
- [Stack Overflow](https://stackoverflow.com/) - 技術的な質問
- [GitHub Discussions](https://github.com/discussions) - プロジェクト固有の質問
- [Discord コミュニティ](https://discord.com/) - リアルタイムサポート

---

## 🎯 次のステップ

### 運用開始後の推奨事項

1. **定期的な動作確認**（月1回）
   - ログイン機能の確認
   - ファイル処理機能の確認
   - Google Drive連携の確認

2. **ユーザー管理**
   - 新規ユーザーの追加手順の確認
   - 退職者のアクセス権削除

3. **セキュリティ更新**
   - 依存関係の定期更新
   - セキュリティパッチの適用

4. **利用状況の監視**
   - AWS CloudWatchでの利用状況確認
   - コスト監視の設定

### 機能拡張の検討

将来的に以下の機能追加を検討できます：

- **処理履歴機能**: 過去の処理結果の確認
- **管理者ダッシュボード**: 利用状況の可視化
- **通知機能**: 処理完了時のメール通知
- **API連携**: 他システムとの連携

---

**🎊 Excel Unlockerのセットアップが完了しました！**

このガイドに従って設定したExcel Unlockerアプリを、安心してご利用ください。何か問題が発生した場合は、このドキュメントのトラブルシューティングセクションを参照するか、社内のIT担当者にご相談ください。

**素晴らしいExcel解除ライフをお楽しみください！** 🚀