# Secure Excel Unlock - 設計書

## 概要

本設計書は、パスワード付きExcelファイル解除Webアプリケーション「Secure Excel Unlock」のシステム設計を定義します。要件定義書で定められた機能要件と非機能要件を満たすアーキテクチャを提示します。

## アーキテクチャ概要

### システム構成

```mermaid
graph TB
    subgraph "Frontend (Vercel)"
        UI[Next.js + React + shadcn/ui]
        Auth[Auth.js + Google OAuth]
    end
    
    subgraph "AWS Cloud"
        subgraph "API Layer"
            APIGW[API Gateway]
            Lambda[AWS Lambda]
        end
        
        subgraph "Storage"
            S3[Amazon S3]
        end
        
        subgraph "Security"
            IAM[IAM Roles]
            CW[CloudWatch Logs]
        end
    end
    
    subgraph "External"
        Google[Google OAuth Provider]
        User[End Users]
    end
    
    User --> UI
    UI --> Auth
    Auth --> Google
    UI --> APIGW
    APIGW --> Lambda
    Lambda --> S3
    Lambda --> CW
    IAM --> Lambda
    IAM --> S3
```

### アーキテクチャの特徴

1. **サーバーレス構成**: AWS Lambda（機能別分割：getUploadUrl, unlock）によるコスト効率的な実行
2. **フロントエンド分離**: Vercelでの独立デプロイ
3. **API呼び出しポリシー**: 本番環境ではフロントエンドから API Gateway を**直接**呼び出す。Next.js の API ルートは**開発・デバッグ用途のみ**とし、プロダクション経路には使用しない。
4. **セキュアなファイル転送**: S3署名付きURLによる直接転送（Upload 60秒、Download 300秒）
5. **認証統合**: Auth.js（旧 NextAuth.js）によるGoogle OAuth認証

## コンポーネント設計

### フロントエンド (Next.js)

#### 主要コンポーネント
- **AuthProvider**: Google OAuth認証の管理
- **FileUpload**: ドラッグ&ドロップファイルアップロード
- **PasswordForm**: パスワード入力フォーム（第一・第二候補）
- **ProcessingStatus**: 処理状況の表示
- **DownloadManager**: 解除済みファイルのダウンロード管理

#### 技術スタック
- **Framework**: Next.js 15.4 (App Router)
- **UI Library**: shadcn/ui + Radix UI
- **Authentication**: Auth.js（旧 NextAuth.js）
- **Form Validation**: zod + react-hook-form
- **State Management**: React hooks + Context API

### バックエンド (AWS Lambda)

#### Lambda 分割ポリシー
Lambda は機能単位で分割する（例：getUploadUrl／unlock）。これにより IAM 権限の最小化、障害切り分け、メトリクス計測が明瞭になる。

#### API エンドポイント

##### 1. **API Gateway 経由の対応エンドポイント（例：POST https://{api-id}.execute-api.{region}.amazonaws.com/prod/getUploadUrl）**
**目的**: S3への安全なファイルアップロード用署名付きURL生成

