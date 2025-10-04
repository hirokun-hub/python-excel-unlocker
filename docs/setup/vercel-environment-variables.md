# Vercel 環境変数設定ガイド

このドキュメントでは、Secure Excel Unlock フロントエンドが Vercel 上で正しく動作するために必要な環境変数を、Vercel の Web ダッシュボードおよび Vercel CLI から登録・確認する手順をまとめます。

## 前提条件

- Vercel アカウントにログイン済みであること。
- 対象プロジェクトが既に Vercel 上に存在していること。
- CLI 操作を行う場合は、開発マシンに [Vercel CLI](https://vercel.com/docs/cli) がインストール済みで、`vercel login` を完了していること。
- リポジトリ側では `frontend/vercel.json` のエイリアスで下記の環境変数を参照しています。

## 必須環境変数

| 変数名 | 用途 | 補足 |
| --- | --- | --- |
| `NEXTAUTH_SECRET` | NextAuth.js の暗号化キー | 本番・プレビュー・ローカルで同一値を使用する運用が推奨。十分な長さの乱数を設定すること。 |
| `NEXTAUTH_URL` | NextAuth.js の基底 URL | 環境ごとに正確なドメインを設定（例: `https://excel-unlocker.vercel.app` / `https://excel-unlocker-staging.vercel.app`）。末尾スラッシュなし。 |
| `GOOGLE_CLIENT_ID` | Google OAuth クライアント ID | Google Cloud Console で発行した Web アプリ用クライアントの値。 |
| `GOOGLE_CLIENT_SECRET` | Google OAuth クライアント シークレット | 上記クライアントに紐づくシークレット。 |
| `NEXT_PUBLIC_API_URL` | フロントエンドが呼び出す API エンドポイント | 既定では API Gateway の URL を指定。Preview ではステージングAPIなど環境に応じて設定。 |
| `NEXT_PUBLIC_USE_MOCK_API` | モック API 利用フラグ | Preview 環境で `true` に設定されている。必要に応じて Production でも管理。 |

> **補足:** `frontend/vercel.json` では `@nextauth_secret` のようなエイリアスを使用しています。Vercel 側で同名の Environment Variable を作成するとビルド・関数実行時に値が展開されます。

## Web ダッシュボードからの登録手順

1. [Vercel Dashboard](https://vercel.com/dashboard) にアクセスし、対象プロジェクトを開きます。
2. プロジェクトメニューの **Settings** タブに移動し、左メニューから **Environment Variables** を選択します。
3. **Production** セクションで「Add」ボタンを押し、上表の各変数を追加します。
   - `NEXTAUTH_URL` は本番ドメイン（例: `https://excel-unlocker.vercel.app`）を入力。
   - `NEXTAUTH_SECRET` は十分に長いランダム値を設定（例: `openssl rand -base64 32` などで生成）。
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` には Google Cloud で発行した値をコピーします。
   - `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_USE_MOCK_API` は本番用の API エンドポイントとフラグを設定。
4. 同様の手順で **Preview** セクションにも必要な値を登録します。
   - `NEXTAUTH_URL` はプレビュー／ステージングのドメイン（例: `https://excel-unlocker-staging.vercel.app`）。
   - Google のクレデンシャルは基本的に Production と同じ値を使用します。
   - プレビュー用 API エンドポイントやモックフラグを環境に合わせて設定します。
5. （必要に応じて）**Development** セクションにもローカル用の値を登録できますが、ローカル開発では `.env.local` を利用するのが一般的です。
6. すべて追加後、環境変数が正しく表示されていることを確認し、必要なら再デプロイを行います。

## CLI からの登録・確認手順

CLI では `vercel env` コマンドを使用して環境変数を管理します。

### プロジェクトのリンク

```bash
cd frontend
vercel link
```

プロンプトに従ってスコープ・既存プロジェクトを選択すると、`.vercel/project.json` が生成され以後のコマンドで対象プロジェクトが自動選択されます。

### 環境変数の追加

```bash
# Production 環境に NEXTAUTH_SECRET を登録する例
vercel env add NEXTAUTH_SECRET production

# Preview 環境に NEXTAUTH_URL を登録する例
vercel env add NEXTAUTH_URL preview
```

コマンド実行後、CLI から値の入力を求められます。Google クライアント情報も同様に `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` を追加してください。

> **Tips:** 同じ値を複数環境に投入する場合は `vercel env add <KEY> production < <file>` のようにファイルリダイレクトを使うと入力ミスを防げます。

### 環境変数の確認

```bash
# すべての環境を一覧表示
vercel env ls

# 環境を指定して確認（Production）
vercel env ls production

# プレビューのみ確認
vercel env ls preview
```

### ローカルへの同期

```bash
# Vercel 上の値をローカルファイルに同期
vercel env pull .env.vercel
```

生成された `.env.vercel` は `.gitignore` によりリポジトリへコミットされません。ローカル検証に利用してください。

### 値の更新・削除

```bash
# 値の更新（再追加）
vercel env add NEXTAUTH_SECRET production

# 値の削除
vercel env rm NEXT_PUBLIC_USE_MOCK_API preview
```

既存値を更新する場合は一度 `vercel env rm` で削除してから `vercel env add` し直すと明確です。

## 運用上のベストプラクティス

- GitHub Actions などの CI からデプロイする際は、`vercel env ls` の結果を検証し、必須キーが欠けている場合はジョブを失敗させて早期に検知します。
- Google OAuth のクレデンシャルと `NEXTAUTH_SECRET` は Production/Preview で整合を取るように管理し、更新時は両環境を同時に更新します。
- Secrets の値は関係者のみに共有し、Vercel Dashboard のアクセス権限も制限します。
- ローカル開発では `.env.local` を利用し、本番値との混在を避けます。必要なら `vercel env pull` で値を確認し、`NEXTAUTH_SECRET` などを `.env.local` に複製してください。

これらの手順に従って環境変数を設定すると、Auth.js および Google Drive 連携が正常に動作するようになります。
