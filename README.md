# Secure Excel Unlock

パスワード付きExcelファイルを安全かつ効率的に解除するWebアプリケーションです。

## 概要

- **フロントエンド**: Next.js + Auth.js（Google OAuth認証）
- **バックエンド**: AWS Lambda + API Gateway + S3
- **認証**: Google OAuth 2.0 + 招待制アクセス制御
- **処理**: msoffcrypto-toolによるExcelパスワード解除

## 主要機能

- 🔐 **パスワード解除**: 複数パスワード候補での自動解除
- 👥 **招待制認証**: Google OAuth + 管理者による許可ユーザー制御
- 📁 **Google Drive連携**: 解除済みファイルの直接保存
- 📱 **マルチデバイス対応**: iPhone/Android/PC/Mac対応
- 🔒 **セキュア**: S3署名付きURL + HTTPS通信

## プロジェクト構成

- `backend/`: AWS Lambda関数のソースコード
- `frontend/`: Next.js Webアプリケーション
- `docs/`: プロジェクトドキュメント
- `scripts/`: ユーティリティスクリプト
- `.kiro/specs/`: 要件定義・設計・実装計画

## 認証・セキュリティ

### Google OAuth認証
- Google アカウントによるセキュアなログイン
- 管理者による招待制アクセス制御
- セッション管理とトークン更新

### バックエンド認証
- フロントエンドからのAPI呼び出し時に`X-User-Email`ヘッダーで認証
- 環境変数による許可ユーザーリスト管理
- メールアドレス正規化による柔軟な認証

### ユーザー管理機能 🆕
- **自動化スクリプト**: ユーザー追加・削除・一覧表示の自動化
- **緊急時対応**: セキュリティインシデント時の即座対応機能
- **アクセステスト**: ユーザー権限の動作確認機能
- **監査レポート**: 定期的なユーザー監査とレポート生成
- **包括的ログ**: 全操作の詳細ログ記録と履歴管理

## 主要機能

### Excel解除機能
- パスワード付きExcelファイル（.xlsx/.xls）の解除
- 複数パスワード候補での自動試行
- リアルタイム処理状況表示

### Google Drive連携
- 解除済みファイルの直接保存
- **フォルダ選択機能**:
  1. 処理完了後、「Google Drive保存先」バーが表示
  2. 「保存先を選ぶ」ボタンをクリック
  3. フォルダピッカーでGoogle Driveフォルダを選択
  4. 「このフォルダを選ぶ」で決定
- ブラウザに保存先を記憶（次回以降も使用可能）
- フォルダ未選択時は「マイドライブ」ルートに保存

### セキュリティ機能
- S3署名付きURLによる安全なファイル転送
- 処理完了後の自動ファイル削除
- HTTPS通信の強制

## 開発・デプロイ

### 初回セットアップ

#### 🚀 自動化セットアップ（推奨）
```bash
# 手作業最小化の完全自動化（事前準備10分 + 自動処理5分）
./scripts/setup-complete-automation.sh
```

#### 📋 従来の手動セットアップ
```bash
# 前提条件確認・環境変数設定・初回デプロイ
./scripts/setup-deployment.sh
```

### ローカル開発
```bash
# バックエンドAPI起動
sam local start-api --port 3001

# フロントエンド起動
cd frontend
npm run dev

# 統合テスト実行
./tests/run-integration-tests.sh all
```

### 段階的デプロイ

#### 環境別デプロイ
```bash
# 開発環境
./scripts/deploy.sh development all

# ステージング環境  
./scripts/deploy.sh staging all

# 本番環境（確認プロンプト付き）
./scripts/deploy.sh production all
```

#### GitHub Actions（推奨）
1. **自動デプロイ**:
   - `develop`ブランチ → 開発環境
   - `main`ブランチ → ステージング環境

2. **手動デプロイ**:
   - Actions タブ → "Deploy Full Stack" → 環境選択 → 実行

#### 環境構成
| 環境 | 用途 | デプロイ方法 | 承認 |
|------|------|-------------|------|
| Development | 開発・テスト | 自動/手動 | 不要 |
| Staging | 本番前検証 | 自動/手動 | 不要 |
| Production | 本番運用 | 手動のみ | 必要 |

## ドキュメント

### 開発・運用ガイド
- [自動化セットアップガイド](docs/automation-setup-guide.md) 🆕 **推奨**
- [段階的デプロイメントガイド](docs/deployment-guide.md)
- [統合テスト実行ガイド](docs/integration-testing-guide.md) 🆕 **テスト環境**
- [認証・API統合ガイド](docs/authentication-integration-guide.md)
- [ローカル開発環境ガイド](docs/local-development-guide.md)

### 設定ランブック
- [手作業参照ガイド](docs/manual-setup-reference-guide.md) 🆕 **完全手順**
- [GitHub Actions Secrets設定](docs/runbook/github-actions_secrets-and-iam-for-aws_and-vercel.md)
- [Google OAuth設定](docs/runbook/google-oauth-setup.md)
- [Vercel設定](docs/runbook/vercel-project-setup_and-detach-github.md)

### 設計・仕様書
- [要件定義書](.kiro/specs/secure-excel-unlock/requirements.md)
- [設計書](.kiro/specs/secure-excel-unlock/design.md)
- [実装計画](.kiro/specs/secure-excel-unlock/tasks.md)

### ユーザー管理・運用
- [ユーザー管理運用ガイド](docs/user-management-operations-guide.md) 🆕 **包括的運用手順**
- [ユーザー管理クイックリファレンス](docs/user-management-quick-reference.md) 🆕 **よく使うコマンド**

### 実装完了状況
- [実装完了サマリー](docs/implementation-complete-summary.md) ✅ **統合テスト環境完了**
- [セキュリティ強化](docs/security-enhancements.md)