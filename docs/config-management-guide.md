# 設定管理ガイド

## 概要

Excel解除ツールの設定管理システムは、初心者でも簡単に設定を完了できるように設計されています。プレースホルダーの自動検出・修正、セキュリティ強度チェック、対話式ウィザードなどの機能を提供します。

## 🎯 主な機能

### ✅ 自動化機能
- **プレースホルダー自動検出**: YOUR_* パターンの未設定項目を自動検出
- **セキュリティキー自動生成**: JWT/セッションシークレットの安全な自動生成
- **設定検証**: JSON Schema + カスタムルールによる包括的検証
- **環境変数自動生成**: 設定ファイルから各環境用の環境変数を自動生成

### 🧙‍♂️ 初心者サポート
- **対話式ウィザード**: 質問に答えるだけで設定完了
- **わかりやすい説明**: 専門用語を使わない日本語説明
- **安心メッセージ**: 「壊れません」「元に戻せます」の明示
- **段階的ガイダンス**: ステップバイステップの案内

## 🚀 クイックスタート

### 1. 超簡単セットアップ（推奨）

```bash
# 1つのコマンドで設定完了
./scripts/setup-easy-config.sh
```

このスクリプトは以下を自動実行します：
- Python環境の確認・セットアップ
- 設定ファイルの作成
- 対話式ウィザードの起動
- 設定検証テストの実行

### 2. 個別コマンドでの設定

```bash
# 仮想環境のアクティベート（macOS）
source venv/bin/activate

# 対話式ウィザード
python3 scripts/config_manager.py wizard

# 自動修正のみ（シークレット生成）
python3 scripts/config_manager.py auto-fix

# 設定検証
python3 scripts/config_manager.py verify
```

## 📋 利用可能なコマンド

### 基本コマンド

```bash
# ヘルプ表示
python3 scripts/config_manager.py --help

# 設定ファイル作成
python3 scripts/config_manager.py create

# 設定検証
python3 scripts/config_manager.py validate

# 環境変数生成
python3 scripts/config_manager.py generate-env development --format dotenv
```

### 高度なコマンド

```bash
# プレースホルダー自動修正（対話式）
python3 scripts/config_manager.py auto-fix

# プレースホルダー自動修正（非対話式）
python3 scripts/config_manager.py auto-fix --non-interactive

# 初心者向けウィザード
python3 scripts/config_manager.py wizard

# 包括的検証テスト
python3 scripts/config_manager.py verify

# 設定ファイルバックアップ
python3 scripts/config_manager.py backup

# 設定ファイル暗号化
python3 scripts/config_manager.py encrypt
```

## 🔧 設定項目の詳細

### Google OAuth設定
```json
{
  "google": {
    "clientId": "123456789-abc...xyz.apps.googleusercontent.com",
    "clientSecret": "GOCSPX-abcdefghijklmnopqrstuvwxyz",
    "redirectUri": "https://your-domain.com/api/auth/callback/google"
  }
}
```

**取得方法:**
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成または選択
3. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
4. アプリケーションの種類：「ウェブアプリケーション」
5. 承認済みのリダイレクト URI を設定

### セキュリティ設定
```json
{
  "security": {
    "allowedUsers": [
      "user1@company.com",
      "user2@company.com"
    ],
    "jwtSecret": "自動生成される64文字のランダム文字列",
    "sessionSecret": "自動生成される64文字のランダム文字列"
  }
}
```

**重要なポイント:**
- `allowedUsers`: 実際のユーザーのメールアドレスを設定
- `jwtSecret`/`sessionSecret`: 自動生成を推奨（最も安全）
- 本番環境では異なるシークレットを使用

### AWS設定
```json
{
  "aws": {
    "region": "ap-northeast-1",
    "s3": {
      "bucketName": "your-unique-bucket-name",
      "corsOrigin": "https://your-domain.com"
    },
    "lambda": {
      "stackName": "excel-unlocker-api-prod",
      "timeout": 300,
      "memorySize": 1024
    }
  }
}
```

## 🛡️ セキュリティ機能

### プレースホルダー検出
システムは以下のパターンを自動検出します：
- `YOUR_*` で始まる値
- `example.com` ドメインのメールアドレス
- `REPLACE_*`, `CHANGE_*`, `UPDATE_*` パターン

