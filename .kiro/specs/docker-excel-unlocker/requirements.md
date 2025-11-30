# Docker Excel Unlocker - 要件定義書

## はじめに

本ドキュメントは、Docker コンテナで動作するシンプルな Excel パスワード解除ツールの要件を定義します。自宅 Windows PC 上の Docker コンテナで FastAPI アプリケーションを起動し、Tailscale VPN 経由で iPhone を含む全デバイスから Excel ファイルのパスワードを解除できるようにします。

## 用語集

- **Excel Unlocker**: パスワード付き Excel ファイルを解除するシステム
- **Tailscale**: ゼロコンフィグの VPN サービス。プライベートネットワークを構築
- **FastAPI**: Python の高速 Web フレームワーク
- **Docker**: コンテナ仮想化プラットフォーム
- **MVP**: Minimum Viable Product（実用最小限の製品）

## アーキテクチャ概要

本 MVP は以下の構成で動作します：

```
[外出先 iPhone/Android/PC]
    │
    │ Tailscale VPN 接続
    ↓
[Tailscale ネットワーク]
    │
    ↓
[自宅 Windows PC] ← Tailscale インストール済み・常時起動
    │
    │ Docker ポート公開 (0.0.0.0:3000)
    ↓
[Docker コンテナ: FastAPI + Jinja2 UI]
    │
    └→ ローカルファイル処理 (/tmp)
```

### 明示的な対象外（本 MVP では使用しない）

- AWS Lambda / API Gateway / S3
- Google OAuth / Google Drive 連携
- Vercel / Next.js
- 外部クラウドストレージ
- ユーザー認証機能

### 既存実装の破棄と新規作成

**重要:** 現リポジトリの `backend/`（AWS Lambda/S3 前提）および `frontend/`（Next.js/OAuth/Drive 前提）は**全て破棄**し、FastAPI + Jinja2 の単一 Docker コンテナとして**新規作成**する。既存コードの流用は行わない（クラウド依存が紛れ込むリスクを排除）。

## 要件

### 要件1: Excel パスワード解除機能

**ユーザーストーリー:** ユーザーとして、パスワード付き Excel ファイルを指定したパスワードで解除し、解除済みファイルをダウンロードしたい。そうすることで、パスワード保護されたファイルを編集・閲覧できるようになる。

#### 受入基準

1. WHEN ユーザーが Excel ファイル（.xlsx または .xls）を1つアップロードし、パスワードを入力して解除ボタンを押す THEN Excel Unlocker はファイルを解除して `downloadUrl` を含むJSONレスポンスを返す
2. WHEN ユーザーが複数のパスワード候補をカンマ区切りで入力する THEN Excel Unlocker は各パスワードを順番に試行し、最初に成功したパスワードで解除する
3. WHEN 入力されたすべてのパスワードで解除に失敗する THEN Excel Unlocker は「パスワードが正しくありません」というエラーメッセージを**この文言で**返す
4. WHEN 解除処理が完了する THEN Excel Unlocker は一時ファイルを即座に削除する
5. WHEN 同時リクエスト数が `MAX_WORKERS` を超える THEN Excel Unlocker は HTTP 429（Too Many Requests）を返し、クライアントにリトライを促す
6. WHEN アップロードされたファイルがパスワード保護されていない THEN Excel Unlocker は「パスワードが設定されていません」というエラーを**この文言で**返し、ダウンロードURLは提供しない
7. WHEN パスワード解除に成功する THEN Excel Unlocker は解除後のファイル名を `{元ファイル名}_解除.{拡張子}` に変更する（拡張子がない場合は `{元ファイル名}_解除`、複数ドットがある場合は最後の拡張子のみを保持する）

**並列度と負荷制御の関係:**
- サーバ側 `MAX_WORKERS` は CPU 数以下、デフォルト4
- クライアント並列は `CLIENT_CONCURRENCY` で指定、デフォルト3
- サーバが 429 を返した場合、クライアントは `retryAfter` に従ってリトライする

#### API 仕様

