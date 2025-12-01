# 設計書

## 概要

大量のExcelファイル（30ファイル程度）を同時に解除する際のUX改善機能の設計書。自動スクロール、ダウンロード済み表示、ダウンロード期限カウントダウン、一括ダウンロード、処理結果クリアの5つの機能を実装する。

## アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────┐
│         フロントエンド (Browser)         │
│  ┌────────────────────────────────────┐ │
│  │  index.html (Jinja2 Template)      │ │
│  │  - 処理結果セクション                │ │
│  │  - 一括ダウンロードボタン            │ │
│  │  - 処理結果クリアボタン              │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  app.js (JavaScript)               │ │
│  │  - カウントダウンタイマー管理        │ │
│  │  - ダウンロード済み状態管理          │ │
│  │  - 一括ダウンロード処理              │ │
│  │  - 自動スクロール処理                │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  style.css                         │ │
│  │  - カウントダウン表示スタイル        │ │
│  │  - ダウンロード済みボタンスタイル    │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                    │
                    │ HTTP/JSON
                    ▼
┌─────────────────────────────────────────┐
│      バックエンド (FastAPI/Python)       │
│  ┌────────────────────────────────────┐ │
│  │  unlock.py (Router)                │ │
│  │  - expiresAt フィールド追加         │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  download.py (Router)              │ │
│  │  - /download/bulk エンドポイント    │ │
│  │  - ZIP生成・配信                    │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  storage_service.py                │ │
│  │  - 一時ZIPファイル管理              │ │
│  │  - 有効期限管理（5分）              │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### レイヤー構成

1. **プレゼンテーション層**: HTML/CSS/JavaScript
   - UI表示・ユーザー操作の処理
   - カウントダウンタイマーの管理
   - ダウンロード済み状態の管理

2. **API層**: FastAPI Router
   - `/unlock` エンドポイントの拡張（expiresAt追加）
   - `/download/bulk` エンドポイントの新規実装

3. **ビジネスロジック層**: Service
   - ZIP生成ロジック
   - ファイル有効期限管理

4. **データ層**: StorageService
   - 一時ファイル保存・取得
   - 期限切れファイルの自動削除

## コンポーネントとインターフェース

### 1. フロントエンド コンポーネント

#### 1.1 カウントダウンタイマー管理

**責務**: 各ファイルのダウンロード期限をリアルタイムで表示

**インターフェース**:
```javascript
class CountdownTimer {
  constructor(fileId, expiresAt, element)
  start()
  stop()
  update()
  formatTime(seconds)
}
```

**状態管理**:
```javascript
const timers = new Map(); // fileId -> CountdownTimer
```

#### 1.2 ダウンロード済み状態管理

**責務**: ダウンロード済みファイルの視覚的な区別

**インターフェース**:
```javascript
const downloadedFiles = new Set(); // fileId のセット

function markAsDownloaded(fileId)
function isDownloaded(fileId)
function clearDownloadedState()
```

#### 1.3 一括ダウンロード処理

**責務**: 複数ファイルのZIP一括ダウンロード

**インターフェース**:
```javascript
async function bulkDownload(fileIds)
async function downloadZipFromUrl(url, filename)
```

**状態管理**:
```javascript
const successFileIds = new Set(); // 成功ファイルのfileIdを管理
```

**successFileIds の管理方法**:
- **追加タイミング**: 各ファイルの解除処理が `status=success` で完了した時点で `successFileIds.add(fileId)` を実行
- **参照タイミング**: 一括ダウンロードボタンクリック時に `Array.from(successFileIds)` で配列化してAPIリクエスト
- **クリアタイミング**: 処理結果クリア時に `successFileIds.clear()` を実行
- **ResultItem との同期**: ResultItem の status が 'success' になった時点で successFileIds に追加することで、両者を同期

#### 1.4 自動スクロール処理

**責務**: 解除ボタンクリック時の自動スクロール

**インターフェース**:
```javascript
function scrollToResults()
```

#### 1.5 処理結果クリア処理

**責務**: 処理結果セクションの状態リセット

**インターフェース**:
```javascript
function clearResults()
```

### 2. バックエンド コンポーネント

