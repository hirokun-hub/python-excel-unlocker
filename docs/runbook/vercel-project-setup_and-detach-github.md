# Vercel プロジェクト設定と GitHub 連携解除（GitHub Actions でのデプロイ移行）

対象読者: 初めてVercelを触る人。画面でどこを押すか、何を入力するかを具体的に記載します。最新UIの表記は変わる場合があるため、適宜Vercel公式の最新ドキュメントも参照してください（「参考リンク」参照）。

---

## ゴール

- Vercel上のフロントエンド本番/プレビュー環境を正しく設定する
- VercelのGitHub自動連携（プッシュ→自動デプロイ）をオフ/解除する
- GitHub ActionsからVercel APIを使ってデプロイできる状態にする（`VERCEL_TOKEN`/`VERCEL_ORG_ID`/`VERCEL_PROJECT_ID`を取得）
- Vercelの環境変数（Production/Preview）を設定する

---

## 事前準備

- Vercelアカウント（無料可）
- GitHubリポジトリ（このプロジェクト）
- 本番用ドメイン（任意。`*.vercel.app`のみでも可）

---

## 1. プロジェクトの確認（または新規作成）

1) ブラウザで `https://vercel.com/dashboard` にアクセスしログイン
2) 既存のプロジェクト `Excel_Password`（例）をクリック
   - 新規作成する場合は「New Project」→「Import」からGitHubを選択して作成可能です。後でGit連携は解除します。

---

## 2. GitHub連携を解除（自動デプロイを止める）

1) プロジェクト画面右上「Settings」をクリック
2) 左のメニューから「Git」を選択
3) 「Git Integration」セクションで、現在のリポジトリがリンクされている場合は「Disconnect」または「Remove Link」をクリック
   - 確認ダイアログが出たら「Disconnect」を選択
4) これで「Gitのプッシュ → Vercel自動デプロイ」は停止します

注意:
- 将来また自動デプロイに戻したい場合は、同じ画面で再度GitHubリポジトリをリンクしてください

---

## 3. Vercelトークン・組織ID・プロジェクトIDを取得

GitHub ActionsからVercelにデプロイするために、以下の3つが必要です。
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

方法A: ダッシュボードで確認（推奨）
1) トークン: `https://vercel.com/account/tokens` → 「Create」→ 任意の名前（例: `github-actions-token`）→ 生成されたトークンをコピー（例: `vc_1234567890abcdef...`）
2) 組織ID/プロジェクトID: プロジェクトの「Settings」→「General」→ 下部の「Project ID」をコピー（例: `prj_AbCdEfGhIj1234`）。組織（Personal/Team）も同画面上部で確認できます。組織のIDは `Settings` → `Teams`（またはアカウント設定）で `team_********` 形式が確認できます。

方法B: Vercel CLIで確認（補助）
```bash
# ローカルで（必要なら）
npm i -g vercel
vercel login
vercel projects ls | cat
```

ダミー例（コピーして使わないでください）:
```
VERCEL_TOKEN=vc_1a2b3c4d5e6f_example_only
VERCEL_ORG_ID=team_7g8h9i0j_example
VERCEL_PROJECT_ID=prj_KLMNoP123_example
```

---

## 4. 環境変数をVercelに登録（Production/Preview）

1) プロジェクトの「Settings」→「Environment Variables」
2) 「Add New」を押して以下を追加します

推奨のキー（ダミー値例付き）:
- `NEXT_PUBLIC_API_URL`
  - Production: `https://api.example.com`（API Gateway の本番URL）
  - Preview: `https://api-staging.example.com` または `https://xxxx.execute-api.ap-northeast-1.amazonaws.com/staging`
- `NEXTAUTH_URL`
  - Production: `https://app.example.com`
  - Preview: `https://your-project-git-branch-username.vercel.app`
- `NEXTAUTH_SECRET`
  - Production/Preview: `s3cure-secret-please-change`（十分に長いランダム文字列）
- `GOOGLE_CLIENT_ID`
  - Production/Preview: `1234567890-abcdefg.apps.googleusercontent.com`
- `GOOGLE_CLIENT_SECRET`
  - Production/Preview: `GOCSPX-abc_defg-hijklmnop`

入力のコツ:
- 「Environment」で `Production` と `Preview` を切り替えて、同じキーでも値を分けて登録できます
- `NEXT_PUBLIC_` で始まる値はクライアントに公開される点に注意（秘密値は避ける）

---

## 5. ドメイン設定（任意）

1) 「Settings」→「Domains」→ 「Add」
2) 本番用ドメイン `app.example.com` を追加
3) 提示されるDNS設定（CNAME等）をドメイン側に設定
4) 自動でTLS証明書が配布されます（反映に数分〜数十分）

プレビュー用は `*.vercel.app` が自動で用意されます

---

## 6. Build 設定の確認

1) 「Settings」→「Build & Development Settings」
2) Framework が「Next.js」になっていることを確認
3) Build Command / Output は自動検出でOK（特殊要件がなければ変更不要）

---

## 7. 接続確認（スモーク）

GitHub Actions設定後に、任意のブランチで「手動トリガーのデプロイ」を実施し、Vercelの「Deployments」タブに新しいデプロイが作成されることを確認します。

チェック:
- Deployment が `BUILD PASSED` になっている
- 該当デプロイのURLでアプリが表示される
- ログイン（Google OAuth）が開始できる（詳細は「Google OAuth設定」参照）

---

## よくあるトラブル

- GitHubを切ったのに自動デプロイが走る
  - 他の自動連携（Import Flow）が残っていないか「Git」設定を再確認
- 403や環境変数未設定エラー
  - `NEXT_PUBLIC_API_URL` と `NEXTAUTH_URL`、`NEXTAUTH_SECRET` が正しく登録され、対象環境（Production/Preview）になっているか
- Google OAuthのエラー
  - `GOOGLE_CLIENT_ID/SECRET` が正しいか、Google側の「Authorized redirect URI/Origin」が正しく本番/プレビューを含んでいるか

---

## 参考リンク（最新UIは公式で確認）

- Vercel 環境変数: `https://vercel.com/docs/projects/environment-variables`
- Vercel トークン: `https://vercel.com/docs/accounts/tokens`
- Vercel Git連携: `https://vercel.com/docs/projects/deployments/git`


