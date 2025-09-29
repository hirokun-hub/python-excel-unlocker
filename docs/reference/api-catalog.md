【出力】リファレンス.API_カタログ

```yaml
---
layout: default
title: APIカタログ
description: Excel パスワード解除ツールの公開APIエンドポイント、リクエスト/レスポンス仕様、エラーコード一覧
author: Hiroaki Endo
permalink: api-catalog
date: 2025-01-19
last_modified_at: 2025-01-19
published: false
Tags:
  - api
  - reference
  - backend
  - frontend
  - authentication
  - excel_processing
  - google_drive
  - error_handling
---
```

> 内容の最終確認が必要です。数値・日付は原典と照合してください。

**結論**：バックエンドAPI 2つ、フロントエンドAPI 3つの計5エンドポイントでJWT認証とBot保護を実装  
**対象**：開発者・QA担当者・運用担当者  
**所要時間**：10分  
**次の一手**：1) 認証設定確認 → 2) エンドポイントテスト → 3) エラーハンドリング検証  
**根拠**：・get_upload_url.py/unlock.py実装・フロントエンドAPI routes実装・JWT認証統一仕様

## バックエンドAPI（AWS Lambda + API Gateway）

### 共通仕様

#### 認証方式
- **JWT認証**: `Authorization: Bearer <id_token>` ヘッダー必須
- **Bot保護**: リクエストボディにreCAPTCHA/Turnstileトークン自動付与
- **ユーザー制限**: 環境変数 `ALLOWED_USERS` で許可されたメールアドレスのみ

#### 共通レスポンス形式

**成功レスポンス**:
```json
{
  "success": true,
  // エンドポイント固有のデータ
}
```

**エラーレスポンス**:
```json
{
  "success": false,
  "error": "error_code",
  "message": "ユーザー向けエラーメッセージ",
  "suggestion": "解決方法の提案（任意）"
}
```