#### 2.1 UnlockRouter 拡張

**責務**: `/unlock` レスポンスに期限情報を追加

**変更点**:
```python
# app/routers/unlock.py

@router.post("/unlock")
async def unlock_file(...) -> JSONResponse:
    # 既存処理
    
    if result["success"]:
        # 成功時のみ expiresAt を計算
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(
            seconds=settings.DOWNLOAD_EXPIRY_SECONDS
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "fileName": result["unlocked_filename"],
                "status": "success",
                "message": None,
                "downloadUrl": download_url,
                "expiresAt": expires_at.isoformat() + "Z"  # 追加
            }
        )
    else:
        # エラー時は expiresAt を含めない
        return JSONResponse(
            status_code=400,
            content={
                "fileName": filename,
                "status": "error",
                "message": result["message"],
                "downloadUrl": None,
                "expiresAt": None  # エラー時は null
            }
        )
```

**expiresAt の取り扱い**:
- **成功時（status=success）**: expiresAt を UTC ISO8601形式で返す
- **エラー時（status=error）**: expiresAt は null を返す
- フロントエンドはカウントダウン開始の条件判定で `status === 'success' && expiresAt !== null` を使用

#### 2.2 BulkDownloadRouter (新規)

**責務**: 一括ダウンロードAPI

**エンドポイント**: `POST /download/bulk`

**インターフェース**:
```python
# app/routers/bulk_download.py (新規ファイル)

from pydantic import BaseModel
from typing import List

class BulkDownloadRequest(BaseModel):
    fileIds: List[str]

@router.post("/download/bulk")
async def bulk_download(
    request: Request,
    body: BulkDownloadRequest
) -> Response:
    """
    複数ファイルをZIP形式で一括ダウンロード
    
    処理順序:
    1. fileIds をユニーク化（重複除去）
    2. 各 fileId の存在チェックと有効期限チェック
    3. 有効なファイルのみでZIP生成
    4. 結果に応じてレスポンス返却:
       - 全件成功: HTTP 200 + ZIPバイナリ
       - 部分成功: HTTP 206 + JSON（downloadUrl, missingCount含む）
       - 全件不在: HTTP 404
    
    Returns:
        HTTP 200: ZIPバイナリストリーム
        HTTP 206: JSON（部分成功、downloadUrl含む）
        HTTP 400: バリデーションエラー
        HTTP 404: 全ファイル不在
        HTTP 500: ZIP生成失敗
    """
    pass
```

**処理フロー詳細**:
1. **重複除去**: `fileIds = list(set(body.fileIds))` でユニーク化
2. **存在・期限チェック**: 各fileIdに対して `storage_service.get_path()` で確認
3. **結果判定**:
   - `len(valid_ids) == len(fileIds)`: 全件成功 → HTTP 200
   - `len(valid_ids) > 0`: 部分成功 → HTTP 206
   - `len(valid_ids) == 0`: 全件不在 → HTTP 404

#### 2.3 ZipService (新規)

**責務**: ZIP生成とファイル管理

**インターフェース**:
```python
# app/services/zip_service.py (新規ファイル)

from typing import List, Tuple, Optional
from io import BytesIO

class ZipService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
    
    def create_zip(
        self, 
        file_ids: List[str]
    ) -> Tuple[BytesIO, List[str], List[str]]:
        """
        複数ファイルからZIPを生成
        
        Args:
            file_ids: ファイルIDのリスト
        
        Returns:
            (zip_buffer, successful_ids, missing_ids)
        """
        pass
    
    def save_temp_zip(
        self, 
        zip_buffer: BytesIO, 
        filename: str
    ) -> Tuple[str, str]:
        """
        一時ZIPファイルを保存
        
        Returns:
            (zip_id, zip_path)
        """
        pass
```

#### 2.4 StorageService 拡張

**責務**: 一時ZIPファイルの管理

