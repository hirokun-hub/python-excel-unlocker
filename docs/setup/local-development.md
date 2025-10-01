---
layout: default
title: ローカル開発環境構築ガイド
description: Secure Excel Unlockプロジェクトのローカル開発環境セットアップの完全ガイド
author: Hiroaki Endo
permalink: setup-local-development
date: 2025-01-29
last_modified_at: 2025-01-29
published: false
Tags:
  - setup
  - local_development
  - nodejs
  - python
  - sam_cli
  - environment_variables
---

> **AI生成物の注意書き**：内容の最終確認が必要です。数値・日付は原典と照合してください。

**結論**：Node.js 18 + Python 3.9 + SAM CLI の組み合わせで効率的なローカル開発環境を構築  
**対象**：新規参加開発者、フロントエンド・バックエンド開発者  
**所要時間**：30分（初回セットアップ）、5分（日常起動）  
**次の一手**：1) 前提ツール確認 → 2) 環境変数設定 → 3) ローカル実行テスト  
**根拠**：・SAM Localによる本番環境に近い開発体験／・Hot Reloadによる開発効率向上／・統合テスト環境の提供

## 前提ツール

### 必須ツール

#### Node.js 18以上
```bash
# バージョン確認
node --version  # v18.0.0 以上
npm --version   # 9.0.0 以上

# インストール（未インストールの場合）
# macOS (Homebrew)
brew install node@18

# Windows (Chocolatey)
choco install nodejs --version=18.19.0

# Linux (NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Python 3.9以上
```bash
# バージョン確認
python3 --version  # Python 3.9.0 以上
pip3 --version     # 21.0.0 以上

# インストール（未インストールの場合）
# macOS (Homebrew)
brew install python@3.9

# Windows (Python.org)
# https://www.python.org/downloads/ からダウンロード

# Linux (apt)
sudo apt update
sudo apt install python3.9 python3.9-pip
```

#### AWS SAM CLI
```bash
# バージョン確認
sam --version  # SAM CLI, version 1.100.0 以上

# インストール（未インストールの場合）
# macOS (Homebrew)
brew tap aws/tap
brew install aws-sam-cli

# Windows (MSI Installer)
# https://github.com/aws/aws-sam-cli/releases/latest からダウンロード

# Linux (pip)
pip3 install aws-sam-cli
```

### 推奨ツール

#### Docker（SAM Local用）
```bash
# バージョン確認
docker --version  # Docker version 20.0.0 以上

# インストール
# Docker Desktop をインストール
# https://www.docker.com/products/docker-desktop
```

#### Git
```bash
# バージョン確認
git --version  # git version 2.30.0 以上
```

## プロジェクトセットアップ

### 1. リポジトリクローン

```bash
# プロジェクトクローン
git clone https://github.com/your-org/secure-excel-unlock.git
cd secure-excel-unlock

# ブランチ確認
git branch -a
git checkout develop  # 開発ブランチに切り替え
```

### 2. 依存関係インストール

#### フロントエンド依存関係
```bash
cd frontend

# 依存関係インストール
npm install

# インストール確認
npm list --depth=0
```

#### バックエンド依存関係
```bash
cd ../backend

# Python仮想環境作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r src/requirements.txt

# 開発・テスト用依存関係
pip install pytest pytest-cov moto[s3] boto3-stubs

# インストール確認
pip list
```

## 環境変数設定

### フロントエンド環境変数

#### .env.local 作成
```bash
cd frontend

# テンプレートをコピー
cp .env.example .env.local

# 設定ファイル編集
nano .env.local  # または好みのエディタ
```

#### .env.local 設定例
```bash
# Next.js設定
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-development-secret-key-min-32-chars

# Google OAuth設定（開発用）
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# バックエンドAPI設定
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_USE_MOCK_API=false

# 開発モード設定
NODE_ENV=development
```

### バックエンド環境変数

#### 環境変数設定（開発用）
```bash
# 開発環境用の環境変数
export AWS_REGION=ap-northeast-1
export S3_BUCKET_NAME=excel-unlocker-bucket-dev-local
export LOG_LEVEL=INFO
export ALLOWED_USERS=your-email@example.com
export ENVIRONMENT=development

