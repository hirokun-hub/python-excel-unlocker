# セキュリティ強化実装ガイド

## 概要

このドキュメントは、Secure Excel Unlockアプリケーションに実装されたセキュリティ強化機能について説明します。

## 実装されたセキュリティ強化機能

### 1. S3バケットセキュリティ強化

#### パブリックアクセスブロック
```yaml
PublicAccessBlockConfiguration:
  BlockPublicAcls: true
  BlockPublicPolicy: true
  IgnorePublicAcls: true
  RestrictPublicBuckets: true
```

#### 暗号化設定
- **暗号化方式**: AES256 (Server-Side Encryption)
- **バケットキー**: 有効化（コスト最適化）

#### ライフサイクル設定
- **一時ファイル自動削除**: 1日後に自動削除
- **不完全マルチパートアップロード**: 1日後に自動削除

#### CORS設定の最適化
```yaml
AllowedOrigins:
  - "https://localhost:3000"
  - "https://localhost:3001"
  - "https://*.vercel.app"
AllowedHeaders:
  - "Content-Type"
  - "Content-Length"
  - "Authorization"
  - "X-Amz-Date"
  - "X-Amz-Security-Token"
```

### 2. S3バケットポリシー

#### Lambda関数からのアクセス制御
- GetUploadUrlFunction: PutObject権限のみ
- UnlockFunction: GetObject, PutObject, DeleteObject権限

#### 署名付きURLアクセス制御
- 署名の有効期限: 1時間以内
- HTTPS通信の強制

### 3. IAMロールの最小権限設定

#### GetUploadUrlFunction用ロール
```yaml
Policies:
  - PolicyName: S3AccessPolicy
    PolicyDocument:
      Statement:
        - Effect: Allow
          Action:
            - s3:PutObject
            - s3:PutObjectAcl
          Resource: !Sub "${ExcelBucket}/*"
```

#### UnlockFunction用ロール
```yaml
Policies:
  - PolicyName: S3AccessPolicy
    PolicyDocument:
      Statement:
        - Effect: Allow
          Action:
            - s3:GetObject
            - s3:PutObject
            - s3:DeleteObject
          Resource: !Sub "${ExcelBucket}/*"
```

### 4. ログからの機密情報除外

#### 実装された機能
- **署名付きURL**: クエリパラメータを`[REDACTED]`に置換
- **AWSクレデンシャル**: アクセスキー・シークレットキーをマスク
- **ファイル名**: 日本語文字を含む個人情報を`[FILENAME_REDACTED]`に置換
- **メールアドレス**: ローカル部を部分マスク（例: `u**r@example.com`）
- **パスワード**: 完全にアスタリスクに置換
- **エラーメッセージ**: 一時ファイルパス、S3パスをマスク

#### 使用例
```python
# ログ出力前にサニタイズ
sanitized_key = sanitize_for_log(s3_key)
logger.info(f"Processing file: {sanitized_key}")

# パスワードのサニタイズ
sanitized_password = sanitize_password_for_log(password)
logger.info(f"Trying password: {sanitized_password}")
```

### 5. 一時ファイルの確実な削除

#### セキュア削除機能
```python
def cleanup_local_file(file_path: str) -> bool:
    """
    ローカル一時ファイルを確実に削除する
    - ファイル内容をランダムデータで3回上書き
    - fsync()でディスクに強制書き込み
    - os.remove()でファイル削除
    """
```

#### S3オブジェクト削除
```python
def cleanup_s3_object(bucket: str, key: str) -> bool:
    """
    S3オブジェクトを削除する
    - delete_object APIを使用
    - エラーハンドリングとログ出力
    """
```

### 6. HTTPレスポンスセキュリティヘッダー

#### 実装されたヘッダー
```python
headers = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; ..."
}
```

## セキュリティ設定の確認方法

### 1. S3バケット設定の確認
```bash
# パブリックアクセスブロック確認
aws s3api get-public-access-block --bucket your-bucket-name

# 暗号化設定確認
aws s3api get-bucket-encryption --bucket your-bucket-name

# ライフサイクル設定確認
aws s3api get-bucket-lifecycle-configuration --bucket your-bucket-name
```

### 2. IAMロール権限の確認
```bash
# ロールポリシー確認
aws iam get-role-policy --role-name GetUploadUrlFunctionRole --policy-name S3AccessPolicy
aws iam get-role-policy --role-name UnlockFunctionRole --policy-name S3AccessPolicy
```

### 3. ログ出力の確認
```bash
# CloudWatch Logsでサニタイズされたログを確認
aws logs filter-log-events --log-group-name /aws/lambda/excel-unlock-function --filter-pattern "[REDACTED]"
```

## テスト

### セキュリティ機能のテスト実行
```bash
cd backend
source venv/bin/activate
python -m pytest tests/unit/test_utils.py::TestSecurityFeatures -v
```

### テスト項目
- ログサニタイズ機能
- 一時ファイル削除機能
- S3オブジェクト削除機能
- セキュリティヘッダー設定
- メールアドレス・パスワード・ファイル名のマスク処理

## 運用時の注意事項

### 1. ログ監視
- CloudWatch Logsで機密情報の漏洩がないか定期確認
- `[REDACTED]`パターンでフィルタリング

### 2. S3バケット監視
- 一時ファイルが適切に削除されているか確認
- 不正アクセスの監視

### 3. IAM権限の定期見直し
- 最小権限の原則に従った権限設定の維持
- 不要な権限の削除

## 今後の改善予定

### Phase 3での追加セキュリティ強化
- AWS CloudTrailによる操作ログ記録
- AWS Configによる設定変更監視
- AWS GuardDutyによる脅威検出
- VPCエンドポイントによるネットワーク分離

## 関連ドキュメント

- [要件定義書](../.kiro/specs/secure-excel-unlock/requirements.md)
- [設計書](../.kiro/specs/secure-excel-unlock/design.md)
- [認証・API統合ガイド](./authentication-integration-guide.md)
- [ローカル開発環境ガイド](./local-development-guide.md)