| エンドポイント | メソッド | 説明 |
|---------------|----------|------|
| `/` | GET | Web UI（Jinja2 テンプレート） |
| `/unlock` | POST | Excel 解除 API（1ファイル専用） |
| `/health` | GET | ヘルスチェック |
| `/download/{file_id}` | GET | 解除済みファイルダウンロード（MVP: ローカル/tmp から送信。将来: StorageService 実装に応じて GCS 署名 URL に差し替え可能） |

**HTTPステータスコード:**
| ステータス | 用途 |
|------------|------|
| 200 | 正常系（解除成功、ダウンロード成功、ヘルスチェック） |
| 400 | 入力エラー（拡張子違反、サイズ超過、パスワード不正、パスワード未設定ファイル） |
| 429 | 過負荷（同時リクエスト数超過） |
| 500 | 内部エラー（予期せぬ例外） |

**ダウンロードURLの有効期限:**
- `file_id` は短期有効（5分）
- ダウンロード済みまたは期限切れ後は `StorageService.delete` を呼び出してファイルを削除
- ローカル /tmp の肥大化を防止

**StorageService の適用箇所:**
- `/unlock` における save/load/delete と downloadUrl 生成はすべて StorageService を経由して行う
- MVP: `LocalStorageService`（/tmp）、将来: `GCSStorageService`

**POST /unlock リクエスト:**
- Content-Type: `multipart/form-data`
- フィールド: `file`（単一ファイル）、`passwords`（カンマ区切り文字列）

**POST /unlock レスポンス（成功時）:**
```json
{
  "fileName": "example.xlsx",
  "status": "success",
  "message": null,
  "downloadUrl": "/download/abc123"
}
```

**POST /unlock レスポンス（エラー時 - パスワード不正）:**
```json
{
  "fileName": "example.xlsx",
  "status": "error",
  "message": "パスワードが正しくありません",
  "downloadUrl": null
}
```

**POST /unlock レスポンス（エラー時 - パスワードなしファイル）:**
```json
{
  "fileName": "example.xlsx",
  "status": "error",
  "message": "パスワードが設定されていません",
  "downloadUrl": null
}
```

**POST /unlock レスポンス（過負荷時 - HTTP 429）:**
```json
{
  "error": "Too Many Requests",
  "message": "サーバーが混雑しています。しばらく待ってから再試行してください。",
  "retryAfter": 5
}
```

### 要件2: Web ユーザーインターフェース

**ユーザーストーリー:** ユーザーとして、シンプルで直感的な Web 画面から Excel 解除機能を利用したい。そうすることで、技術的な知識がなくても簡単に操作できる。

#### 受入基準

1. WHEN ユーザーがブラウザでアクセスする THEN Excel Unlocker はファイル選択（複数可）、パスワード入力、解除ボタンを含む単一ページのシンプルな画面を表示する
2. WHEN ユーザーがファイルをドラッグ＆ドロップまたはタップして選択する THEN Excel Unlocker はファイルを受け付けてファイル名を表示する
3. WHEN ユーザーが複数ファイルを選択して解除ボタンを押す THEN Excel Unlocker は JavaScript で並列リクエスト（最大3〜5並列）を送信し、各ファイルの進捗を個別に表示する
4. WHEN 解除処理中である THEN Excel Unlocker は各ファイルの処理状態（待機中/処理中/完了/エラー）を表示する
5. WHEN 解除が成功する THEN Excel Unlocker はダウンロードボタンを表示し、ユーザーがクリック/タップすると解除済みファイルをダウンロードできる
6. WHEN API が HTTP 429 を返す THEN Excel Unlocker は自動的に `retryAfter` 秒後にリトライする（最大3回まで）

**UI 要件の補足:**
- 認証画面は不要（Tailscale で保護）
- Google Drive 保存機能は不要（ダウンロードで代替）
- ログイン/ログアウト導線は不要
- クライアント側並列数: `CLIENT_CONCURRENCY` で指定（デフォルト3）
- 429 受信時のリトライ: `retryAfter` 秒後に再送、最大リトライ回数は3回（無限リトライ防止）

### 要件3: マルチデバイス対応

**ユーザーストーリー:** ユーザーとして、iPhone、Android、PC、Mac のいずれのデバイスからも Tailscale VPN 経由で同じ操作で Excel 解除を行いたい。そうすることで、外出先でも手元にあるデバイスで即座に作業できる。