# Google OAuth設定（JWT検証用）
export GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# 開発用設定
export AWS_SAM_LOCAL=true
export DEVELOPMENT_MODE=true
```

#### 環境変数永続化（推奨）
```bash
# ~/.bashrc または ~/.zshrc に追加
echo 'export AWS_REGION=ap-northeast-1' >> ~/.bashrc
echo 'export S3_BUCKET_NAME=excel-unlocker-bucket-dev-local' >> ~/.bashrc
echo 'export LOG_LEVEL=INFO' >> ~/.bashrc
echo 'export ALLOWED_USERS=your-email@example.com' >> ~/.bashrc
echo 'export ENVIRONMENT=development' >> ~/.bashrc

# 設定を反映
source ~/.bashrc
```

## Google OAuth設定

### 1. Google Cloud Console設定

#### OAuth 2.0 クライアント作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト選択または新規作成
3. 「APIとサービス」→「認証情報」
4. 「認証情報を作成」→「OAuth 2.0 クライアント ID」

#### 開発用設定
```yaml
アプリケーションの種類: ウェブアプリケーション
名前: Secure Excel Unlock (Development)

承認済みのJavaScript生成元:
  - http://localhost:3000
  - http://127.0.0.1:3000

承認済みのリダイレクトURI:
  - http://localhost:3000/api/auth/callback/google
  - http://127.0.0.1:3000/api/auth/callback/google
```

#### 必要なAPI有効化
```bash
# Google Drive API
# Google Cloud Console → APIとサービス → ライブラリ
# "Google Drive API" を検索して有効化

# People API（プロフィール情報取得用）
# "Google People API" を検索して有効化
```

### 2. スコープ設定確認

```typescript
// frontend/src/auth.ts で設定されるスコープ
const scopes = [
  "openid",
  "email", 
  "profile",
  "https://www.googleapis.com/auth/drive.file", // ファイル作成・編集のみ
].join(" ")
```

## ローカル実行

### 1. バックエンド起動（SAM Local）

```bash
cd backend

# SAM ビルド
sam build

# ローカルAPI起動
sam local start-api --port 3001 --host 0.0.0.0

# 起動確認
curl http://localhost:3001/presigned-urls -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-jwt-token-your-email@example.com" \
  -d '{"fileName": "test.xlsx", "fileSize": 1024, "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}'
```

#### SAM Local 設定オプション
```bash
# デバッグモード
sam local start-api --port 3001 --debug

# 環境変数ファイル使用
sam local start-api --port 3001 --env-vars env.json

# Docker ネットワーク指定
sam local start-api --port 3001 --docker-network sam-local
```

### 2. フロントエンド起動

```bash
cd frontend

# 開発サーバー起動
npm run dev

# または特定ポートで起動
npm run dev:3001

# 起動確認
open http://localhost:3000
```

#### 開発サーバーオプション
```bash
# Turbopack使用（高速）
npm run dev -- --turbo

# 特定ホストでバインド
npm run dev -- --hostname 0.0.0.0

# ポート指定
npm run dev -- --port 3002
```

## 開発ワークフロー

### 日常的な開発手順

#### 1. 開発環境起動
```bash
# ターミナル1: バックエンド
cd backend
sam local start-api --port 3001

# ターミナル2: フロントエンド
cd frontend
npm run dev

# ターミナル3: テスト実行用
cd frontend
npm run test:watch
```

#### 2. 開発サイクル
```mermaid
---
title: 開発サイクル
config:
  theme: neutral
  sequence:
    showSequenceNumbers: true
---
flowchart TD
    Start["🚀 開発開始"] --> Code["💻 コード編集"]
    Code --> HotReload["🔄 Hot Reload<br>自動反映"]
    HotReload --> Test["🧪 テスト実行"]
    Test --> Debug["🐛 デバッグ"]
    Debug --> Code
    Test --> Commit["📝 コミット"]
    Commit --> Push["📤 プッシュ"]
    Push --> CI["🔄 CI/CD実行"]
```

### テスト実行

#### フロントエンドテスト
```bash
cd frontend

# ユニットテスト
npm run test

# ウォッチモード
npm run test:watch

# カバレッジ付き
npm run test:coverage

# E2Eテスト
npm run test:e2e