#### 共通HTTPヘッダー
```
Content-Type: application/json
Access-Control-Allow-Origin: <環境別固定オリジン>
Access-Control-Allow-Credentials: true
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 1. 署名付きURL生成API

**エンドポイント**: `POST /presigned-urls`

**目的**: S3アップロード用の署名付きURLを生成する

#### リクエスト

```json
{
  "fileName": "sample.xlsx",
  "fileSize": 1048576,
  "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

**パラメータ**:
- `fileName` (string, 必須): アップロードするファイル名
- `fileSize` (number, 任意): ファイルサイズ（バイト）
- `contentType` (string, 任意): MIMEタイプ

#### レスポンス

**成功時（200 OK）**:
```json
{
  "success": true,
  "uploadUrl": "https://s3.amazonaws.com/bucket/...",
  "uploadFields": {
    "key": "uploads/20250119_123456_sample.xlsx",
    "policy": "eyJ...",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-credential": "...",
    "x-amz-date": "20250119T123456Z",
    "x-amz-signature": "..."
  },
  "fileKey": "uploads/20250119_123456_sample.xlsx",
  "expiresIn": 60,
  "method": "POST"
}
```

**レスポンスフィールド**:
- `uploadUrl`: S3アップロード先URL
- `uploadFields`: 署名付きPOSTに必要なフィールド
- `fileKey`: 生成されたS3オブジェクトキー
- `expiresIn`: URL有効期限（秒）
- `method`: アップロード方式（POST固定）

#### エラーコード

| エラーコード | HTTPステータス | 説明 |
|-------------|---------------|------|
| `authentication_failed` | 401 | JWT認証失敗 |
| `access_denied` | 403 | ユーザーアクセス権限なし |
| `bot_protection_failed` | 403 | Bot保護チェック失敗 |
| `rate_limit_exceeded` | 429 | レート制限超過 |
| `missing_filename` | 400 | ファイル名未指定 |
| `unsupported_format` | 400 | サポート外ファイル形式 |
| `file_too_large` | 400 | ファイルサイズ超過（20MB） |
| `macro_file_rejected` | 400 | マクロ付きExcelファイル（.xlsm） |
| `configuration_error` | 500 | サーバー設定エラー |

### 2. Excel解除処理API

**エンドポイント**: `POST /unlock`

**目的**: パスワード保護されたExcelファイルを解除する

#### リクエスト

**複数ファイル処理（推奨）**:
```json
{
  "files": [
    {
      "s3_key": "uploads/20250119_123456_file1.xlsx",
      "original_name": "file1.xlsx"
    },
    {
      "s3_key": "uploads/20250119_123457_file2.xlsx", 
      "original_name": "file2.xlsx"
    }
  ],
  "passwords": ["password1", "password2", "123456"]
}
```

**単一ファイル処理（後方互換）**:
```json
{
  "fileKey": "uploads/20250119_123456_sample.xlsx",
  "passwords": ["password1", "password2"],
  "fileName": "sample.xlsx"
}
```

**パラメータ**:
- `files` (array, 複数ファイル時必須): ファイル情報配列
  - `s3_key` (string): S3オブジェクトキー
  - `original_name` (string): 元のファイル名
- `passwords` (array, 必須): 試行するパスワード候補
- `fileKey` (string, 単一ファイル時): S3オブジェクトキー（後方互換）
- `fileName` (string, 単一ファイル時): ファイル名（後方互換）

#### レスポンス

**成功時（200 OK）**:
```json
{
  "success": true,
  "results": [
    {
      "fileName": "file1_unlocked.xlsx",
      "status": "success",
      "downloadUrl": "https://s3.amazonaws.com/bucket/unlocked/..."
    },
    {
      "fileName": "file2_unlocked.xlsx", 
      "status": "error",
      "message": "入力されたパスワードでは解除できませんでした。別のパスワード候補をお試しください。"
    }
  ]
}
```

**レスポンスフィールド**:
- `results` (array): 処理結果配列（ProcessResult形式）
  - `fileName` (string): 解除済みファイル名
  - `status` (string): 処理状況（"success" | "error"）
  - `downloadUrl` (string, 成功時): ダウンロード用署名付きURL（有効期限300秒）
  - `message` (string, エラー時): エラーメッセージ

#### エラーコード

| エラーコード | HTTPステータス | 説明 |
|-------------|---------------|------|
| `authentication_failed` | 401 | JWT認証失敗 |
| `access_denied` | 403 | ユーザーアクセス権限なし |
| `missing_parameter` | 400 | 必須パラメータ不足 |
| `invalid_json` | 400 | JSONフォーマットエラー |
| `internal_server_error` | 500 | 予期しないサーバーエラー |

**個別ファイル処理エラー（results内のmessage）**:
- パスワード解除失敗: "入力されたパスワードでは解除できませんでした"
- 暗号化なし: "ファイルは暗号化されていませんでした"
- ファイル形式エラー: "サポートされていないファイル形式です"
- システムエラー: "Excel処理モジュールが利用できません"

## フロントエンドAPI（Next.js API Routes）

### 共通仕様

#### 認証方式
- **セッション認証**: Next-Auth.jsセッション必須
- **Google OAuth**: Google Drive APIアクセス用

#### 共通エラーレスポンス
```json
{
  "error": "エラーメッセージ"
}
```

### 3. Google Drive フォルダ一覧API

**エンドポイント**: `GET /api/drive/folders`

**目的**: Google Driveのフォルダ一覧を取得する

#### リクエストパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| `parentId` | string | 任意 | 親フォルダID（デフォルト: "root"） |
| `q` | string | 任意 | 検索クエリ（フォルダ名部分一致） |
| `pageToken` | string | 任意 | ページネーション用トークン |

#### レスポンス

**成功時（200 OK）**:
```json
{
  "files": [
    {
      "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
      "name": "プロジェクト資料",
      "mimeType": "application/vnd.google-apps.folder",
      "parents": ["0BwwA4oUTeiV1TGRPeTVjaWRDY1E"],
      "modifiedTime": "2025-01-19T12:34:56.789Z",
      "driveId": null,
      "displayPath": "マイドライブ / 業務 / プロジェクト資料"
    }
  ],
  "nextPageToken": "CAESBggBEAIYAw"
}
```

**レスポンスフィールド**:
- `files` (array): フォルダ情報配列
  - `id` (string): フォルダID
  - `name` (string): フォルダ名
  - `displayPath` (string): 表示用パス（ルートからの階層）
  - `parents` (array): 親フォルダID配列
  - `modifiedTime` (string): 最終更新日時（ISO 8601）
  - `driveId` (string|null): 共有ドライブID
- `nextPageToken` (string): 次ページトークン

#### エラーコード

| HTTPステータス | 説明 |
|---------------|------|
| 401 | Google認証失敗・トークン期限切れ |
| 500 | Google Drive API呼び出しエラー |

### 4. Google Drive アップロードAPI

**エンドポイント**: `POST /api/drive/upload`

**目的**: ファイルをGoogle Driveにアップロードする

#### リクエスト

**Content-Type**: `multipart/form-data`

| フィールド | 型 | 必須 | 説明 |
|-----------|---|------|------|
| `file` | File | 必須 | アップロードするファイル |
| `filename` | string | 必須 | 保存時のファイル名 |
| `parentId` | string | 任意 | 保存先フォルダID |

#### レスポンス

**成功時（200 OK）**:
```json
{
  "success": true,
  "file": {
    "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "name": "sample_unlocked.xlsx",
    "webViewLink": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view"
  },
  "message": "ファイルがGoogle Driveに保存されました。"
}
```

**レスポンスフィールド**:
- `success` (boolean): 処理成功フラグ
- `file` (object): アップロードされたファイル情報
  - `id` (string): Google DriveファイルID
  - `name` (string): ファイル名
  - `webViewLink` (string): Google Drive表示用URL
- `message` (string): 成功メッセージ

#### エラーコード

| HTTPステータス | エラーメッセージ | 説明 |
|---------------|-----------------|------|
| 400 | "ファイルとファイル名が必要です。" | 必須パラメータ不足 |
| 401 | "認証が切れました。再ログインしてください。" | Google認証失敗 |
| 403 | "Google Drive APIへのアクセス権限がありません。" | API権限不足 |
| 500 | "Google Driveへのアップロードに失敗しました。" | その他のエラー |

### 5. Google Drive パンくずリストAPI

**エンドポイント**: `GET /api/drive/breadcrumb`

**目的**: 指定フォルダのパンくずリスト（階層パス）を取得する

#### リクエストパラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| `id` | string | 任意 | フォルダID（デフォルト: "root"） |

#### レスポンス

**成功時（200 OK）**:
```json
[
  {
    "id": "root",
    "name": "マイドライブ"
  },
  {
    "id": "0BwwA4oUTeiV1TGRPeTVjaWRDY1E",
    "name": "業務"
  },
  {
    "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "name": "プロジェクト資料"
  }
]
```

**レスポンス形式**: フォルダ階層の配列（ルートから指定フォルダまで）
- `id` (string): フォルダID
- `name` (string): フォルダ名

#### エラーコード

| HTTPステータス | 説明 |
|---------------|------|
| 401 | Google認証失敗・トークン期限切れ |

## セキュリティ制約

### レート制限
- **バックエンドAPI**: WAFによる地理的制限（日本のみ）、レートベース制限
- **フロントエンドAPI**: Next.jsデフォルト制限

### ファイル制約
- **サポート形式**: `.xlsx`, `.xls` のみ
- **最大サイズ**: 20MB
- **禁止形式**: `.xlsm`（マクロ付きExcel）、実行可能ファイル

### 認証制約
- **JWT有効期限**: Google ID Token仕様に準拠
- **署名付きURL有効期限**: アップロード用60秒、ダウンロード用300秒
- **セッション有効期限**: Next-Auth.js設定に準拠

## 結論

本APIカタログは、Excel パスワード解除ツールの全5エンドポイントの仕様を網羅している。バックエンドはJWT認証とBot保護、フロントエンドはセッション認証を採用し、セキュリティと使いやすさを両立している。エラーハンドリングは日本語メッセージで統一され、適切な解決方法を提案する設計となっている。