### セキュリティ強度チェック
- JWT/セッションシークレットの長さ（32文字以上推奨）
- 弱いパスワードパターンの検出
- 本番環境での同一シークレット使用の警告

### 自動生成シークレット
```python
# 64文字の安全なランダム文字列を生成
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
secret = ''.join(secrets.choice(alphabet) for _ in range(64))
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. Python環境エラー
```bash
# エラー: ModuleNotFoundError: No module named 'jsonschema'
# 解決方法: 仮想環境を使用
python3 -m venv venv
source venv/bin/activate
pip install jsonschema cryptography
```

#### 2. プレースホルダーが残っている
```bash
# 問題確認
python3 scripts/config_manager.py verify

# 自動修正
python3 scripts/config_manager.py auto-fix

# 手動修正が必要な場合
python3 scripts/config_manager.py wizard
```

#### 3. 設定ファイルが壊れた
```bash
# バックアップから復元
ls config-backup/
cp config-backup/setup-config.YYYYMMDD_HHMMSS.json setup-config.json

# または新規作成
python3 scripts/config_manager.py create
```

#### 4. 環境変数生成エラー
```bash
# 設定ファイル検証
python3 scripts/config_manager.py validate

# 基本的な環境変数生成
python3 scripts/config_manager.py generate-env development --format json
```

## 📊 検証テストの詳細

### 実行される検証項目

1. **設定ファイル存在確認**
   - setup-config.json の存在確認

2. **JSON形式確認**
   - 有効なJSON形式かチェック

3. **プレースホルダー確認**
   - 未設定項目の検出と報告

4. **セキュリティ強度確認**
   - シークレットの長さと強度チェック

5. **環境変数生成テスト**
   - 各環境の環境変数生成可能性確認

6. **全体検証**
   - JSON Schema + カスタムルール検証

### 検証結果の解釈

```bash
# 全て正常
🎉 全ての検証テストに合格しました！
✅ 設定は完璧です。デプロイメントを開始できます。

# 問題あり
⚠️  一部の検証テストで問題が見つかりました
💡 上記の問題を修正してから再度テストを実行してください
```

## 🔄 バックアップと復元

### 自動バックアップ
設定変更時に自動的にバックアップが作成されます：
```
config-backup/setup-config.20250922_164939.json
```

### 手動バックアップ
```bash
python3 scripts/config_manager.py backup --dir my-backup
```

### 復元方法
```bash
# バックアップファイル一覧
ls config-backup/

# 復元
cp config-backup/setup-config.YYYYMMDD_HHMMSS.json setup-config.json
```

## 🔐 暗号化機能

### 設定ファイルの暗号化
```bash
# 暗号化
python3 scripts/config_manager.py encrypt

# 復号化
python3 scripts/config_manager.py decrypt setup-config.json.encrypted
```

暗号化キーは `.config-encryption-key` に保存されます。

## 💡 ベストプラクティス

### 初心者向け
1. **ウィザードを使用**: `python3 scripts/config_manager.py wizard`
2. **自動生成を活用**: シークレットは自動生成が最も安全
3. **定期的な検証**: `python3 scripts/config_manager.py verify`

### 上級者向け
1. **環境別設定**: 開発・ステージング・本番で異なる設定
2. **暗号化**: 機密性の高い環境では暗号化を使用
3. **バックアップ**: 重要な変更前にバックアップ作成

### セキュリティ
1. **実際のメールアドレス**: example.com は使用しない
2. **強力なシークレット**: 32文字以上のランダム文字列
3. **定期的な更新**: シークレットの定期的な更新

## 📞 サポート

### 困ったときは
1. **検証テスト実行**: `python3 scripts/config_manager.py verify`
2. **ドキュメント確認**: このガイドと `docs/` フォルダ
3. **バックアップ確認**: `config-backup/` フォルダ
4. **管理者に連絡**: サポート担当者まで

### 関連ドキュメント
- [統合セットアップガイド](integrated-setup-guide.md)
- [初心者向け完全セットアップガイド](beginner-complete-setup-guide.md)
- [Python環境トラブルシューティング](python-environment-troubleshooting.md)