#### 受入基準

1. WHEN ユーザーが iPhone Safari から Tailscale 経由でアクセスする THEN Excel Unlocker はタッチ操作に最適化されたレスポンシブ画面を表示する
2. WHEN ユーザーが iPhone でファイルを選択する THEN Excel Unlocker は「ファイル」アプリや iCloud Drive からの選択を受け付ける
3. WHEN ユーザーが PC/Mac ブラウザから Tailscale 経由でアクセスする THEN Excel Unlocker はデスクトップ向けのレイアウトで表示する
4. WHEN 解除済みファイルをダウンロードする THEN Excel Unlocker は各デバイスの標準的なダウンロード動作でファイルを保存できる

### 要件4: Docker コンテナ動作

**ユーザーストーリー:** 運用者として、Docker コンテナとしてシステムを起動・停止したい。そうすることで、環境構築が簡単で、Windows PC 上で安定して動作する。

#### 受入基準

1. WHEN 運用者が `docker-compose up -d` を実行する THEN Excel Unlocker は起動し、ポート 3000 でリクエストを受け付ける
2. WHEN 運用者が `docker-compose down` を実行する THEN Excel Unlocker は正常に停止し、一時ファイルを削除する
3. WHEN Docker コンテナが起動する THEN Excel Unlocker は環境変数から設定を読み込み、デフォルト値にフォールバックする
4. WHEN `/health` エンドポイントにアクセスする THEN Excel Unlocker は `200 OK` と `{"status": "ok"}` を返す

**Docker 構成の補足:**
- ポート公開: `0.0.0.0:3000:3000`（Tailscale 経由アクセスのため全インターフェース）
- ログ出力: 標準出力のみ（`docker logs` で確認可能）
- ファイルローテーション: なし（シンプル運用）
- イメージ名: `excel-unlocker`
- コンテナ名: `excel-unlocker`
- ボリュームマウント: **デバッグ時のみ** `./data/tmp:/tmp/excel-unlocker`。通常運用ではマウントなし（即削除を優先）

**Dockerfile 環境変数:**
- `ENV TMP_DIR=/tmp/excel-unlocker`
- `ENV PORT=3000`
- `ENV HOST=0.0.0.0`
- `ENV MAX_WORKERS=4`（設定表と統一）
- Windows ホストは compose で `TMP_DIR=C:\tmp\excel-unlocker` に上書き

**新規作成ファイル:**
- `Dockerfile` - Python 3.11 + FastAPI ベース
- `docker-compose.yml` - 上記構成を定義
- 現リポジトリには Dockerfile/docker-compose.yml は存在しないため、新規作成する

### 要件5: 設定の一元管理

**ユーザーストーリー:** 開発者として、アプリケーションの設定値を一箇所で管理したい。そうすることで、設定変更時の影響範囲を把握しやすく、保守性が向上する。

#### 受入基準

1. WHEN 開発者が設定を変更する THEN Excel Unlocker は `config.py` の1ファイルのみを修正すれば設定が反映される
2. WHEN 環境変数が設定されている THEN Excel Unlocker は環境変数の値を優先して使用する
3. WHEN 環境変数が設定されていない THEN Excel Unlocker はデフォルト値を使用する
4. WHEN 設定値を参照する THEN Excel Unlocker はハードコードされた値ではなく設定モジュールから取得する

**管理対象の設定項目:**

| 設定項目 | 環境変数 | デフォルト値 | 説明 |
|----------|----------|--------------|------|
| ポート | `PORT` | `3000` | サーバー待ち受けポート |
| ホスト | `HOST` | `0.0.0.0` | サーバー待ち受けアドレス |
| 最大ファイルサイズ | `MAX_FILE_SIZE_MB` | `50` | アップロード上限（MB） |
| 許可拡張子 | `ALLOWED_EXTENSIONS` | `.xlsx,.xls` | 許可するファイル拡張子 |
| 一時ディレクトリ | `TMP_DIR` | `C:\tmp\excel-unlocker`（Windows）<br>`/tmp/excel-unlocker`（Linux/Cloud Run） | 一時ファイル保存先（OS 別） |
| 最大同時処理数 | `MAX_WORKERS` | `4` | 同時処理リクエスト数（CPU数以下推奨） |
| クライアント並列数 | `CLIENT_CONCURRENCY` | `3` | フロントエンドの同時リクエスト数 |