**リクエスト**:
```json
{
  "fileName": "example.xlsx",
  "fileSize": 1024000,
  "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

**レスポンス**:
```json
{
  "uploadUrl": "https://s3.amazonaws.com/bucket/key?signature=...",
  "fileKey": "uploads/uuid-filename.xlsx",
  "expiresIn": 60
}
```

##### 2. **API Gateway 経由の対応エンドポイント（例：POST https://{api-id}.execute-api.{region}.amazonaws.com/prod/unlock）**
**目的**: パスワード付きExcelファイルの解除処理

**リクエスト**:
```json
{
  "fileKey": "uploads/uuid-filename.xlsx",
  "passwords": ["password1", "password2"]
}
```

**レスポンス**:
```json
{
  "success": true,
  "downloadUrl": "https://s3.amazonaws.com/bucket/unlocked/key?signature=...",
  "fileName": "unlocked-example.xlsx",
  "expiresIn": 300,
  "processingTime": 2.5
}
```

**エラーレスポンス**:
```json
{
  "success": false,
  "error": "password_incorrect",
  "message": "両方のパスワードで解除できませんでした",
  "suggestion": "別のパスワード候補をお試しください"
}
```

#### 処理フロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Frontend as Next.js
    participant API as API Gateway
    participant Lambda as AWS Lambda
    participant S3 as Amazon S3
    
    User->>Frontend: ファイル選択 + パスワード入力
    Frontend->>API: GET /api/get-upload-url
    API->>Lambda: 署名付きURL生成要求
    Lambda->>S3: 署名付きURL生成
    Lambda-->>Frontend: uploadUrl返却
    
    Frontend->>S3: ファイル直接アップロード
    S3-->>Frontend: アップロード完了
    
    Frontend->>API: POST /api/unlock
    API->>Lambda: 解除処理開始
    Lambda->>S3: 暗号化ファイル取得
    Lambda->>Lambda: msoffcrypto-toolで解除
    Lambda->>S3: 解除済みファイル保存
    Lambda->>S3: 署名付きダウンロードURL生成
    Lambda-->>Frontend: downloadUrl返却
    
    Frontend->>User: ダウンロードリンク表示
    User->>S3: ファイルダウンロード
```

### データモデル

#### ファイル処理状態
```typescript
interface ProcessingStatus {
  fileKey: string;
  fileName: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  error?: ErrorInfo;
  downloadUrl?: string;
  processingTime?: number;
}

interface ErrorInfo {
  code: 'password_incorrect' | 'unsupported_format' | 'timeout' | 'file_corrupted';
  message: string;
  suggestion: string;
}
```

#### 認証情報
```typescript
interface UserSession {
  id: string;
  email: string;
  name: string;
  image?: string;
  allowedDomains: string[];
  permissions: string[];
}
```

## セキュリティ設計

### 認証・認可

#### Google OAuth 2.0 + OIDC
- **プロバイダー**: Google OAuth 2.0
- **フロー**: Authorization Code with PKCE
- **トークン管理**: httpOnly Cookie + Refresh Token Rotation
- **セッション**: 24時間有効期限

#### アクセス制御
```typescript
// 許可されたユーザーリスト（環境変数）
const ALLOWED_USERS = [
  "user1@nsc-company.com",
  "user2@nsc-company.com"
];

// ミドルウェアでの認証チェック
async function authenticateUser(request: Request) {
  const session = await getSession(request);
  if (!session || !ALLOWED_USERS.includes(session.user.email)) {
    throw new UnauthorizedError();
  }
  return session;
}
```

### データ保護

#### ファイル暗号化・保護
- **転送時暗号化**: HTTPS/TLS 1.3
- **保存時暗号化**: S3 Server-Side Encryption (SSE-S3)
- **アクセス制御**: S3バケットポリシー + IAM最小権限
- **データ保持**: 処理完了後即時削除

#### 署名付きURL設定
Pre-signed URL の有効期限は Upload 60秒、Download 300秒とする。全ドキュメントでこの値に統一し、変更時は一括で更新する。

```python
def generate_presigned_url(bucket: str, key: str, expiration: int = 60):
    return s3_client.generate_presigned_url(
        'put_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expiration,  # Upload: 60秒, Download: 300秒
        HttpMethod='PUT'
    )
```

### ログ・監査

#### ログ設計
```json
{
  "timestamp": "2025-01-17T10:30:00Z",
  "event": "unlock_attempt",
  "outcome": "success",
  "duration_ms": 2500,
  "file_ext": "xlsx",
  "size_class": "1-10MB",
  "user_id": "hashed_user_id",
  "request_id": "uuid",
  "app_version": "v1.0.0"
}
```

**ログに含めない情報**:
- 平文パスワード
- ファイル名・内容
- 個人識別情報

## エラーハンドリング

