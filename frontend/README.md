# Secure Excel Unlocker – Frontend

このリポジトリは **Next.js** 製フロントエンドです。**NextAuth** で **Google ログイン**を行い、解除済みファイルの保存先として \*\*Google Drive API（`drive.file` スコープ）\*\*を利用します。**モックAPI**での画面確認にも対応しています。

---

## 要件

* Node.js v18.17+ または v20+ 推奨
* パッケージマネージャー：**pnpm**（推奨）または **npm**
* Google OAuth クライアント（Client ID / Client Secret 発行済み）

---

## セットアップ

1. 依存関係のインストール

   ```bash
   cd frontend
   pnpm i        # または npm i
   ```

2. 環境変数ファイルの作成（**コミット禁止**）

   * `frontend/.env.local` を新規作成し、以下を設定（値は実環境に合わせて置換）

     ```
     GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
     GOOGLE_CLIENT_SECRET=yyyyyyyy
     NEXTAUTH_URL=http://localhost:3001
     AUTH_SECRET=（例：node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"）
     USE_MOCK_API=true
     # NEXT_PUBLIC_API_URL=（実APIを使うときのみ例：http://127.0.0.1:3002）
     ```
   * `.env.local` は `.gitignore` 済み（リポジトリに含めないでください）。

---

## 開発サーバーの起動

* 既定ポートは **3001** です（`package.json` の `dev` スクリプト）。

  ```bash
  pnpm dev           # http://localhost:3001
  ```
* もし **3000** で起動したい場合：

  ```bash
  pnpm run dev:3000  # http://localhost:3000
  ```
* **Google 側のリダイレクトURI**は起動ポートに合わせて追加してください

  * `http://localhost:3001/api/auth/callback/google`
  * または `http://localhost:3000/api/auth/callback/google`

本番ビルド／起動:

```bash
pnpm build
pnpm start
```

---

## ログイン動作確認（手順）

1. ブラウザで `http://localhost:3001`（または 3000）を開く
2. 「Googleでログイン」→ 同意画面 → 画面右上にログイン状態が表示されればOK

**トラブル時のチェック**

* Google Auth Platform → **対象** → **テストユーザー**に自分のアカウントが入っているか
* **リダイレクトURIが完全一致**しているか（1文字違いも不可）
* `.env.local` の `NEXTAUTH_URL` が現在の起動URLと一致しているか

---

## API 接続（モック／実API）

* **モックで動かす（推奨：初回確認）**
  `.env.local` に `USE_MOCK_API=true` を設定。バックエンド未整備でも画面遷移を確認できます。
* **実APIに接続**
  バックエンドを別ポート（例：3002）で起動し、
  `.env.local` に `NEXT_PUBLIC_API_URL=http://127.0.0.1:3002` を設定（**ベースURLのみ**推奨）。
  フロント側の呼び出しは `${API_BASE}/unlock`・`${API_BASE}/presigned-urls`・`${API_BASE}/status` 形式にします。

> もし既存コードが `NEXT_PUBLIC_API_URL` に `/unlock` を含む設計なら、将来の拡張のため **ベースURL方式**にリファクタしてください。

---

## Google 設定メモ

* スコープ

  * `openid` / `https://www.googleapis.com/auth/userinfo.email` / `https://www.googleapis.com/auth/userinfo.profile`
  * `https://www.googleapis.com/auth/drive.file`（当アプリで扱うファイルのみ／最小権限）
* リダイレクトURI（ローカル）

  * `http://localhost:3001/api/auth/callback/google`（または 3000）
* スコープの「非機密／機密／制限付き」の分類は **自動**（手動移動はできません）

---

## 便利スクリプト

* `pnpm dev`：開発起動（**3001**）
* `pnpm run dev:3000`：開発起動（3000）
* `pnpm build`：本番ビルド
* `pnpm start`：本番起動
* `pnpm lint`：Lint 実行
* `pnpm debug:pack`：**デバッグ用Zip作成**（下記）

---

## トラブルシューティング：デバッグZip（`debug:pack`）

ビルド失敗や import エラー時に、必要ログだけを **zip** にまとめます（**秘密ファイルは含みません**）。

1. 初回のみ実行権限を付与

   ```bash
   chmod +x scripts/fe-debug.sh
   ```
2. 収集

   ```bash
   pnpm debug:pack
   ```
   
### デバッグパックの作成
リポジトリ直下または `frontend/` で以下を実行してください:

```bash
npm run debug:pack   # npm を使う場合
# もしくは
pnpm run debug:pack  # pnpm を使う場合（pnpm が入っているとき）
```
※ `npm debug:pack` や `pnpm debug:pack` ではなく、必ず `run` を付けてください。
3. 出力例
   `Created archive: /path/to/frontend/fe-debug-YYYYMMDD-HHMMSS.zip`
   → このZipを共有すれば再現性の高い調査が可能です。

**オプション**

* ビルド実行をスキップ：
  `NO_BUILD=1 pnpm debug:pack`
* Nextの匿名テレメトリを止める：
  `NEXT_TELEMETRY_DISABLED=1 pnpm dev`

---

## よくあるエラーと対処

* **`Cannot find module '@/lib/utils'`**
  `src/lib/utils.ts` が無い／場所ズレ／`tsconfig.json` のパス設定ズレが原因。
  対処例：

  ```ts
  // src/lib/utils.ts
  import { type ClassValue } from "clsx";
  import { clsx } from "clsx";
  import { twMerge } from "tailwind-merge";
  export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
  }
  ```

  `tsconfig.json` の `compilerOptions.paths` は `"@/*": ["./src/*"]` を推奨。

---

## デプロイ（メモ）

* **Vercel** に以下を設定（Preview 環境）

  * `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `AUTH_SECRET` / `NEXTAUTH_URL` / `USE_MOCK_API`
* 本番ドメイン決定後、Google 側の **承認済みリダイレクトURI** に
  `https://{your-domain}/api/auth/callback/google` を**追記**してください。

---

## セキュリティ／注意

* `.env.local`、認証JSON、秘密鍵などの **秘密情報はリポジトリに含めない**でください。
* `NEXT_PUBLIC_` で始まる環境変数は **クライアントに公開**されます。**秘密は入れない**でください。
* デバッグZipは `.gitignore` 済み（`fe-debug-*.zip` / `fe-debug-*/`）。`git add` しなければ履歴に残りません。
