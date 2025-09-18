# クイックリファレンス - スクリーンショット付きガイド

## 📸 概要

このドキュメントは、Excel Unlocker セットアップ時の**重要な画面**と**設定箇所**をスクリーンショット付きで説明します。実際のUI画面で迷わないための視覚的ガイドです。

> **注意**: UIは随時更新されるため、最新の画面と異なる場合があります。その場合は各サービスの公式ドキュメントを参照してください。

---

## 🔐 Google Cloud Console

### OAuth 同意画面の設定

#### 1. APIとサービスへの移動
```
📍 場所: https://console.cloud.google.com/
👆 クリック箇所: ハンバーガーメニュー（≡）→ APIとサービス → OAuth 同意画面
```

**画面の特徴**:
- 左上にハンバーガーメニュー（3本線）
- 「APIとサービス」は青いアイコン
- 「OAuth 同意画面」は左メニューの上部にある

#### 2. アプリ情報入力画面
```
📝 入力項目:
- アプリ名: Secure Excel Unlock
- ユーザーサポートメール: your-email@example.com
- アプリドメイン: your-domain.com
- 承認済みドメイン: your-domain.com, vercel.app
```

**画面の特徴**:
- 「アプリ名」は必須項目（赤いアスタリスク）
- 「承認済みドメイン」は下部にある
- 「保存して次へ」ボタンで進む

#### 3. スコープ設定画面
```
✅ 選択するスコープ:
- ../auth/userinfo.email
- ../auth/userinfo.profile  
- openid
- ../auth/drive.file（Google Drive連携用）
```

**画面の特徴**:
- 「スコープを追加または削除」ボタンをクリック
- 検索ボックスで「userinfo」「drive」を検索
- チェックボックスで選択

### OAuth クライアントID作成

#### 1. 認証情報画面
```
📍 場所: APIとサービス → 認証情報
👆 クリック箇所: + 認証情報を作成 → OAuth クライアントID
```

**画面の特徴**:
- 上部に青い「+ 認証情報を作成」ボタン
- ドロップダウンメニューから「OAuth クライアントID」を選択

#### 2. クライアント設定画面
```
📝 設定項目:
- アプリケーションの種類: ウェブアプリケーション
- 名前: secure-excel-unlock-web-client

承認済みのJavaScript生成元:
- https://your-domain.com
- https://*.vercel.app
- http://localhost:3000

承認済みのリダイレクトURI:
- https://your-domain.com/api/auth/callback/google
- https://*.vercel.app/api/auth/callback/google
- http://localhost:3000/api/auth/callback/google
```

**画面の特徴**:
- 「ウェブアプリケーション」を選択
- 「URIを追加」ボタンで複数のURIを追加
- 各URIは正確に入力（末尾のスラッシュに注意）

#### 3. 認証情報取得画面
```
📋 取得する値:
- クライアントID: 1234567890-abcdefghijklmnop.apps.googleusercontent.com
- クライアントシークレット: GOCSPX-abcdefghijklmnopqrstuvwxyz
```

**画面の特徴**:
- ポップアップダイアログで表示
- コピーボタンでクリップボードにコピー
- ⚠️ この画面を閉じると再表示できない

---

## ☁️ AWS Management Console

### IAM ユーザー作成

#### 1. IAM ダッシュボード
```
📍 場所: https://console.aws.amazon.com/iam/
👆 クリック箇所: 左メニュー「ユーザー」→「ユーザーを追加」
```

**画面の特徴**:
- 左メニューに「ユーザー」「グループ」「ロール」「ポリシー」
- 「ユーザーを追加」は青いボタン

#### 2. ユーザー詳細画面
```
📝 入力項目:
- ユーザー名: github-deploy-bot
- アクセスの種類: プログラムによるアクセス（チェック）
```

**画面の特徴**:
- 「プログラムによるアクセス」にチェック
- 「AWS Management Console へのアクセス」はチェック不要

#### 3. アクセス許可設定画面
```
👆 選択項目:
- 既存のポリシーを直接アタッチ
- ポリシーの作成（新しいタブで開く）
```

**画面の特徴**:
- 3つのオプションから「既存のポリシーを直接アタッチ」を選択
- 「ポリシーの作成」リンクをクリック

### IAM ポリシー作成

#### 1. ポリシー作成画面
```
👆 選択項目:
- JSON タブを選択
- ポリシードキュメントを貼り付け
```

**画面の特徴**:
- 「ビジュアルエディタ」と「JSON」のタブ
- JSONタブでポリシーを直接編集

#### 2. ポリシー確認画面
```
📝 入力項目:
- 名前: ExcelUnlockerDeployPolicy
- 説明: Excel Unlocker deployment policy with minimal permissions
```

**画面の特徴**:
- 「名前」は必須項目
- 「説明」は任意だが推奨

