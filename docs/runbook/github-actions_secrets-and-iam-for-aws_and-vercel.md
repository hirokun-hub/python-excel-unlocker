# GitHub Actions 用 Secrets と AWS/IAM・Vercel 準備ランブック

対象読者: 初めてGitHub Actionsでクラウドにデプロイする人。どこで何を登録するかを具体化します。公式の最新UIや命名は随時変わるため、必要に応じて公式ドキュメントを参照してください（末尾リンク）。

---

## ゴール

- GitHub リポジトリの Actions Secrets に必要な値を登録する
- AWS 側に最小権限の IAM ユーザーを作成し、アクセスキーを発行する
- Vercel API 用の `VERCEL_TOKEN`/`VERCEL_ORG_ID`/`VERCEL_PROJECT_ID` を登録する
- 環境ごとの変数（Production/Preview/Staging）を迷わず管理できるようにする

---

## 1. GitHub Actions Secrets の場所

1) ブラウザで GitHub を開く → 対象リポジトリ
2) 「Settings」→ 左メニュー「Secrets and variables」→「Actions」
3) 「New repository secret」で1件ずつ登録

登録する主なキー（ダミー値例）:
```
# AWS（SAMデプロイ）
AWS_ACCESS_KEY_ID=AKIAEXAMPLE1234567890
AWS_SECRET_ACCESS_KEY=abcdEFGHijklMNOPqrstUVWXyz0123456789example
AWS_REGION=ap-northeast-1

# Vercel（フロントデプロイ）
VERCEL_TOKEN=vc_1a2b3c4d5e6f_example_only
VERCEL_ORG_ID=team_7g8h9i0j_example
VERCEL_PROJECT_ID=prj_KLMNoP123_example

# Auth.js（NextAuth）/ Google
GOOGLE_CLIENT_ID=1234567890-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc_defg-hijklmnop
NEXTAUTH_SECRET=s3cure-secret-please-change

# フロント用APIエンドポイント
NEXT_PUBLIC_API_URL=https://api.example.com
```

補足:
- `NEXT_PUBLIC_*` はJSに埋め込まれるため公開前提。秘匿不要な値のみ登録してください。
- 環境ごとに値を変えたい場合は、
  - 方式A: Secret名に suffix を付ける（例: `AWS_ACCESS_KEY_ID_PROD`）
  - 方式B: GitHub Environments を使い、環境別にシークレットを分ける（推奨）

---

## 2. AWS IAMユーザーの作成（最小権限）

1) `https://console.aws.amazon.com/iam/` に管理者でログイン
2) 左メニュー「ユーザー」→「ユーザーを追加」
3) ユーザー名: `github-deploy-bot`
4) 「アクセスキー - プログラムによるアクセス」を有効化
5) 権限の設定:
   - ポリシーを直接アタッチ → 最小権限のカスタムポリシーを作成して付与

最小権限ポリシー例（必要に応じてリソースARNを絞る）:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:Describe*",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack"
      ], "Resource": "*" },
    { "Effect": "Allow", "Action": [
        "s3:PutObject","s3:GetObject","s3:DeleteObject","s3:ListBucket"
      ], "Resource": "*" },
    { "Effect": "Allow", "Action": [
        "lambda:*"
      ], "Resource": "*" },
    { "Effect": "Allow", "Action": [
        "iam:PassRole"
      ], "Resource": "*" }
  ]
}
```

6) アクセスキーを発行 → `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` を控える
   - 画面を閉じると再表示できないため、その場でGitHubに登録するのが安全

---

## 3. Vercel 用の値（再掲）

- `VERCEL_TOKEN`: `https://vercel.com/account/tokens` で作成
- `VERCEL_ORG_ID`: チーム/個人のID（`team_xxx` 形式）
- `VERCEL_PROJECT_ID`: 対象プロジェクトのID（`prj_xxx` 形式）

全て GitHub の Actions Secrets に登録します。

---

## 4. Secrets と Vercel Env の役割分担

- GitHub Secrets: CI/CD パイプライン（Actions）内でのみ使う。ビルド・デプロイに必要な資格情報
- Vercel Environment Variables: 実行時/ビルド時にフロントが参照する値
  - 例: `NEXT_PUBLIC_API_URL`, `NEXTAUTH_URL`, `GOOGLE_*`, `NEXTAUTH_SECRET`
  - Production と Preview で値を分けられる

---

## 5. ワークフロー（概念）

GitHub Actions の一般的な流れ（概略）:
1) チェックアウト
2) Node セットアップ → `frontend` を build
3) Vercel CLI を用いて `--token ${{ secrets.VERCEL_TOKEN }}` でデプロイ
4) Python/SAM セットアップ → `sam build` / `sam deploy`（`AWS_*` Secrets を使用）

Tips:
- Vercel の Git 連携を解除済みでも、API経由（CLI）でのデプロイは可能
- 並列実行によりフロント/バックのスループットを上げられるが、最初は直列がおすすめ

---

## 6. 総合チェックリスト（CORS/Origin/Callback）

- Google OAuth
  - 承認済みの JavaScript 生成元: `https://app.example.com`, `https://*.vercel.app`
  - 承認済みのリダイレクトURI: `https://app.example.com/api/auth/callback/google`, `https://*.vercel.app/api/auth/callback/google`
- Vercel Env
  - `NEXT_PUBLIC_API_URL` が本番/プレビューで正しい
  - `NEXTAUTH_URL` が本番/プレビューで正しい
- API Gateway（SAM `template.yaml`）
  - CORS の AllowOrigin が本番ドメインに限定されている
- S3 CORS
  - フロントのオリジンが許可されている

---

## 7. スモーク実行（GitHubから）

1) GitHub → 「Actions」→ 既存のデプロイ用ワークフローを選択
2) 「Run workflow」→ `environment: production` を選択（あるいは `staging`）
3) 実行後、Vercelの「Deployments」とAWSのCloudFormationスタックが更新されたことを確認

---

## 参考リンク（最新情報を確認）

- GitHub Actions Secrets: `https://docs.github.com/actions/security-guides/using-secrets-in-github-actions`
- AWS IAM ベストプラクティス: `https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html`
- AWS SAM Deploy: `https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference-sam-deploy.html`
- Vercel CLI Deploy: `https://vercel.com/docs/cli/deploy`


