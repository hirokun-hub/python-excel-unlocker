# Implementation Plan

## 既存コードの削除と環境準備

- [ ] 1. 既存コードの削除とプロジェクト初期化
  - [ ] 1.1 既存ディレクトリの削除
    - `backend/`, `frontend/`, `.github/workflows/`, `docs/`, `scripts/`, `tests/` を削除
    - `template.yaml`, `samconfig.toml` を削除
    - `.kiro/`, `.gitignore`, `README.md` は保持
    - _Requirements: 既存コードの扱い_
  - [ ] 1.2 新規ディレクトリ構成の作成
    - `app/`, `app/routers/`, `app/services/`, `app/models/`, `app/templates/`
    - `static/css/`, `static/js/`, `tests/`, `scripts/`
    - _Requirements: 設計書のディレクトリ構成_

## コア機能の実装

- [ ] 2. 設定管理モジュールの実装
  - [ ] 2.1 config.py の作成
    - Pydantic Settings を使用した設定クラス
    - 環境変数からの読み込みとデフォルト値
    - OS 別 TMP_DIR のデフォルト設定
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [ ]* 2.2 設定読み込みのプロパティテスト作成
    - **Property 7: 設定の環境変数優先**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [ ] 3. StorageService の実装
  - [ ] 3.1 StorageService 抽象クラスの定義
    - `save(file_like, filename) -> (file_id, file_path)`: file-like を保存し ID とパスを返す
    - `get_path(file_id) -> Optional[str]`: msoffcrypto 用にローカルパスを取得
    - `load`, `delete`, `generate_download_url`, `get_filename`, `is_expired` メソッド
    - _Requirements: 将来拡張性（Cloud Storage 連携）_
  - [ ] 3.2 LocalStorageService の実装
    - ファイルレジストリ（インメモリ）の管理
    - file_id の生成と有効期限管理（5分）
    - `get_path` で UnlockService にパスを提供
    - `save` はチャンク書き込みでメモリを抑制（例: 1MB単位）
    - 期限切れファイルの自動削除
    - _Requirements: 1.4, 6.1, ダウンロードURLの有効期限_
  - [ ]* 3.3 一時ファイル削除のプロパティテスト作成
    - **Property 3: 一時ファイルの削除**
    - **Validates: Requirements 1.4, 6.1**

- [ ] 4. UnlockService の実装
  - [ ] 4.1 Excel 解除ロジックの実装
    - `storage.get_path(file_id)` でローカルパスを取得
    - msoffcrypto-tool を使用したパスワード解除
    - 第1パスワード → 第2パスワード（存在する場合）の順で試行
    - 暗号化状態のチェック
    - 解除成功時は `storage.save` で解除済みファイルを保存
    - _Requirements: 1.1, 1.2, 1.3, 1.6_
  - [ ] 4.2 ファイル名変更ロジックの実装
    - `{元ファイル名}_解除.{拡張子}` 形式への変換
    - 拡張子なし、複数ドットのケース対応
    - _Requirements: 1.7_
  - [ ]* 4.3 パスワード解除のプロパティテスト作成
    - **Property 1: パスワード解除の成功条件**
    - **Property 2: パスワード不正時のエラーメッセージ**
    - **Property 5: パスワード未設定ファイルのエラー**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.6**
  - [ ]* 4.4 ファイル名変更のプロパティテスト作成
    - **Property 6: ファイル名変更規則**
    - **Validates: Requirements 1.7**

- [ ] 5. Checkpoint - コアサービスのテスト確認
  - Ensure all tests pass, ask the user if questions arise.

## API エンドポイントの実装

- [ ] 6. FastAPI アプリケーション基盤の作成
  - [ ] 6.1 main.py の作成
    - FastAPI アプリケーションの初期化
    - ルーターの登録
    - 静的ファイル配信の設定
    - Jinja2 テンプレートの設定
    - _Requirements: 4.3_
  - [ ] 6.2 同時リクエスト制御の実装
    - Semaphore を使用した MAX_WORKERS 制限
    - 429 レスポンスの返却
    - _Requirements: 1.5_
  - [ ]* 6.3 過負荷時の 429 レスポンスのプロパティテスト作成
    - **Property 4: 過負荷時の 429 レスポンス**
    - **Validates: Requirements 1.5**

- [ ] 7. /unlock エンドポイントの実装
  - [ ] 7.1 unlock.py ルーターの作成
    - multipart/form-data の受け取り（file, password1, password2）
    - ファイルバリデーション（拡張子、サイズ）を **save 前に実施**、NG なら 400 で即返却
    - バリデーション通過後に `storage.save` でファイル保存
    - `unlock_service.unlock(file_id, password1, password2)` で解除処理
    - StorageService 経由のファイル操作
    - _Requirements: 1.1, 1.2, 1.3, 1.6, 6.2, 6.3_
  - [ ]* 7.2 バリデーションのプロパティテスト作成
    - **Property 8: ファイル形式バリデーション**
    - **Property 9: ファイルサイズバリデーション**
    - **Validates: Requirements 6.2, 6.3**

