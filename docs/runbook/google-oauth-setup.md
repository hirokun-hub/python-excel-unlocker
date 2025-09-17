# Google OAuth 設定ランブック（Auth.js / NextAuth）

対象読者: 初めてGoogle Cloud Consoleを触る人。どの画面で何を入力するかを手順化します。UIは随時更新されるため、必要に応じて公式ドキュメントで最新情報を確認してください（「参考リンク」参照）。

---

## ゴール

- Google OAuth 同意画面の設定を完了する
- Webアプリ用OAuthクライアントを作成する
- 本番/プレビューの「承認済みのリダイレクトURI」「承認済みのJavaScript生成元」を正しく登録する
- 取得した `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` をVercel環境変数とGitHub Secretsに反映する

---

## 用語とダミー例

- 本番フロントURL: `https://app.example.com`
- プレビューURL: `https://your-project-git-branch-user.vercel.app`
- リダイレクトURI: `https://<フロントURL>/api/auth/callback/google`
  - 例（本番）: `https://app.example.com/api/auth/callback/google`
  - 例（プレビューワイルドカード）: `https://*.vercel.app/api/auth/callback/google`

---

## 1. プロジェクト選択

1) ブラウザで `https://console.cloud.google.com/` にアクセス
2) 画面上部のプロジェクトセレクタで「本番用」のプロジェクトを選択（未作成なら作成）

---

## 2. OAuth 同意画面の設定

1) 左上ハンバーガーメニュー → 「APIとサービス」→「OAuth 同意画面」
2) ユーザーの種類: 通常は「外部」を選択（社内限定なら「内部」でも可）
3) アプリ情報を入力
   - アプリ名: `Secure Excel Unlock`
   - サポートメール: 管理用メール（例: `admin@example.com`）
   - アプリロゴ: 任意
   - アプリドメイン: `app.example.com`
4) スコープ: 基本は `email` / `profile` / `openid`
   - 実装にDriveスコープがある場合は `.../drive.file` など必要範囲のみ選択
5) テストユーザー: 本番公開前はログイン可能ユーザーを追加（例: `hironomac2025@gmail.com`）
6) 保存

注意:
- 本番公開（検証）を行う場合、Googleの審査が必要になることがあります

---

## 3. OAuth クライアントIDの作成（Web アプリ）

1) 左メニュー「認証情報」→ 上部「+ 認証情報を作成」→「OAuth クライアントID」
2) アプリケーションの種類: 「ウェブアプリ」
3) 名前: `secure-excel-unlock-web`
4) 「承認済みの JavaScript 生成元」を追加
   - 本番: `https://app.example.com`
   - プレビュー: `https://*.vercel.app`
5) 「承認済みのリダイレクト URI」を追加
   - 本番: `https://app.example.com/api/auth/callback/google`
   - プレビュー: `https://*.vercel.app/api/auth/callback/google`
6) 作成 → `クライアントID` と `クライアントシークレット` を控える

ダミー例（コピー禁止）:
```
GOOGLE_CLIENT_ID=1234567890-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc_defg-hijklmnop
```

---

## 4. 値の反映先（Vercel と GitHub Secrets）

Vercel（フロント実行時に参照）:
- 場所: Vercel プロジェクト → Settings → Environment Variables
- 追加キー:
  - `GOOGLE_CLIENT_ID`（Production/Preview 両方）
  - `GOOGLE_CLIENT_SECRET`（Production/Preview 両方）
  - `NEXTAUTH_URL`（本番/プレビューで異なる）
  - `NEXTAUTH_SECRET`（十分に長いランダム値）

GitHub Secrets（CIからのデプロイで使用）:
- 場所: GitHub → 対象リポジトリ → Settings → Secrets and variables → Actions
- 追加キー例:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `NEXTAUTH_SECRET`

---

## 5. NextAuth（Auth.js）側の整合

アプリの `frontend/src/auth.ts`（例）では、`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`NEXTAUTH_SECRET` を利用します。環境変数が正しくセットされていないとログインが失敗します。

確認ポイント:
- `NEXTAUTH_URL` は本番/プレビューで正しいURLか
- `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` が一致しているか
- スコープの差異がないか（Driveアクセスを要求しているなら同意画面に反映されているか）

---

## 6. スモークテスト

1) VercelのプレビューURLを開く
2) 画面の「ログイン」→ Googleを選択
3) Googleの同意画面表示 → 許可
4) 画面右上などにログイン後のメールアドレスが表示されるかを確認

失敗例と対策:
- `redirect_uri_mismatch`
  - Googleの「承認済みのリダイレクトURI」にそのURLが含まれていない
- `origin_mismatch`
  - Googleの「承認済みの JavaScript 生成元」にそのオリジンが含まれていない

---

## 参考リンク（最新情報を確認）

- Google OAuth 同意画面: `https://console.cloud.google.com/apis/credentials/consent`
- OAuth クライアントID: `https://console.cloud.google.com/apis/credentials`
- Auth.js (NextAuth) Google Provider: `https://authjs.dev/reference/core/providers/google`