**TMP_DIR の OS 別デフォルト:**
- Windows（MVP 環境）: `C:\tmp\excel-unlocker`
- Linux / Cloud Run: `/tmp/excel-unlocker`
- 環境変数で上書き可能

### 要件6: セキュリティとファイル管理

**ユーザーストーリー:** ユーザーとして、アップロードしたファイルが安全に処理され、処理後に削除されることを期待する。そうすることで、機密情報の漏洩リスクを最小化できる。

#### 受入基準

1. WHEN ファイルがアップロードされる THEN Excel Unlocker はローカル一時ディレクトリ（`TMP_DIR`）に保存し、処理完了後に即座に削除する
2. WHEN Excel 以外のファイル形式がアップロードされる THEN Excel Unlocker は「サポートされていないファイル形式です」というエラーを**この文言で**返す
3. WHEN ファイルサイズが上限（`MAX_FILE_SIZE_MB`）を超える THEN Excel Unlocker は「ファイルサイズが大きすぎます」というエラーを**この文言で**返す
4. WHEN アクセス制御が必要な場合 THEN Tailscale ACL および Windows ファイアウォールで制御する（アプリ側での VPN 判定は行わない）

**セキュリティ方針:**
- アクセス制御は Tailscale ACL / ファイアウォールの責務とする
- アプリ側は将来的に IP allowlist やヘッダーチェックのミドルウェアを差し込める構造とする
- S3 署名付き URL や外部ストレージは使用しない

## 非機能要件

### パフォーマンス要件

| 項目 | 要件 | 計測方法 |
|------|------|----------|
| 処理時間 | 20MB 以下のファイルを 10 秒以内に処理 | スモークテストスクリプトで計測 |
| 最大ファイルサイズ | 50MB | 設定値で制御 |
| 同時処理数 | 4 リクエスト（MAX_WORKERS） | 並列リクエストテストで確認 |
| 過負荷時応答 | HTTP 429 + retryAfter | 超過時のレスポンス確認 |

**パフォーマンス計測:**
- `scripts/perf-smoke.sh` として 20MB ダミーファイルを N=4 並列で POST するスモークスクリプトを用意する
- 起動後に手動実行し、10 秒以内を確認する
- Cloud Run 移行時も同じ計測スクリプトを再利用する
- **合否基準**: 20MB × N=4 並列で 10 秒以内、HTTP 200 連続成功。429/500 など 200 以外が 1 件でもあれば不合格

**msoffcrypto-tool の特性:**
- CPU バウンド処理のため、FastAPI の async でも実質スレッド/プロセスで処理
- ThreadPoolExecutor のワーカー数は MIN(CPU数, MAX_WORKERS) 程度に設定

### 運用要件

| 項目 | 要件 |
|------|------|
| 起動方法 | `docker-compose up -d` |
| 停止方法 | `docker-compose down` |
| ログ出力 | 標準出力のみ（`docker logs excel-unlocker` で確認） |
| ヘルスチェック | `GET /health` → `200 OK` + `{"status": "ok"}` |
| 再起動ポリシー | `restart: unless-stopped` |

### コード品質要件

| 項目 | 要件 |
|------|------|
| ハードコード禁止 | 設定値は `config.py` 経由で取得 |
| 関数の責務 | 1関数1責務、一文で説明できる粒度 |
| エラーハンドリング | 適切な例外処理とユーザー向けメッセージ |
| 将来の拡張性 | ミドルウェア追加で認証等を差し込める構造 |

## 将来拡張性