- [ ] 8. /download エンドポイントの実装
  - [ ] 8.1 download.py ルーターの作成
    - file_id からのファイル取得（`storage.load`）
    - 存在しない/期限切れ file_id は HTTP 404 で `{"error":"Not Found","message":"ファイルが見つかりません"}` を返却
    - ダウンロード成功時は必ず `storage.delete` を呼び出す
    - _Requirements: API仕様（/download/{file_id}）、ダウンロードURLの有効期限_

- [ ] 9. /health エンドポイントの実装
  - [ ] 9.1 health.py ルーターの作成
    - {"status": "ok"} レスポンス
    - _Requirements: 4.4_

- [ ] 10. Pydantic スキーマの定義
  - [ ] 10.1 schemas.py の作成
    - UnlockRequest（password1: str, password2: Optional[str]）
    - UnlockResponse, TooManyRequestsResponse, HealthResponse
    - ErrorMessages 定数クラス
    - _Requirements: API仕様_

- [ ] 11. Checkpoint - API エンドポイントのテスト確認
  - Ensure all tests pass, ask the user if questions arise.

## フロントエンドの実装

- [ ] 12. Jinja2 テンプレートの作成
  - [ ] 12.1 index.html の作成
    - ファイル選択（複数可）
    - 第1パスワード入力欄（必須）
    - 第2パスワード入力欄（任意、空欄可）
    - 解除ボタン
    - ドラッグ＆ドロップ対応
    - レスポンシブデザイン（モバイル対応）
    - _Requirements: 2.1, 2.2, 3.1, 3.3_

- [ ] 13. CSS スタイルの作成
  - [ ] 13.1 style.css の作成
    - シンプルで直感的なデザイン
    - モバイルファーストのレスポンシブ対応
    - 処理状態の視覚的フィードバック
    - _Requirements: 2.3, 2.4, 3.1, 3.3_

- [ ] 14. JavaScript クライアントの実装
  - [ ] 14.1 app.js の作成
    - 並列リクエスト処理（Promise.all）
    - CLIENT_CONCURRENCY による同時リクエスト制限
    - 各ファイルの進捗表示（待機中/処理中/完了/エラー）
    - _Requirements: 2.3, 2.4_
  - [ ] 14.2 リトライロジックの実装
    - 429 受信時の retryAfter 秒後リトライ
    - 最大3回のリトライ制限
    - _Requirements: 2.6_
  - [ ]* 14.3 リトライ上限のテスト作成
    - **Property 10: リトライ上限**
    - **Validates: Requirements 2.6**
  - [ ] 14.4 ダウンロードボタンの実装
    - 解除成功時のダウンロードリンク表示
    - _Requirements: 2.5_

## Docker 環境の構築

- [ ] 15. Dockerfile の作成
  - [ ] 15.1 Dockerfile の作成
    - Python 3.11 ベースイメージ
    - 依存関係のインストール
    - 環境変数の設定（TMP_DIR, PORT, HOST, MAX_WORKERS）
    - _Requirements: 4.3, Dockerfile 環境変数_

- [ ] 16. docker-compose.yml の作成
  - [ ] 16.1 docker-compose.yml の作成
    - ポート公開（0.0.0.0:3000:3000）
    - 再起動ポリシー（unless-stopped）
    - デバッグ用ボリュームマウント（コメントアウト）
    - _Requirements: 4.1, 4.2, Docker 構成の補足_

- [ ] 17. requirements.txt の作成
  - [ ] 17.1 requirements.txt の作成
    - fastapi, uvicorn, python-multipart
    - msoffcrypto-tool
    - pydantic-settings
    - jinja2
    - pytest, hypothesis（開発用）
    - _Requirements: 技術的制約_

## テストとドキュメント

- [ ] 18. 統合テストの作成
  - [ ]* 18.1 API 統合テストの作成
    - /unlock, /download, /health の E2E テスト
    - TestClient を使用したリクエストテスト
    - _Requirements: 全 API 仕様_

- [ ] 19. パフォーマンステストスクリプトの作成
  - [ ] 19.1 perf-smoke.sh の作成
    - 20MB ダミーファイルの生成
    - N=4 並列リクエストの送信
    - 10 秒以内、HTTP 200 連続成功の確認
    - _Requirements: パフォーマンス計測、合否基準_

- [ ] 20. README.md の更新
  - [ ] 20.1 README.md の書き換え
    - プロジェクト概要
    - 起動方法（docker-compose up -d）
    - 使用方法
    - 設定項目一覧
    - _Requirements: 運用要件_

- [ ] 21. Final Checkpoint - 全テスト確認
  - Ensure all tests pass, ask the user if questions arise.