# 型チェック
npm run type-check

# リント
npm run lint
```

#### バックエンドテスト
```bash
cd backend

# Python環境アクティベート
source venv/bin/activate

# ユニットテスト
pytest tests/unit/

# カバレッジ付き
pytest tests/unit/ --cov=src --cov-report=html

# 特定テスト実行
pytest tests/unit/test_auth_utils.py -v

# テスト環境変数設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest
```

### 統合テスト

#### SAM Local + Next.js 連携テスト
```bash
# 統合テストスクリプト実行
./tests/run-integration-tests.sh all

# 個別テスト
./tests/run-integration-tests.sh auth
./tests/run-integration-tests.sh upload
./tests/run-integration-tests.sh unlock
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. SAM Local起動エラー
```bash
# Docker未起動
Error: Docker is not running
→ Docker Desktop を起動

# ポート競合
Error: Port 3001 is already in use
→ lsof -ti:3001 | xargs kill -9

# 権限エラー
Error: Permission denied
→ sudo sam local start-api --port 3001
```

#### 2. フロントエンド起動エラー
```bash
# Node.jsバージョン不一致
Error: Node.js version mismatch
→ nvm use 18 または node --version 確認

# 依存関係エラー
Error: Module not found
→ rm -rf node_modules package-lock.json && npm install

# ポート競合
Error: Port 3000 is already in use
→ npm run dev -- --port 3002
```

#### 3. 認証エラー
```bash
# Google OAuth設定エラー
Error: Invalid client ID
→ .env.local の GOOGLE_CLIENT_ID 確認

# JWT検証エラー
Error: JWT verification failed
→ バックエンドの GOOGLE_CLIENT_ID 環境変数確認

# セッションエラー
Error: Session not found
→ NEXTAUTH_SECRET 設定確認（32文字以上）
```

#### 4. API通信エラー
```bash
# CORS エラー
Error: CORS policy blocked
→ バックエンドの ALLOWED_ORIGIN 設定確認

# 接続エラー
Error: Connection refused
→ SAM Local が起動しているか確認
→ NEXT_PUBLIC_API_URL 設定確認
```

### デバッグ方法

#### フロントエンドデバッグ
```bash
# ブラウザ開発者ツール
# Chrome DevTools → Network/Console タブ

# Next.js デバッグモード
DEBUG=* npm run dev

# React Developer Tools
# Chrome拡張機能をインストール
```

#### バックエンドデバッグ
```bash
# SAM Local デバッグモード
sam local start-api --debug --port 3001

# Python デバッガー
# コードに breakpoint() を挿入

# ログレベル変更
export LOG_LEVEL=DEBUG
sam local start-api --port 3001
```

## 開発ツール推奨設定

### VS Code 設定

#### 推奨拡張機能
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "aws-scripting-guy.cform",
    "amazonwebservices.aws-toolkit-vscode"
  ]
}
```

#### ワークスペース設定
```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.testing.pytestEnabled": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

### Git フック設定

#### pre-commit フック
```bash
# .git/hooks/pre-commit
#!/bin/sh
cd frontend && npm run lint && npm run type-check
cd ../backend && python -m pytest tests/unit/ --tb=short
```

## パフォーマンス最適化

### 開発環境の高速化

#### Node.js 最適化
```bash
# npm キャッシュクリア
npm cache clean --force

# Turbopack 使用
npm run dev -- --turbo

# 並列処理数調整
export UV_THREADPOOL_SIZE=4
```

#### Python 最適化
```bash
# pip キャッシュ利用
pip install --cache-dir ~/.pip/cache -r requirements.txt

# Python バイトコード生成
export PYTHONDONTWRITEBYTECODE=0
```

#### Docker 最適化
```bash
# Docker イメージキャッシュ
docker system prune -f

# SAM Local キャッシュ
sam local start-api --warm-containers EAGER
```

## 結論

ローカル開発環境は、Node.js 18 + Python 3.9 + SAM CLI の組み合わせにより、本番環境に近い開発体験を提供します。適切な環境変数設定、Google OAuth の開発用設定、効率的なテスト実行により、生産性の高い開発ワークフローを実現できます。トラブルシューティングガイドと推奨ツール設定により、スムーズな開発開始が可能です。