# Google 認証まわりの現状と次のアクション整理（2025-10-04）

## ここまでの流れ

- GitHub Secrets を確認したところ、`GOOGLE_CLIENT_ID` と `GOOGLE_CLIENT_SECRET` は登録済みだったが、NextAuth.js が必須とする `NEXTAUTH_SECRET` と `NEXTAUTH_URL` は登録されていなかった。
- Vercel CLI で環境変数を確認したところ、Preview 環境に `NEXT_PUBLIC_USE_MOCK_API` / `NEXT_PUBLIC_API_URL` のみが存在し、Production には何も設定されていなかった。`frontend/vercel.json` が参照する `@nextauth_secret` などが存在しないため、Google ログイン処理が 500 で失敗していたと推測される。
- `.env.local` には `AUTH_SECRET` という名前で値が置かれていたが、NextAuth.js が読むキーは `NEXTAUTH_SECRET` のため、ローカルでもサーバーエラーが起きる状態だった。
- `docs/setup/vercel-environment-variables.md` を作成し、Vercel ダッシュボード／CLI から環境変数を正しく登録する手順をまとめた。開発者はこの手順に従って本番・プレビューの値を入力できるようになった。

## いまの状態

- Vercel プロジェクトは `frontend` ディレクトリで `vercel link` 済み。CLI から `vercel env ls` が実行できる。
- ただし必須値（`NEXTAUTH_SECRET` / `NEXTAUTH_URL` / `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`）はまだ Vercel に登録されていない。
- GitHub Actions のデプロイワークフローは `vercel pull` → `vercel deploy` を行うが、欠落した環境変数を検知する仕組みがないので、Vercel 側が空のままでもデプロイが成功してしまう。

## これからやるべきこと

1. **Vercel の環境変数を整備する**  
   - `docs/setup/vercel-environment-variables.md` を参照し、Production と Preview の両方に必須キーを登録する。  
   - `NEXTAUTH_SECRET` は十分な長さのランダム値を設定し、`NEXTAUTH_URL` は環境ごとのドメインを完全一致で入力する。
2. **ローカルの `.env.local` を修正する**  
   - `AUTH_SECRET` を `NEXTAUTH_SECRET` にリネームし、`NEXTAUTH_URL` など既存の値を確認する。  
   - 修正後にローカルで `pnpm dev` などを実行し、Google ログインが成功するか再検証する。
3. **CI で環境変数チェックを追加する（推奨）**  
   - `.github/workflows/deploy-vercel-reusable.yml` に `vercel env ls` の結果を検査するステップを追加し、必須キーが欠けていたらジョブを失敗させる。  
   - これにより、将来的にVercel側の設定が抜けた状態でデプロイされるリスクを減らす。
4. **必要に応じて GitHub Secrets を拡張する**  
   - Secrets をソース・オブ・トゥルースとするなら、`NEXTAUTH_SECRET` / `NEXTAUTH_URL`（環境ごとに分ける場合は `NEXTAUTH_URL_PROD` など）を追加し、同期ポリシーを定める。

## 補足メモ

- Vercel の環境変数は CLI で `vercel env add`／`vercel env rm` を使って管理できる。  
- `vercel env pull` を実行すると Vercel 側の値をローカルに同期できるが、取得した `.env.vercel` は `.gitignore` で無視されるため、必要なら各自で `.env.local` に転記する。
- 認証周りの要件は `.kiro/specs/secure-excel-unlock/requirements.md` および `.kiro/specs/cicd-deployment/requirements.md` で定義されている。今回の対応はこれらの要件を満たすための基盤整備にあたる。
