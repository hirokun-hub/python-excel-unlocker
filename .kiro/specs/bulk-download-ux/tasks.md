# 実装タスクリスト

## Phase 1: 基本機能（MVP）

- [ ] 1. 自動スクロール機能の実装
  - `static/js/app.js` に `scrollToResults()` 関数を実装
  - 解除ボタンクリック時に処理結果セクションへスムーズスクロール
  - `scrollIntoView({behavior:'smooth'})` を使用
  - _要件: 1.1, 1.2_

- [ ] 2. ダウンロード済み表示機能の実装
  - `static/js/app.js` にダウンロード済み状態管理を実装
  - `downloadedFiles` Set を追加（fileId をキーとして管理）
  - `markAsDownloaded(fileId)` 関数を実装
  - ダウンロードボタン生成時に `data-file-id` 属性を付与
  - ダウンロードボタンにクリックハンドラを追加し、クリック時に `markAsDownloaded(fileId)` を呼び出す
  - ダウンロードボタンクリック時にボタンテキストを「ダウンロード済み」に変更
  - ダウンロードボタンクリック時に背景色をグレーに変更
  - `static/css/style.css` にダウンロード済みボタンのスタイルを追加
  - _要件: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 3. 処理結果クリア機能の実装
  - `app/templates/index.html` に「処理結果をクリア」ボタンを追加
  - `static/js/app.js` に `clearResults()` 関数を実装
  - 処理結果リストの全アイテム削除
  - 処理結果セクションを非表示
  - ダウンロード済みフラグをリセット
  - _要件: 4.1, 4.2, 4.3, 4.4, 4.7_

- [ ] 4. Checkpoint - 基本機能の動作確認
  - 全テストが通ることを確認
  - 質問があればユーザーに確認

## Phase 2: 期限表示機能

- [ ] 5. バックエンド: expiresAt と fileId フィールド追加
  - `app/routers/unlock.py` の `/unlock` エンドポイントを拡張
  - 成功時に `fileId` (解除済みファイルのID) を返す
  - 成功時に `expiresAt` (UTC ISO8601) を計算して返す
  - エラー時は `expiresAt: null`, `fileId: null` を返す
  - `app/models/schemas.py` の `UnlockResponse` に `fileId: str` と `expiresAt: Optional[str]` フィールドを追加
  - _要件: 2.6, API仕様拡張_

- [ ] 6. フロントエンド: APP_CONFIG に期限定数を注入
  - `app/main.py` のテンプレート変数に `download_expiry_seconds` を追加
  - `app/templates/index.html` の `APP_CONFIG` に `downloadExpirySeconds` を追加
  - _要件: 2 技術仕様_

- [ ] 7. フロントエンド: カウントダウンタイマー実装
  - `static/js/app.js` に `CountdownTimer` クラスを実装
  - `timers` Map でタイマーを管理（fileId をキーとして使用）
  - `start()`, `stop()`, `update()`, `formatTime()` メソッドを実装
  - 解除成功時のレスポンスから `fileId` と `expiresAt` を取得
  - 結果アイテムのDOM要素に `data-file-id` 属性を設定
  - 1秒ごとに残り時間を更新
  - 1分未満で赤色警告表示
  - 0秒到達で「期限切れ」表示とボタン無効化
  - _要件: 2.7, 2.8, 2.9, 2.10_

- [ ] 8. フロントエンド: カウントダウン表示UI
  - `app/templates/index.html` にカウントダウン表示要素を追加
  - ダウンロードボタンの右側に配置
  - `static/css/style.css` にカウントダウン表示スタイルを追加
  - 警告色（赤）のスタイルを追加
  - _要件: 2 技術仕様_

- [ ] 9. フロントエンド: カウントダウン開始・停止処理
  - 解除成功時（status=success && expiresAt !== null）にタイマー開始
  - 処理結果クリア時に全タイマーを停止（clearInterval）
  - ページ離脱時に全タイマーを停止
  - _要件: 2 技術仕様_

- [ ] 10. Checkpoint - 期限表示機能の動作確認
  - 全テストが通ることを確認
  - 質問があればユーザーに確認

## Phase 3: 一括ダウンロード機能

- [ ] 11. バックエンド: ZipService の実装
  - `app/services/zip_service.py` を新規作成
  - `ZipService` クラスを実装
  - `create_zip(file_ids)` メソッドを実装（zipfile使用）
  - fileIds をユニーク化
  - 存在・期限チェック
  - 有効なファイルのみでZIP生成
  - (zip_buffer, successful_ids, missing_ids) を返す
  - _要件: 3 API仕様_

- [ ] 12. バックエンド: StorageService の ZIP対応拡張
  - `app/services/storage_service.py` に `save_zip()` メソッドを追加
  - `_file_registry` に FileEntry を登録
  - 既存の `is_expired()` / `_cleanup_expired()` を流用
  - `load_zip()` メソッドを追加
  - 期限チェック後にZIPファイル内容を返す
  - _要件: 3 クリーンアップポリシー_