### S3 バケット作成

#### 1. S3 ダッシュボード
```
📍 場所: https://console.aws.amazon.com/s3/
👆 クリック箇所: バケットを作成
```

**画面の特徴**:
- オレンジ色の「バケットを作成」ボタン
- 既存バケットの一覧が表示

#### 2. バケット設定画面
```
📝 設定項目:
- バケット名: excel-unlocker-bucket-production-{account-id}-ap-northeast-1
- リージョン: アジアパシフィック (東京) ap-northeast-1
- パブリックアクセス設定: すべてブロック（デフォルト）
```

**画面の特徴**:
- バケット名は全世界で一意である必要がある
- リージョンはドロップダウンで選択
- パブリックアクセス設定はデフォルトのまま

---

## 🚀 Vercel Dashboard

### プロジェクト作成

#### 1. Vercel ダッシュボード
```
📍 場所: https://vercel.com/dashboard
👆 クリック箇所: New Project
```

**画面の特徴**:
- 右上に「New Project」ボタン
- 既存プロジェクトがカード形式で表示

#### 2. Git リポジトリ選択
```
👆 選択項目:
- Import Git Repository
- GitHubリポジトリを選択
- Import ボタンをクリック
```

**画面の特徴**:
- GitHub、GitLab、Bitbucketのタブ
- リポジトリ一覧から選択
- 「Import」ボタンで進む

#### 3. プロジェクト設定
```
📝 設定項目:
- Project Name: excel-unlocker
- Framework Preset: Next.js（自動検出）
- Root Directory: frontend
- Build Command: npm run build（自動設定）
- Output Directory: .next（自動設定）
```

**画面の特徴**:
- Framework Presetは自動検出される
- Root Directoryは手動で「frontend」に変更
- Build設定は通常自動で正しく設定される

### Git連携解除

#### 1. プロジェクト設定画面
```
📍 場所: プロジェクトダッシュボード → Settings
👆 クリック箇所: 左メニュー「Git」
```

**画面の特徴**:
- 左メニューに「General」「Domains」「Git」など
- 「Git」セクションに現在の連携状況が表示

#### 2. Git連携解除
```
👆 クリック箇所:
- Connected Git Repository セクション
- Disconnect ボタン
- 確認ダイアログで Disconnect
```

**画面の特徴**:
- 現在連携中のリポジトリが表示
- 「Disconnect」ボタンは赤色
- 確認ダイアログが表示される

### 環境変数設定

#### 1. 環境変数画面
```
📍 場所: Settings → Environment Variables
👆 クリック箇所: Add New
```

**画面の特徴**:
- 「Add New」ボタンで新しい環境変数を追加
- 既存の環境変数が一覧表示

#### 2. 環境変数追加ダイアログ
```
📝 入力項目:
- Name: NEXT_PUBLIC_API_URL
- Value: https://your-api-gateway-url
- Environment: Production, Preview（両方選択）
```

**画面の特徴**:
- Name、Value、Environmentの3つの入力項目
- Environmentは複数選択可能
- 「Add」ボタンで追加

### API認証情報取得

#### 1. Vercel Token作成
```
📍 場所: https://vercel.com/account/tokens
👆 クリック箇所: Create Token
```

**画面の特徴**:
- 「Create Token」ボタン
- 既存トークンの一覧が表示

#### 2. Token設定ダイアログ
```
📝 設定項目:
- Token Name: github-actions-deploy
- Scope: Full Account
- Expiration: No Expiration（推奨）
```

**画面の特徴**:
- Token Nameは任意の名前
- Scopeは用途に応じて選択
- Expirationは期限設定

#### 3. プロジェクトID確認
```
📍 場所: プロジェクト → Settings → General
📋 確認項目:
- Project ID: prj_AbCdEfGhIj1234
- Team ID: team_XyZ789（チームの場合）
```

**画面の特徴**:
- General設定の下部に表示
- コピーボタンでクリップボードにコピー

---

## 🔧 GitHub Repository

### Secrets設定

#### 1. リポジトリ設定画面
```
📍 場所: GitHubリポジトリ → Settings
👆 クリック箇所: 左メニュー「Secrets and variables」→「Actions」
```

**画面の特徴**:
- 左メニューの「Security」セクション内
- 「Secrets and variables」を展開
- 「Actions」を選択

#### 2. Secret追加画面
```
👆 クリック箇所: New repository secret
📝 入力項目:
- Name: AWS_ACCESS_KEY_ID
- Secret: AKIAIOSFODNN7EXAMPLE
```

**画面の特徴**:
- 「New repository secret」は緑色のボタン
- Nameは大文字・アンダースコア使用
- Secretは入力後に隠される

