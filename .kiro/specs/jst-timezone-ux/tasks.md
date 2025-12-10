# 実装タスクリスト

## 概要

本タスクリストは、Excel パスワード解除ツールにおける日本時間（JST）対応機能の実装手順を定義します。各タスクは段階的に実装され、テストを通じて正確性を検証します。

## タスク

- [ ] 1. tzdata依存の追加
  - `requirements.txt` に `tzdata` パッケージを追加
  - Python 3.9+でIANA TZデータが確実に利用可能にする
  - _要件: 5.2, 5.3_

- [ ] 2. タイムゾーンユーティリティの作成
  - `app/utils/` ディレクトリを作成（存在しない場合）
  - `app/utils/__init__.py` を作成
  - `app/utils/timezone_utils.py` を作成
  - UTC定数とJST定数を定義
  - タイムゾーン変換ヘルパー関数を実装
  - _要件: 5.1, 5.4, 5.5_

- [ ] 2.1 UTC/JST定数の定義
  - `UTC = timezone.utc` を定義
  - `JST = ZoneInfo('Asia/Tokyo')` を定義
  - 固定オフセット表現や文字列直書きを禁止
  - _要件: 5.4, 5.5_

- [ ] 2.2 get_jst_now() の実装
  - `datetime.now(UTC).astimezone(JST)` で実装
  - ローカルTZやTZ環境変数に依存しない
  - _要件: 1.4, 5.1_

- [ ] 2.3 ensure_utc() の実装
  - strictモードで例外を投げる、または少なくともテストで失敗として検知する
  - サイレント補正のみは禁止（9時間ズレの温床を防ぐ）
  - tz-awareの場合はUTCに変換
  - naive検出時はログに警告を出力
  - _要件: 2.4, 3.7, 6.7_

- [ ] 2.4 to_jst() / to_utc() の実装
  - `astimezone()` メソッドを使用した明示的な変換
  - 手作業の加減算は禁止
  - _要件: 1.4, 2.7, 5.1_

- [ ] 2.5 format_http_date() の実装
  - `email.utils.format_datetime(dt.astimezone(UTC), usegmt=True)` で実装
  - RFC 7231準拠のHTTP-date形式（GMT表記）
  - 入力はtz-aware UTC datetimeのみ
  - _要件: 3.3, 3.4, 3.5_

- [ ] 2.6 datetime_to_zip_tuple() の実装
  - `ensure_utc(dt) → to_jst(...) → timetuple()[:6]` で実装
  - ZipInfo.date_time用の6要素タプルを返す
  - JST基準のタイムスタンプ
  - _要件: 2.3, 2.7_

- [ ]* 2.7 timezone_utils のユニットテスト
  - 各関数の基本動作を検証
  - naive datetime の補正動作を検証
  - タイムゾーン変換の正確性を検証
  - _要件: 6.3_

- [ ]* 2.8 timezone_utils のプロパティベーステスト
  - **プロパティ 1**: タイムゾーン変換の可逆性（UTC→JST→UTC）
  - **プロパティ 2**: naive datetime の補正（ensure_utc）
  - **プロパティ 3**: ZIPタイムスタンプの範囲（datetime_to_zip_tuple）
  - **プロパティ 4**: HTTP-date形式の正確性（format_http_date）
  - 各プロパティテストは100回以上の反復実行
  - _要件: 6.3, 6.6_

- [ ] 3. StorageService の拡張
  - `app/services/storage_service.py` を修正
  - `FileEntry.created_at` をtz-aware UTC datetimeに変更
  - `get_mtime()` メソッドを追加
  - `is_expired()` の比較をUTC基準に変更
  - _要件: 3.6, 4.1, 4.3, 4.4_

- [ ] 3.1 FileEntry.created_at の修正
  - デフォルトファクトリを `datetime.now()` から `datetime.now(UTC)` に変更
  - 既存のレジストリエントリとの互換性を確保
  - _要件: 4.4_

- [ ] 3.2 get_mtime() メソッドの追加
  - `os.path.getmtime()` から秒を取得
  - `datetime.fromtimestamp(ts, UTC)` でtz-aware UTCに変換
  - ファイルが存在しない場合は None を返す
  - _要件: 3.6_

- [ ] 3.3 is_expired() の修正
  - `datetime.now()` を `datetime.now(UTC)` に変更
  - UTC基準の比較を使用
  - _要件: 4.1, 4.3_

- [ ]* 3.4 StorageService のユニットテスト更新
  - `get_mtime()` の動作を検証
  - tz-aware UTC datetimeが返されることを検証
  - `is_expired()` のUTC基準比較を検証
  - _要件: 6.3_

- [ ] 4. ZipService の拡張
  - `app/services/zip_service.py` を修正
  - `create_zip()` でZipInfoを使用
  - JST基準のタイムスタンプを設定
  - チャンク転送でメモリ使用量を抑制
  - _要件: 2.1, 2.2, 2.6_

- [ ] 4.1 create_zip() の修正
  - `zf.write()` から `ZipInfo + zf.open() + shutil.copyfileobj` に変更
  - `storage_service.get_mtime()` でファイルのmtimeを取得
  - `datetime_to_zip_tuple()` でJST基準のタイムスタンプを設定
  - 1MBチャンクでストリーミング書き込み
  - _要件: 2.1, 2.2, 2.3, 2.6_