**変更点**:
```python
# app/services/storage_service.py

class LocalStorageService(StorageService):
    # 既存メソッドはそのまま
    
    def save_zip(
        self, 
        zip_buffer: BytesIO, 
        filename: str
    ) -> Tuple[str, str]:
        """
        ZIPファイルを一時保存
        
        実装詳細:
        - zip_id を生成（UUID）
        - zip_path にファイルを保存
        - _file_registry に FileEntry を登録（created_at含む）
        - 既存の is_expired() / _cleanup_expired() メカニズムを流用
        
        Returns:
            (zip_id, zip_path)
        """
        pass
    
    def load_zip(self, zip_id: str) -> Optional[bytes]:
        """
        ZIPファイルを取得
        
        実装詳細:
        - is_expired(zip_id) で期限チェック
        - 期限切れの場合は None を返す（呼び出し側で HTTP 404）
        - 有効な場合はファイル内容を返す
        
        Returns:
            ZIPファイルのバイト列、期限切れ/不在の場合は None
        """
        pass
```

**期限管理の統一**:
- ZIPファイルも通常ファイルと同様に `_file_registry` で管理
- `is_expired()` メソッドで期限チェック（DOWNLOAD_EXPIRY_SECONDS基準）
- `_cleanup_expired()` で自動削除
- この方式により、個別ファイルとZIPファイルの期限管理を統一

## データモデル

### 1. フロントエンド データ構造

#### ResultItem (処理結果アイテム)
```typescript
interface ResultItem {
  fileId: string;
  fileName: string;
  fileSize: number;
  status: 'waiting' | 'uploading' | 'processing' | 'success' | 'error';
  message: string;
  downloadUrl: string | null;
  expiresAt: string | null;  // ISO8601 UTC
  downloaded: boolean;
  timerId: number | null;
}
```

#### BulkDownloadState (一括ダウンロード状態)
```typescript
interface BulkDownloadState {
  isLoading: boolean;
  successFileIds: string[];
}
```

### 2. バックエンド データ構造

#### UnlockResponse (拡張)
```python
class UnlockResponse(BaseModel):
    fileName: str
    status: str
    message: Optional[str]
    downloadUrl: Optional[str]
    expiresAt: Optional[str]  # 追加: ISO8601 UTC
```

#### BulkDownloadRequest
```python
class BulkDownloadRequest(BaseModel):
    fileIds: List[str] = Field(..., min_items=1, max_items=100)
```

#### BulkDownloadPartialResponse
```python
class BulkDownloadPartialResponse(BaseModel):
    status: str = "partial"
    downloadUrl: str
    downloadedCount: int
    missingCount: int
    message: str
```

## エラーハンドリング

### 1. フロントエンド エラー処理

#### カウントダウンタイマー
- **期限切れ**: ボタン無効化、「期限切れ」表示
- **タイマー停止失敗**: コンソールログ出力、継続動作

#### 一括ダウンロード
- **HTTP 400**: トースト通知「リクエストが不正です」
- **HTTP 206**: トースト通知「X件のファイルが見つかりませんでした」、部分ダウンロード実行
- **HTTP 500**: トースト通知「ZIP生成に失敗しました」
- **ネットワークエラー**: トースト通知「ネットワークエラーが発生しました」

#### 処理結果クリア
- **タイマー停止エラー**: 無視して継続（ベストエフォート）

### 2. バックエンド エラー処理

#### /download/bulk
- **fileIds 空**: HTTP 400 `{"error": "fileIds が空です"}`
- **fileIds 100件超過**: HTTP 400 `{"error": "ファイル数が上限を超えています"}`
- **全ファイル不在**: HTTP 404 `{"error": "ファイルが見つかりません"}`
- **ZIP生成失敗**: HTTP 500 `{"error": "ZIP生成に失敗しました"}`
- **部分成功**: HTTP 206 + JSON（downloadUrl含む）

## テスト戦略

### 1. ユニットテスト

#### フロントエンド
- **CountdownTimer**: 時間計算、フォーマット、期限切れ検出
- **ダウンロード済み状態管理**: Set操作、状態確認
- **一括ダウンロード**: fileIds収集、Blob生成、ダウンロード実行

#### バックエンド
- **ZipService.create_zip**: 正常系、部分成功、全失敗
- **ZipService.save_temp_zip**: ファイル保存、ID生成
- **BulkDownloadRouter**: バリデーション、レスポンス形式

### 2. 統合テスト

