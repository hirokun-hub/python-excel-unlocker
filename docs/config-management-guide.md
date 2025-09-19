# 設定情報管理システム ガイド

## 概要

Secure Excel Unlockプロジェクトの設定情報管理システムは、機密情報を安全に管理し、環境別の設定を効率的に運用するためのツールセットです。

## 主な機能

- **設定ファイル管理**: JSON形式での統一設定管理
- **環境別設定**: development/staging/production環境の分離
- **機密情報保護**: 暗号化機能と.gitignore除外設定
- **設定検証**: JSON Schemaによる設定値の検証
- **環境変数生成**: 各種フォーマットでの環境変数出力
- **インポート・エクスポート**: 設定の移行と共有機能
- **バックアップ**: 設定変更履歴の保持

## ファイル構成

```
├── setup-config.example.json    # 設定ファイルテンプレート
├── setup-config.json           # 実際の設定ファイル（機密情報含む）
├── config-schema.json          # 設定ファイルのスキーマ定義
├── scripts/
│   ├── config_manager.py       # 設定管理メインスクリプト
│   ├── config_import_export.py # インポート・エクスポート機能
│   ├── setup-config-manager.sh # Bashラッパースクリプト
│   └── setup-with-config-management.sh # 統合セットアップスクリプト
└── config-backup/              # 設定バックアップディレクトリ
```

## クイックスタート

### 1. 設定ファイルの初期化

```bash
# 設定ファイルのテンプレートを作成
./scripts/setup-config-manager.sh init
```

### 2. 設定ファイルの編集

`setup-config.json` を編集して、以下の情報を設定します：

- **Google OAuth**: クライアントIDとシークレット
- **AWS設定**: S3バケット名、リージョン、プロファイル
- **セキュリティ**: 許可ユーザー、JWT/セッションシークレット
- **Vercel設定**: プロジェクト名、ドメイン

### 3. 設定の検証

```bash
# 設定ファイルの検証
./scripts/setup-config-manager.sh validate
```

### 4. 環境変数の生成

```bash
# 開発環境の環境変数を生成
./scripts/setup-config-manager.sh generate-env development

# 本番環境の環境変数をファイル出力
./scripts/setup-config-manager.sh generate-env production bash prod.env
```

### 5. 統合セットアップの実行

```bash
# 開発環境の完全セットアップ
./scripts/setup-with-config-management.sh development

# 本番環境のセットアップ + Vercelデプロイ
./scripts/setup-with-config-management.sh production true
```

## 詳細な使用方法

### 設定ファイルの構造

```json
{
  "version": "1.0.0",
  "environments": {
    "development": {
      "aws": {
        "region": "ap-northeast-1",
        "s3": {
          "bucketName": "excel-unlock-dev-bucket",
          "corsOrigin": "http://localhost:3000"
        },
        "lambda": {
          "stackName": "excel-unlocker-api-dev"
        }
      },
      "google": {
        "clientId": "YOUR_GOOGLE_CLIENT_ID",
        "clientSecret": "YOUR_GOOGLE_CLIENT_SECRET"
      },
      "security": {
        "allowedUsers": ["user@example.com"],
        "jwtSecret": "YOUR_JWT_SECRET"
      }
    }
  },
  "features": {
    "googleDriveIntegration": true,
    "multiFileProcessing": true
  }
}
```

### コマンドリファレンス

#### 基本コマンド

```bash
# 設定ファイルの初期化
./scripts/setup-config-manager.sh init

# 設定ファイルの検証
./scripts/setup-config-manager.sh validate

# 環境変数の生成（標準出力）
./scripts/setup-config-manager.sh generate-env <environment>

# 環境変数の生成（ファイル出力）
./scripts/setup-config-manager.sh generate-env <environment> <format> <output_file>
```

#### バックアップ・暗号化

```bash
# 設定ファイルのバックアップ
./scripts/setup-config-manager.sh backup

# 設定ファイルの暗号化
./scripts/setup-config-manager.sh encrypt

# 設定ファイルの復号化
./scripts/setup-config-manager.sh decrypt <encrypted_file>
```

#### インポート・エクスポート

```bash
# 環境設定のエクスポート
python3 scripts/config_import_export.py export-env production prod-config.json

# 環境設定のインポート
python3 scripts/config_import_export.py import-env staging-config.json staging

# 機密情報テンプレートのエクスポート
python3 scripts/config_import_export.py export-secrets production secrets-template.json

# 機密情報のインポート
python3 scripts/config_import_export.py import-secrets secrets.json production
```

#### 環境比較

