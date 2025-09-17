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

### ローカル開発
```bash
# バックエンドAPI起動
sam local start-api --port 3001

# フロントエンド起動
cd frontend
npm run dev
```

### デプロイ
```bash
# バックエンドデプロイ
sam deploy

# フロントエンドデプロイ（Vercel）
vercel --prod
```

## ドキュメント

- [認証・API統合ガイド](docs/authentication-integration-guide.md)
- [ローカル開発環境ガイド](docs/local-development-guide.md)
- [要件定義書](.kiro/specs/secure-excel-unlock/requirements.md)
- [設計書](.kiro/specs/secure-excel-unlock/design.md)
- [実装計画](.kiro/specs/secure-excel-unlock/tasks.md)