- **自動スクロール**: 解除ボタンクリック → 処理結果セクションへスクロール
- **カウントダウン表示**: 解除成功 → カウントダウン開始 → 1秒ごと更新
- **ダウンロード済み表示**: ダウンロードクリック → ボタン状態変更
- **一括ダウンロード（成功）**: 複数ファイル選択 → ZIP生成 → ダウンロード
- **一括ダウンロード（部分成功）**: 一部期限切れ → HTTP 206 → 通知 → 部分ダウンロード
- **処理結果クリア**: クリアボタンクリック → 状態リセット → タイマー停止

### 3. E2Eテスト

- **30ファイル一括処理**: ファイルアップロード → 解除 → 自動スクロール → カウントダウン表示 → 一括ダウンロード → 処理結果クリア

## セキュリティ考慮事項

### 1. 入力バリデーション
- **fileIds**: 配列長チェック（1-100件）、重複除去、型チェック
- **ZIP生成**: ファイル名サニタイズ、パストラバーサル防止

### 2. リソース制限
- **ZIP最大サイズ**: 個別ファイル50MB × 100件 = 5GB上限（実装時に調整）
- **同時リクエスト**: 既存のSemaphore制御を継承

### 3. 一時ファイル管理
- **有効期限**: 5分で自動削除
- **ディスク容量**: 定期クリーンアップ（既存機能）

## パフォーマンス考慮事項

### 1. フロントエンド
- **カウントダウンタイマー**: 1秒間隔、軽量な時間計算
- **DOM操作**: 最小限の更新、バッチ処理
- **メモリ管理**: Blob URL の適切な解放

### 2. バックエンド
- **ZIP生成**: ストリーミング処理、メモリ効率化
- **並列処理**: 既存の MAX_WORKERS 制御を継承
- **ファイルI/O**: チャンク読み込み（既存実装）

## デプロイメント考慮事項

### 1. 設定変更
- **app/config.py**: 変更不要（DOWNLOAD_EXPIRY_SECONDS 既存）
- **app/main.py**: テンプレート変数追加

### 2. 依存関係
- **Python**: zipfile（標準ライブラリ）
- **JavaScript**: 追加ライブラリ不要

### 3. データベース
- 不要（インメモリ管理）

### 4. 後方互換性
- **既存API**: 変更なし（/unlock は拡張のみ）
- **既存UI**: 段階的な機能追加

## 実装の優先順位

### Phase 1: 基本機能（MVP）
1. 自動スクロール
2. ダウンロード済み表示
3. 処理結果クリア

### Phase 2: 期限表示
4. expiresAt フィールド追加（バックエンド）
5. カウントダウンタイマー実装（フロントエンド）

### Phase 3: 一括ダウンロード
6. /download/bulk エンドポイント（HTTP 200のみ）
7. フロントエンド一括ダウンロード処理

### Phase 4: 高度な機能
8. HTTP 206 部分成功対応
9. エラーハンドリング強化

## 技術的な設計判断

### 1. カウントダウン計算方法
**選択**: サーバー起算UTC時刻（expiresAt）
**理由**: クライアント時刻ずれ・タイムゾーン差異を排除
**代替案**: クライアント側で5分加算 → 誤差が累積するため不採用

### 2. 一括ダウンロード部分成功時のレスポンス
**選択**: HTTP 206 + JSON（downloadUrl含む）
**理由**: メタ情報とZIPを分離し、フロントで柔軟に処理
**代替案**: HTTP 206 + ZIPバイナリ + ヘッダー → アンカータグで読めないため不採用

### 3. 処理結果クリア時のサーバー側ファイル
**選択**: サーバー側は削除しない（期限管理に任せる）
**理由**: 既存の5分有効ルールと整合性を保つ
**代替案**: クリア時に削除API呼び出し → 複雑化するため不採用

### 4. カウントダウンタイマーの実装
**選択**: setInterval + Map管理
**理由**: シンプルで軽量、タイマー停止が容易
**代替案**: requestAnimationFrame → オーバースペックのため不採用

### 5. ZIP生成ライブラリ
**選択**: Python標準ライブラリ zipfile
**理由**: 追加依存なし、十分な機能
**代替案**: 外部ライブラリ → 不要な複雑化のため不採用