```bash
# 環境設定の比較
python3 scripts/config_import_export.py compare development production

# 比較結果をファイル出力
python3 scripts/config_import_export.py compare development production --output comparison.json
```

### 環境変数の出力フォーマット

#### Bash形式

```bash
#!/bin/bash
export AWS_REGION="ap-northeast-1"
export S3_BUCKET_NAME="excel-unlock-dev-bucket"
export GOOGLE_CLIENT_ID="your-client-id"
```

#### .env形式

```
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=excel-unlock-dev-bucket
GOOGLE_CLIENT_ID=your-client-id
```

#### JSON形式

```json
{
  "AWS_REGION": "ap-northeast-1",
  "S3_BUCKET_NAME": "excel-unlock-dev-bucket",
  "GOOGLE_CLIENT_ID": "your-client-id"
}
```

## セキュリティ考慮事項

### 機密情報の保護

1. **Gitignore設定**: `setup-config.json` は自動的に除外されます
2. **暗号化機能**: 機密情報を含む設定ファイルを暗号化できます
3. **バックアップ**: 設定変更前に自動バックアップが作成されます
4. **アクセス制御**: 設定ファイルのファイル権限を適切に設定してください

### 推奨セキュリティ設定

```bash
# 設定ファイルの権限を制限
chmod 600 setup-config.json

# 暗号化キーの権限を制限
chmod 600 .config-encryption-key

# バックアップディレクトリの権限を制限
chmod 700 config-backup/
```

## トラブルシューティング

### よくある問題

#### 1. 設定ファイルの検証エラー

```bash
❌ JSON Schema検証エラー: 'clientSecret' is a required property
```

**解決方法**: 必須フィールドが不足しています。設定ファイルを確認してください。

#### 2. 環境変数生成エラー

```bash
❌ 環境 'production' が設定ファイルに存在しません
```

**解決方法**: 指定した環境が設定ファイルに定義されているか確認してください。

#### 3. 暗号化キーが見つからない

```bash
❌ 暗号化キーが見つかりません: .config-encryption-key
```

**解決方法**: 暗号化機能を初回使用時にキーが自動生成されます。キーファイルを削除した場合は再暗号化が必要です。

### ログとデバッグ

設定管理スクリプトは詳細なログを出力します：

- ✅ 成功メッセージ（緑色）
- ⚠️ 警告メッセージ（黄色）
- ❌ エラーメッセージ（赤色）
- 📍 情報メッセージ（青色）

## 高度な使用方法

### カスタム設定の追加

設定ファイルに独自の設定項目を追加する場合：

1. `config-schema.json` にスキーマ定義を追加
2. `setup-config.example.json` にテンプレートを追加
3. `config_manager.py` の環境変数生成ロジックを更新

### 新しい環境の追加

staging2環境を追加する例：

```json
{
  "environments": {
    "staging2": {
      "description": "第2ステージング環境",
      "aws": { ... },
      "google": { ... },
      "security": { ... }
    }
  }
}
```

### 設定の継承

環境間で共通設定を継承する場合は、インポート・エクスポート機能を使用：

```bash
# 本番設定をベースにステージング設定を作成
python3 scripts/config_import_export.py export-env production base-config.json
python3 scripts/config_import_export.py import-env base-config.json staging2 --merge merge
```

## 統合ワークフロー

### 開発フロー

1. **初期設定**: `setup-config-manager.sh init`
2. **設定編集**: `setup-config.json` の編集
3. **検証**: `setup-config-manager.sh validate`
4. **開発環境構築**: `setup-with-config-management.sh development`
5. **テスト**: ローカル環境での動作確認

### デプロイフロー

1. **設定バックアップ**: `setup-config-manager.sh backup`
2. **本番設定更新**: 本番環境用の設定値を更新
3. **検証**: `setup-config-manager.sh validate`
4. **本番デプロイ**: `setup-with-config-management.sh production true`
5. **動作確認**: デプロイ後の動作確認

### チーム共有フロー

1. **設定エクスポート**: `config_import_export.py export-env`
2. **機密情報分離**: 機密情報テンプレートの作成
3. **設定共有**: 非機密部分のみをチームで共有
4. **個別設定**: 各メンバーが機密情報を個別設定

## まとめ

設定情報管理システムにより、以下の利点が得られます：

- **セキュリティ向上**: 機密情報の適切な管理
- **運用効率化**: 環境別設定の自動化
- **設定品質**: スキーマ検証による設定ミス防止
- **チーム協力**: 設定の共有と移行の簡素化
- **監査対応**: 設定変更履歴の保持

詳細な技術情報や追加機能については、各スクリプトのヘルプオプション（`--help`）を参照してください。