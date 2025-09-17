# 統合テスト

このディレクトリには、フロントエンド・バックエンド間のAPI統合テスト、実際のS3との連携テスト、ファイルアップロード・ダウンロードのE2Eテストが含まれています。

## テスト構成

- `api/` - API統合テスト
- `s3/` - S3連携テスト  
- `e2e/` - エンドツーエンドテスト
- `fixtures/` - テスト用ファイル
- `utils/` - テスト用ユーティリティ

## 実行方法

```bash
# 全統合テスト実行
npm run test:integration

# API統合テストのみ
npm run test:integration:api

# S3連携テストのみ
npm run test:integration:s3

# E2Eテストのみ
npm run test:integration:e2e
```

## 前提条件

- AWS CLI設定済み
- S3バケット作成済み
- Lambda関数デプロイ済み
- 環境変数設定済み