### エラー分類と対応

#### 1. パスワード関連エラー
```typescript
const PASSWORD_ERRORS = {
  password_incorrect: {
    message: "入力されたパスワードでは解除できませんでした",
    suggestion: "別のパスワード候補をお試しください",
    action: "retry"
  }
};
```

#### 2. ファイル関連エラー
```typescript
const FILE_ERRORS = {
  unsupported_format: {
    message: "サポートされていないファイル形式です",
    suggestion: ".xlsx または .xls ファイルを選択してください",
    action: "reselect"
  },
  file_corrupted: {
    message: "ファイルが破損している可能性があります",
    suggestion: "元のファイルを確認して再度お試しください",
    action: "reselect"
  }
};
```

#### 3. システムエラー
```typescript
const SYSTEM_ERRORS = {
  timeout: {
    message: "処理がタイムアウトしました",
    suggestion: "しばらく待ってから再度お試しください",
    action: "retry"
  },
  service_unavailable: {
    message: "サービスが一時的に利用できません",
    suggestion: "しばらく待ってから再度お試しください",
    action: "wait"
  }
};
```

### リトライ機構
```typescript
async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      const delay = baseDelay * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## パフォーマンス最適化

### フロントエンド最適化

#### 1. コード分割
```typescript
// 動的インポートによるコード分割
const FileUpload = dynamic(() => import('./FileUpload'), {
  loading: () => <Skeleton className="h-32 w-full" />
});
```

#### 2. キャッシュ戦略
```typescript
// SWRによるデータキャッシュ
const { data, error } = useSWR('/api/status', fetcher, {
  refreshInterval: 1000,
  revalidateOnFocus: false
});
```

### バックエンド最適化

#### 1. Lambda最適化
```python
# コールドスタート対策
import json
import boto3
from msoffcrypto import OfficeFile

# グローバル変数でクライアント初期化
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # 処理ロジック
    pass
```

#### 2. 並列処理
```python
import asyncio
import concurrent.futures