- [ ] 13. バックエンド: /download/bulk エンドポイント実装（HTTP 200のみ）
  - `app/routers/bulk_download.py` を新規作成
  - `BulkDownloadRequest` スキーマを定義
  - `POST /download/bulk` エンドポイントを実装
  - 入力バリデーション（空配列、重複除去、100件上限）
  - 全件成功時は HTTP 200 + ZIPバイナリストリーム
  - ファイル名: `解除済み_YYYYMMDD_HHMMSSZ.zip` (UTC)
  - _要件: 3.1, 3.2, 3.3, 3.4, 入力バリデーション_

- [ ] 14. バックエンド: /download/bulk エンドポイントにルーター登録
  - `app/main.py` に `bulk_download` ルーターを登録
  - _要件: 3 API仕様_

- [ ] 15. フロントエンド: successFileIds 状態管理
  - `static/js/app.js` に `successFileIds` Set を追加
  - 解除成功時のレスポンスから `fileId` を取得
  - 解除成功時（status=success && fileId）に `successFileIds.add(fileId)` を実行
  - 結果アイテムのDOM要素に `data-file-id` 属性を保持
  - 処理結果クリア時に `successFileIds.clear()` を実行
  - _設計書: 1.3 一括ダウンロード処理_

- [ ] 16. フロントエンド: 一括ダウンロードボタンUI
  - `app/templates/index.html` に「一括ダウンロード」ボタンを追加
  - 処理結果セクションのヘッダーに配置
  - 成功ファイル2件以上で表示、1件以下で非表示
  - `static/css/style.css` にボタンスタイルを追加
  - _要件: 3.1, 3.2_

- [ ] 17. フロントエンド: 一括ダウンロード処理（HTTP 200のみ）
  - `static/js/app.js` に `bulkDownload()` 関数を実装
  - `Array.from(successFileIds)` で fileIds 配列を生成
  - `POST /download/bulk` に `{fileIds: [...]}` をリクエスト
  - HTTP 200 受信時は直接ZIPダウンロード
  - ローディング状態管理（二重押下防止）
  - 成功時は全対象ファイル（successFileIds内の各fileId）を「ダウンロード済み」に変更
  - 各fileIdに対応するDOM要素を `data-file-id` で検索して状態更新
  - _要件: 3.3, 3.5, 3.7_

- [ ] 18. Checkpoint - 一括ダウンロード基本機能の動作確認
  - 全テストが通ることを確認
  - 質問があればユーザーに確認

## Phase 4: 高度な機能（部分成功対応）

- [ ] 19. バックエンド: HTTP 206 部分成功対応
  - `app/routers/bulk_download.py` を拡張
  - 部分成功時（一部ファイル不在）の処理を追加
  - 一時ZIPを保存し `downloadUrl` を生成
  - HTTP 206 + JSON レスポンス（downloadUrl, downloadedCount, missingCount, message）
  - 全件不在時は HTTP 404
  - `app/models/schemas.py` に `BulkDownloadPartialResponse` を追加
  - _要件: 3.6, 3 API仕様, エラーハンドリング_

- [ ] 20. バックエンド: 一時ZIP用ダウンロードエンドポイント
  - `app/routers/bulk_download.py` に `GET /download/bulk/{zip_id}` を追加
  - `storage_service.load_zip(zip_id)` でZIPを取得
  - 期限切れ時は HTTP 404
  - _要件: 3 クリーンアップポリシー_

- [ ] 21. フロントエンド: HTTP 206 部分成功対応
  - `static/js/app.js` の `bulkDownload()` を拡張
  - HTTP 206 受信時の処理を追加
  - JSONから `downloadUrl`, `downloadedCount`, `missingCount` を取得
  - トースト通知「X件のファイルが見つかりませんでした」
  - `downloadZipFromUrl()` 関数を実装（fetch → Blob → a要素ダウンロード）
  - 取得できたファイルのみ「ダウンロード済み」に変更（downloadedCount分のfileId）
  - 各fileIdに対応するDOM要素を `data-file-id` で検索して状態更新
  - _要件: 3.6, 3 部分成功時の実装方針, エラーハンドリング_

- [ ] 22. フロントエンド: エラーハンドリング強化
  - HTTP 400: トースト通知「リクエストが不正です」
  - HTTP 404: トースト通知「ファイルが見つかりません」
  - HTTP 500: トースト通知「ZIP生成に失敗しました」
  - ネットワークエラー: トースト通知「ネットワークエラーが発生しました」
  - _要件: 3 エラーハンドリング_

- [ ] 23. 最終 Checkpoint - 全機能の動作確認
  - 全テストが通ることを確認
  - E2Eテスト: 30ファイル一括処理フロー
  - 質問があればユーザーに確認