#### 3. Secrets一覧画面
```
✅ 設定確認:
- AWS_ACCESS_KEY_ID ✓
- AWS_SECRET_ACCESS_KEY ✓
- VERCEL_TOKEN ✓
- VERCEL_ORG_ID ✓
- VERCEL_PROJECT_ID ✓
- GOOGLE_CLIENT_ID ✓
- GOOGLE_CLIENT_SECRET ✓
- NEXTAUTH_SECRET ✓
```

**画面の特徴**:
- 設定済みSecretsが一覧表示
- 値は「***」で隠される
- 「Updated」に最終更新日時が表示

### Actions実行

#### 1. Actions画面
```
📍 場所: GitHubリポジトリ → Actions
👆 クリック箇所: 実行したいワークフロー名
```

**画面の特徴**:
- 左側にワークフロー一覧
- 右側に実行履歴
- 緑色のチェックマークは成功、赤色のXは失敗

#### 2. 手動実行画面
```
👆 クリック箇所:
- Run workflow ボタン
- Environment選択（production/staging/development）
- Run workflow（確定）
```

**画面の特徴**:
- 「Run workflow」は青色のボタン
- ドロップダウンで環境を選択
- 入力項目がある場合は表示される

#### 3. 実行ログ画面
```
📊 確認項目:
- 各ステップの実行状況
- エラーメッセージ（失敗時）
- 実行時間
- アーティファクト（生成された場合）
```

**画面の特徴**:
- 左側にジョブ一覧
- 右側に詳細ログ
- 展開可能なセクション

---

## 🎯 設定確認のポイント

### Google OAuth設定確認
```
✅ チェックポイント:
□ OAuth同意画面でアプリ名が設定されている
□ 必要なスコープが選択されている
□ テストユーザーが追加されている
□ クライアントIDが作成されている
□ JavaScript生成元に本番・プレビューURLが含まれている
□ リダイレクトURIに正確なコールバックURLが含まれている
```

### AWS設定確認
```
✅ チェックポイント:
□ IAMユーザーが作成されている
□ 最小権限ポリシーがアタッチされている
□ アクセスキーが発行されている
□ S3バケットが作成されている
□ バケット名が一意である
□ パブリックアクセスがブロックされている
```

### Vercel設定確認
```
✅ チェックポイント:
□ プロジェクトが作成されている
□ Git連携が解除されている
□ 必要な環境変数が設定されている
□ Production/Preview両方に設定されている
□ APIトークンが作成されている
□ プロジェクトID・組織IDが取得されている
```

### GitHub Actions設定確認
```
✅ チェックポイント:
□ 必要なSecretsがすべて設定されている
□ Secret名に typo がない
□ ワークフローファイルが存在している
□ 手動実行が可能である
□ 実行ログでエラーが発生していない
```

---

## 🚨 よくある画面での間違い

### Google Cloud Console
```
❌ よくある間違い:
- 「内部」と「外部」を間違える → 通常は「外部」を選択
- リダイレクトURIの末尾に余分なスラッシュ → 正確なURLを入力
- JavaScript生成元にパスを含める → オリジンのみ（パス不要）
- スコープの選択漏れ → 必要なスコープをすべて選択
```

### AWS Console
```
❌ よくある間違い:
- 「AWS Management Console へのアクセス」をチェック → 不要
- ポリシーのリソース指定が広すぎる → 最小権限に限定
- バケット名にアンダースコアを使用 → ハイフンを使用
- リージョンの選択間違い → ap-northeast-1（東京）を選択
```

### Vercel Dashboard
```
❌ よくある間違い:
- Root Directoryを設定しない → 「frontend」に設定
- 環境変数をProductionのみに設定 → Preview環境にも設定
- Git連携を解除しない → 自動デプロイが重複する
- NEXT_PUBLIC_プレフィックスの付け忘れ → クライアント側で必要な変数に付ける
```

### GitHub Repository
```
❌ よくある間違い:
- Secret名の大文字小文字間違い → 正確な名前を使用
- 環境変数とSecretsの混同 → 用途に応じて適切な場所に設定
- ワークフロー実行権限不足 → リポジトリの権限設定を確認
- 手動実行時の環境選択間違い → 正しい環境を選択
```

---

## 📱 モバイル・タブレット対応

### スマートフォンでの設定
```
📱 注意点:
- 画面が小さいため、メニューが折りたたまれている場合がある
- ハンバーガーメニューを使用してナビゲーション
- 長いURLやキーの入力時は横画面を推奨
- コピー&ペースト機能を活用
```

### タブレットでの設定
```
📱 注意点:
- デスクトップ版とほぼ同じUI
- タッチ操作でのクリック精度に注意
- 複数タブでの作業が可能
- キーボード接続時はショートカットキーが使用可能
```

---

**🎉 これで視覚的なガイドは完了です！実際の画面と照らし合わせながら設定を進めてください。**