async def process_multiple_files(file_keys: list, passwords: list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [
            executor.submit(process_single_file, key, passwords)
            for key in file_keys
        ]
        results = await asyncio.gather(*tasks)
    return results
```

## テスト戦略

### 差分テスト戦略

#### コンポーネント境界とテスト範囲
```mermaid
graph TB
    subgraph "Frontend Components"
        UI[UI Components]
        API_ROUTES[API Routes]
        AUTH[Authentication]
        UTILS[Utilities]
    end
    
    subgraph "Backend Components"
        LAMBDA[Lambda Functions]
        S3_OPS[S3 Operations]
        EXCEL[Excel Processing]
    end
    
    subgraph "Infrastructure"
        WORKFLOWS[GitHub Actions]
        CONFIG[Configuration Files]
    end
    
    UI --> API_ROUTES
    API_ROUTES --> LAMBDA
    LAMBDA --> S3_OPS
    LAMBDA --> EXCEL
```

#### 変更検出基準
| 変更パス | テスト範囲 | 実行条件 |
|---------|-----------|----------|
| `frontend/src/components/` | フロントエンド単体テスト | 常時 |
| `frontend/src/app/api/` | API統合テスト + フロントエンド | 常時 |
| `backend/src/` | バックエンド単体テスト + API統合 | 常時 |
| `frontend/e2e/` | E2Eテスト | PR時のみ |
| `.github/workflows/` | ワークフロー検証 | 常時 |
| `template.yaml` | インフラテスト | main ブランチ |

#### テスト実行マトリックス
```yaml
# 開発段階別テスト戦略
stages:
  development:
    - unit_tests: always
    - integration_tests: on_api_changes
    - e2e_tests: manual_trigger
  
  pull_request:
    - unit_tests: always
    - integration_tests: always
    - e2e_tests: always
    - performance_tests: on_backend_changes
  
  main_branch:
    - all_tests: always
    - deployment_tests: always
    - security_scans: always
```

### 単体テスト
- **フロントエンド**: Jest + React Testing Library
- **バックエンド**: pytest + moto (AWS mocking)
- **カバレッジ目標**: 80%以上

### 統合テスト
- **API テスト**: Postman/Newman
- **E2E テスト**: Playwright
- **認証フロー**: 実際のGoogle OAuth環境

### パフォーマンステスト
- **負荷テスト**: Artillery.js
- **目標値**: P95 < 8秒、同時実行50

### AI向けアーティファクト生成

#### 現在の状況（2024-12-28時点）
**✅ 成功している項目**:
- セキュリティスキャン結果（bandit）: 正常アップロード
- バックエンドテスト結果（pytest）: 8/8パス、92%カバレッジ、正常アップロード
- actions/upload-artifact@v4への更新: 完了

**❌ 修正が必要な項目**:
- フロントエンドテスト結果のアップロード失敗
  ```
  No files were found with the provided path: coverage/
  junit.xml. Make sure you have correctly specified the path.
  ```
- Jest設定でカバレッジレポートとJUnitレポートが生成されていない
- プロジェクト構造情報を含むAI分析用統合データが不足

#### 包含情報（修正版）
```yaml
ai_package_contents:
  test_results:
    - security_scan_results.json ✅
    - backend_coverage.json ✅
    - frontend_coverage/ ❌ (要修正)
    - junit.xml ❌ (要修正)
  
  project_metadata: ❌ (未実装)
    - file_structure.txt
    - dependency_tree.json
    - git_history.txt
    - change_summary.md
  
  configuration: ❌ (未実装)
    - package.json
    - requirements.txt
    - template.yaml
    - workflow_configs/
  
  analysis_data: ❌ (未実装)
    - performance_metrics.json
    - code_quality_reports/
```

#### 緊急修正が必要な項目
1. **Jest設定の修正**: カバレッジとJUnitレポート生成
2. **GitHub Actions設定の修正**: フロントエンドアーティファクトパス
3. **プロジェクト構造情報の追加**: AI分析用メタデータ生成

#### 生成タイミング
- **毎回**: 基本的なテスト結果とプロジェクト構造
- **PR時**: 変更差分と影響分析
- **main更新時**: 完全なプロジェクト状態スナップショット

## 運用・監視

### メトリクス収集
```python
# CloudWatch カスタムメトリクス
def put_custom_metric(metric_name: str, value: float, unit: str = 'Count'):
    cloudwatch.put_metric_data(
        Namespace='SecureExcelUnlock',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }]
    )
```

### アラート設定
- **エラー率**: 5%以上で警告
- **レスポンス時間**: P95 > 10秒で警告
- **Lambda エラー**: 連続3回失敗で警告

## デプロイメント

### CI/CD パイプライン
```yaml
# GitHub Actions
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy Lambda
        run: |
          sam build
          sam deploy --no-confirm-changeset
  
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: vercel --prod
```

### 環境管理
- **開発環境**: 個人AWS アカウント
- **本番環境**: 同一アカウント（別リソース）
- **設定管理**: AWS Systems Manager Parameter Store

## 実装済み機能

### ✅ 完了済み機能
- **Google Drive 連携**: フォルダ選択、個別・一括保存機能
- **複数ファイル一括処理UI**: ドラッグ&ドロップ、並列処理対応
- **認証システム**: Google OAuth 2.0 + セッション管理
- **レスポンシブUI**: shadcn/ui ベースの統一デザイン

### 将来拡張計画

#### Phase 2: 追加機能
- 処理履歴機能
- 管理者ダッシュボード
- ファイル形式拡張（.xlsm対応等）

#### Phase 3: スケール対応
- 非同期ジョブ処理 (SQS + Step Functions)
- マルチリージョン対応
- CDN導入 (CloudFront)

この設計書に基づいて、要件定義書で定められた全ての機能要件と非機能要件を満たすシステムを構築します。