- [ ]* 4.2 ZipService のユニットテスト更新
  - ZipInfo.date_timeがJST基準であることを検証
  - チャンク転送が正しく動作することを検証
  - メモリ使用量が抑制されていることを確認
  - _要件: 6.3, 6.4_

- [ ] 5. bulk_download エンドポイントの修正
  - `app/routers/bulk_download.py` を修正
  - ZIPファイル名生成をJST基準に変更
  - `_JST` サフィックスを追加
  - _要件: 1.1, 1.2, 1.3_

- [ ] 5.1 bulk_download() の修正
  - `datetime.now(timezone.utc)` を `get_jst_now()` に変更
  - ファイル名形式を `解除済み_YYYYMMDD_HHMMSS_JST.zip` に変更
  - UTC表示（`Z`）を削除
  - _要件: 1.1, 1.2, 1.3, 1.5_

- [ ]* 5.2 bulk_download のユニットテスト更新
  - ファイル名がJST基準であることを検証
  - `_JST` サフィックスが含まれることを検証
  - UTC表示が含まれないことを検証
  - _要件: 6.3, 6.4_

- [ ] 6. download エンドポイントの拡張
  - `app/routers/download.py` を修正
  - Last-Modifiedヘッダーを追加
  - UTC mtimeから直接HTTP-date(GMT)を生成（中間JST変換は不要）
  - _要件: 3.1, 3.2, 3.3, 3.5_

- [ ] 6.1 download_file() の修正
  - `storage_service.get_mtime()` でファイルのUTC mtimeを取得
  - `format_http_date()` でUTC→HTTP-date(GMT)に直接変換
  - Last-Modifiedヘッダーを追加
  - FileResponse使用時は自動付与されるため注意
  - 中間でJSTに変換する必要はない
  - _要件: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 6.2 download のユニットテスト更新
  - Last-Modifiedヘッダーが含まれることを検証
  - RFC 7231準拠のHTTP-date形式であることを検証
  - UTC/GMT表記であることを検証
  - _要件: 6.3, 6.5_

- [ ] 7. チェックポイント - すべてのテストを実行
  - すべてのユニットテストが合格することを確認
  - すべてのプロパティベーステストが合格することを確認
  - 既存のテストが引き続き合格することを確認
  - 質問があればユーザーに確認
  - _要件: 6.1, 6.2_

- [ ]* 8. 統合テストの作成
  - `/download/bulk` エンドポイントの完全なフローをテスト
  - `/download/{file_id}` エンドポイントの完全なフローをテスト
  - ZIPファイル名、ZIP内タイムスタンプ、Last-Modifiedヘッダーを検証
  - _要件: 6.3_

- [ ]* 8.1 bulk_download 統合テスト
  - ZIPファイル名がJST基準であることを検証
  - ZIP内ファイルのタイムスタンプがJST基準であることを検証
  - 部分成功時のdownloadUrlが正しいことを検証
  - _要件: 6.4_

- [ ]* 8.2 download 統合テスト
  - Last-ModifiedヘッダーがRFC 7231準拠であることを検証
  - ファイルが正しくダウンロードできることを検証
  - 有効期限が正しく動作することを検証
  - _要件: 6.5_

- [ ]* 8.3 naive datetime ガードのテスト
  - naive入力が渡された場合に例外を投げることを検証
  - または少なくともテストで失敗として検知することを検証
  - サイレント補正のみは禁止
  - _要件: 6.7_

- [ ]* 8.4 共通定数使用の検証テスト
  - ZipInfo.date_time書き込みとLast-Modified生成が同一定数（UTC, JST）を使用することを検証
  - タイムゾーン変換が共通定数経由であることを検証
  - _要件: 6.6_

- [ ] 9. 最終チェックポイント - すべてのテストを実行
  - すべてのユニットテストが合格することを確認
  - すべてのプロパティベーステストが合格することを確認
  - すべての統合テストが合格することを確認
  - 既存のテストが引き続き合格することを確認
  - 質問があればユーザーに確認
  - _要件: 6.1, 6.2_

- [ ] 10. ドキュメントの更新
  - README.md にJST対応機能を追記
  - リリースノートにZIPファイル名形式の変更を明記
  - API仕様書にLast-Modifiedヘッダーを追記
  - _要件: 5.6_

## 注意事項

- **オプションタスク（`*` 付き）**: テスト関連のタスクはオプションとしてマークされていますが、品質保証のため実装を推奨します
- **タスクの順序**: タスクは依存関係を考慮して順序付けられています。順番通りに実行してください
- **チェックポイント**: タスク7と9はチェックポイントです。すべてのテストが合格することを確認してから次に進んでください
- **プロパティベーステスト**: 各プロパティテストは100回以上の反復実行を推奨します
- **naive datetime**: naive datetimeは禁止です。すべてのdatetimeはtz-awareでなければなりません
- **共通定数**: すべてのタイムゾーン処理は `timezone_utils.py` で定義された定数（UTC, JST）を使用してください
- **メモリ効率**: ZIPファイル生成時は全読み込みを避け、チャンク転送を使用してください
