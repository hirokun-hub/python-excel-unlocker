# Docker Excel Unlocker

Docker コンテナで動作するシンプルな Excel パスワード解除ツールです。自宅 Windows PC 上の Docker コンテナで FastAPI アプリケーションを起動し、Tailscale VPN 経由で iPhone を含む全デバイスから Excel ファイルのパスワードを解除できます。

## 概要

- **バックエンド**: FastAPI + Jinja2（単一 Docker コンテナ）
- **処理エンジン**: msoffcrypto-tool による Excel パスワード解除
- **アクセス制御**: Tailscale VPN によるプライベートネットワーク保護
- **対応デバイス**: iPhone / Android / PC / Mac（レスポンシブ対応）

## 主要機能

- 🔐 **パスワード解除**: 第1パスワード → 第2パスワードの順で自動試行
- 📁 **複数ファイル対応**: クライアント側並列処理で複数ファイルを同時処理
- 📱 **マルチデバイス対応**: タッチ操作に最適化されたレスポンシブ UI
- 🚀 **シンプル運用**: `docker-compose up -d` で即起動

## クイックスタート

### 前提条件

- Docker / Docker Compose がインストール済み
- Tailscale VPN が設定済み（外部アクセス時）

### 起動方法

```bash
# コンテナを起動（バックグラウンド）
docker-compose up -d

# ログを確認
docker logs excel-unlocker

# コンテナを停止
docker-compose down
```

### アクセス方法

起動後、以下の URL でアクセスできます：

- **ローカル**: http://localhost:3000
- **Tailscale 経由**: http://<Tailscale IP>:3000

## 使用方法

1. ブラウザで Web UI にアクセス
2. Excel ファイル（.xlsx / .xls）を選択またはドラッグ＆ドロップ
3. 第1パスワード（必須）を入力
4. 必要に応じて第2パスワード（任意）を入力
5. 「解除」ボタンをクリック
6. 解除成功後、ダウンロードボタンからファイルを取得

### 解除後のファイル名

解除されたファイルは `{元ファイル名}_解除.{拡張子}` の形式で保存されます。

例: `report.xlsx` → `report_解除.xlsx`

## 設定項目一覧

環境変数で以下の設定をカスタマイズできます：

| 設定項目 | 環境変数 | デフォルト値 | 説明 |
|----------|----------|--------------|------|
| ポート | `PORT` | `3000` | サーバー待ち受けポート |
| ホスト | `HOST` | `0.0.0.0` | サーバー待ち受けアドレス |
| 最大ファイルサイズ | `MAX_FILE_SIZE_MB` | `50` | アップロード上限（MB） |
| 許可拡張子 | `ALLOWED_EXTENSIONS` | `.xlsx,.xls` | 許可するファイル拡張子 |
| 一時ディレクトリ | `TMP_DIR` | `/tmp/excel-unlocker` | 一時ファイル保存先 |
| 最大同時処理数 | `MAX_WORKERS` | `4` | 同時処理リクエスト数 |
| クライアント並列数 | `CLIENT_CONCURRENCY` | `3` | フロントエンドの同時リクエスト数 |
| ダウンロード有効期限 | `DOWNLOAD_EXPIRY_SECONDS` | `300` | ダウンロード URL の有効期限（秒） |

### 設定例（docker-compose.yml）

```yaml
services:
  excel-unlocker:
    environment:
      - PORT=3000
      - MAX_FILE_SIZE_MB=100
      - MAX_WORKERS=8
```

## API エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|----------|------|
| `/` | GET | Web UI（Jinja2 テンプレート） |
| `/unlock` | POST | Excel 解除 API |
| `/download/{file_id}` | GET | 解除済みファイルダウンロード |
| `/health` | GET | ヘルスチェック |

### ヘルスチェック

```bash
curl http://localhost:3000/health
# {"status": "ok"}
```

## プロジェクト構成

```
excel-unlocker/
├── app/
│   ├── main.py              # FastAPI エントリポイント
│   ├── config.py            # 設定一元管理
│   ├── routers/             # API ルーター
│   ├── services/            # ビジネスロジック
│   ├── models/              # Pydantic スキーマ
│   └── templates/           # Jinja2 テンプレート
├── static/                  # 静的ファイル（CSS/JS）
├── tests/                   # テストコード
├── scripts/                 # ユーティリティスクリプト
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 開発

### ローカル開発環境

```bash
# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 開発サーバーを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
```

### テスト実行

```bash
# ユニットテスト
pytest tests/ -v

# プロパティベーステスト
pytest tests/test_unlock_properties.py -v

# カバレッジ付き
pytest tests/ --cov=app --cov-report=html
```

### 配布パッケージの作成

社内配布向けに Docker イメージと起動スクリプトを同梱した ZIP を生成できます。

```bash
# 配布パッケージを作成
./scripts/create-distribution.sh

# 出力: excel-unlocker.zip
# 展開後の構成例:
# distribution/
#   excel-unlocker/
#     images/app.tar        # docker save 出力
#     docker-compose.yml    # 配布用 compose
#     README.txt            # 利用手順
#     setup.command/.bat    # イメージ読み込み
#     start.command/.bat    # 起動
#     server.env (任意)     # .env があれば同梱
```

### パフォーマンステスト

```bash
# スモークテスト（20MB × 4並列）
./scripts/perf-smoke.sh
```

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker logs excel-unlocker

# コンテナの状態を確認
docker ps -a
```

### ファイルが解除できない

- パスワードが正しいか確認してください
- ファイル形式が `.xlsx` または `.xls` であることを確認してください
- ファイルサイズが上限（デフォルト 50MB）以下であることを確認してください

### 429 Too Many Requests エラー

サーバーが混雑しています。しばらく待ってから再試行してください。クライアントは自動的にリトライします（最大3回）。

## ライセンス

MIT License

## 関連ドキュメント

- [要件定義書](.kiro/specs/docker-excel-unlocker/requirements.md)
- [設計書](.kiro/specs/docker-excel-unlocker/design.md)
- [実装計画](.kiro/specs/docker-excel-unlocker/tasks.md)