| 項目 | 対応方針 |
|------|----------|
| Cloud Run 移行 | 同一 Dockerfile をベースに、`PORT`/`HOST=0.0.0.0` 環境変数対応。MVP ではクラウド資源は使用しない。タイムアウトは Cloud Run の 15 分上限を意識。1ファイル1リクエスト設計により、Cloud Run の自動スケールを最大限活用可能 |
| Cloud Storage 連携 | `StorageService` 抽象（`save`/`load`/`delete`/`generate_download_url`）を定義。MVP は `LocalStorageService`（/tmp）、将来は `GCSStorageService` に差し替え。レスポンスの `downloadUrl` を GCS 署名付き URL に変更するだけで移行可能。**適用箇所**: `/unlock` での save/load/delete および downloadUrl 生成は全て StorageService 経由で行う |
| 認証追加 | FastAPI ミドルウェアで Google OAuth 等を差し込める構造。MVP では実装しない |
| スケーリング | クライアント側並列 + API直列設計により、Cloud Run インスタンス数に応じて自動スケール。クライアント並列数（3〜5）とサーバー MAX_WORKERS（CPU数）を調整可能 |

## CI/CD 方針

| 項目 | 方針 |
|------|------|
| 既存ワークフロー | `.github/workflows/` 配下の AWS/Vercel/Next.js 関連ワークフローを**全削除**または `archive/` へ移動する |
| MVP での CI/CD | 一旦無効化。手動で `docker-compose up` による運用 |
| 将来の CI/CD | Cloud Run 移行時に再設計する |

**削除対象ワークフロー（.github/workflows/）:**
- `build-frontend.yml` - Next.js ビルド
- `deploy-aws.yml` - AWS デプロイ
- `deploy-backend.yml` - Lambda バックエンドデプロイ
- `deploy-frontend.yml` - Vercel フロントエンドデプロイ
- `deploy-full-stack.yml` - フルスタックデプロイ
- `deploy-platform.yml` - プラットフォームデプロイ
- `deploy-vercel-reusable.yml` - Vercel 再利用ワークフロー
- `e2e-test-frontend.yml` - E2E テスト
- `validate-frontend.yml` - フロントエンド検証
- `common-error-handler.yml` - エラーハンドラー
- `manual-environment-check.yml` - 環境チェック

## 技術的制約

### Excel パスワード解除ライブラリ

| 項目 | 指定 |
|------|------|
| 使用ライブラリ | **msoffcrypto-tool**（必須） |
| 理由 | 経験上、他のライブラリでは解除に失敗するケースが多い |
| 代替ライブラリ | 使用しない（openpyxl 等では解除不可） |
| 解除後の保存形式 | XLSX/XLS そのまま保存（形式変換なし） |

### 既存コードの扱い

| 項目 | 方針 |
|------|------|
| 既存コード | **全削除**して新規作成 |
| 理由 | AWS Lambda 前提のコードを FastAPI に移植するより新規作成の方が効率的 |
| 残すもの | `.kiro/`（スペック）、`.gitignore`、`README.md`（書き換え） |

**削除対象:**
- `backend/` - AWS Lambda 用 Python コード
- `frontend/` - Next.js / Vercel 用コード
- `.github/workflows/` - AWS / Vercel デプロイ用ワークフロー
- `template.yaml` - AWS SAM テンプレート
- `samconfig.toml` - SAM 設定
- `docs/` - 旧ドキュメント
- `scripts/` - 旧セットアップスクリプト
- `tests/` - 旧テスト
- その他 AWS / Vercel 関連ファイル

## 対象外範囲

以下の機能は本 MVP の対象外とします：

1. **パスワード解析・総当たり機能** - セキュリティ上の理由により実装しない
2. **ユーザー認証機能** - Tailscale VPN で保護するため MVP では不要
3. **ファイルの長期保存** - 処理完了後は即時削除
4. **Google Drive 連携** - ダウンロード機能で代替
5. **API内での複数ファイル一括処理** - クライアント側並列で対応（Cloud Run スケーリングと相性が良い）
6. **AWS Lambda / S3 / API Gateway** - Docker + ローカルファイル処理で代替
7. **Vercel / Next.js** - FastAPI + Jinja2 テンプレートで代替
8. **msoffcrypto-tool 以外の解除ライブラリ** - 動作実績がないため使用しない

## 成功指標

| 指標 | 目標 |
|------|------|
| 動作確認 | 外出先の iPhone Safari から Tailscale 経由で Excel 解除が完了できる |
| 起動時間 | `docker-compose up` から利用可能まで 30 秒以内 |
| 処理成功率 | 正しいパスワード入力時の成功率 100% |
| レスポンシブ対応 | iPhone / Android / PC / Mac で正常に表示・操作できる |
