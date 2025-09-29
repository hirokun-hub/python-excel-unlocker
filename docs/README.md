【出力】ドキュメント.全体構成_プロジェクトドキュメントガイド

```yaml
---
layout: default
title: プロジェクトドキュメントガイド
description: Secure Excel Unlockプロジェクトの包括的ドキュメント体系への入り口
author: Hiroaki Endo
permalink: project-documentation-guide
date: 2025-01-29
last_modified_at: 2025-01-29
published: false
Tags:
  - documentation
  - guide
  - project_overview
  - navigation
  - getting_started
---
```

> **AI生成物の注意書き**：内容の最終確認が必要です。数値・日付は原典と照合してください。

**結論**：用途別カテゴリに整理されたドキュメント体系により、開発・運用・セキュリティの各領域で効率的な情報アクセスを実現  
**対象**：開発者、運用担当者、セキュリティ担当者、QA担当者  
**所要時間**：5分（概要把握）、各ガイド10-30分  
**次の一手**：1) 役割に応じたガイド選択 → 2) セットアップ実行 → 3) 運用開始  
**根拠**：・カテゴリ別整理による検索効率向上／・現行コードベースとの完全整合性

## プロジェクト概要

**Secure Excel Unlock** は、パスワード保護されたExcelファイルを安全かつ効率的に解除するWebアプリケーションです。Google OAuth認証による招待制アクセス制御と、AWS Lambda + S3による高セキュリティなファイル処理を特徴としています。

### 技術構成
- **フロントエンド**: Next.js 15.4 + React 19 + Auth.js（Google OAuth）
- **バックエンド**: AWS Lambda（Python 3.9）+ API Gateway + S3
- **認証**: Google OAuth 2.0 + JWT + 招待制アクセス制御
- **処理エンジン**: msoffcrypto-tool による Excel パスワード解除
- **デプロイ**: GitHub Actions + AWS SAM + Vercel

## まず読むガイドライン

### 🚀 新規参加者向け
1. **[システム全体構成](architecture/solution-overview.md)** - 技術スタックとデータフローの理解
2. **[ローカル開発環境構築](setup/local-development.md)** - 開発環境のセットアップ
3. **[テスト実行方法](testing/overview.md)** - 品質保証の基本

### 👨‍💻 開発者向け
1. **[フロントエンドアプリ構成](architecture/frontend-app.md)** - Next.js App Router と認証フロー
2. **[バックエンドサービス](architecture/backend-services.md)** - Lambda 関数と AWS リソース
3. **[API仕様](reference/api-catalog.md)** - エンドポイントとリクエスト/レスポンス

### 🔧 運用担当者向け
1. **[環境プロビジョニング](setup/environment-provisioning.md)** - AWS と Vercel へのデプロイ
2. **[運用ランブック](operations/runbook.md)** - 日常運用と障害対応
3. **[ユーザー管理](operations/user-management.md)** - アクセス権限の管理

### 🔒 セキュリティ担当者向け
1. **[認証ガイド](security/authentication-guide.md)** - JWT 認証と Google OAuth 設定
2. **[ストレージセキュリティ](security/storage-and-files.md)** - S3 署名付き URL とファイル検証
3. **[プラットフォーム強化](security/platform-hardening.md)** - WAF、CORS、監視設定

## カテゴリ別ドキュメント

### 🏗️ アーキテクチャ（システム設計・技術構成）
| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [システム全体構成](architecture/solution-overview.md) | 技術スタック、データフロー、環境別構成 | 全員 |
| [バックエンドサービス](architecture/backend-services.md) | Lambda 関数、AWS リソース、IAM 設計 | 開発者、運用者 |
| [フロントエンドアプリ](architecture/frontend-app.md) | App Router、認証、Google Drive API 連携 | 開発者 |

### ⚙️ セットアップ（環境構築・デプロイ）
| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [ローカル開発環境](setup/local-development.md) | 前提ツール、環境変数、SAM Local 連携 | 開発者 |
| [環境プロビジョニング](setup/environment-provisioning.md) | AWS デプロイ、Vercel 設定、環境別設定 | 運用者 |
| [GitHub OIDC 連携](setup/github-oidc-aws.md) | IAM Role 設計、CI/CD パイプライン設定 | 運用者 |

### 🔐 セキュリティ（認証・認可・データ保護）
| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [認証ガイド](security/authentication-guide.md) | JWT 認証、Google OAuth、Bot 保護 | セキュリティ、開発者 |
| [ストレージ・ファイル](security/storage-and-files.md) | S3 署名付き URL、ファイル検証、クリーンアップ | セキュリティ、開発者 |
| [プラットフォーム強化](security/platform-hardening.md) | WAF、CORS、監視、Secrets 管理 | セキュリティ、運用者 |

### 🔧 運用（監視・保守・障害対応）
| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [運用ランブック](operations/runbook.md) | 定常運用、障害対応、API 疎通確認 | 運用者 |
| [ユーザー管理](operations/user-management.md) | ALLOWED_USERS 更新、監査、アクセステスト | 運用者、セキュリティ |

### 🧪 テスト（品質保証・テスト戦略）
| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [テスト戦略概要](testing/overview.md) | ユニット/統合/E2E、SAM Local 連携 | 開発者、QA |
| [フロントエンドテスト](testing/frontend.md) | Jest/RTL、Playwright、モック API | 開発者、QA |

### 📚 リファレンス（設定・API・スクリプト）
| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [設定マトリックス](reference/configuration-matrix.md) | 環境別設定表、SAM パラメータ対応 | 全員 |
| [スクリプトカタログ](reference/script-catalog.md) | scripts/ 配下の全スクリプト使用方法 | 開発者、運用者 |
| [API カタログ](reference/api-catalog.md) | エンドポイント、リクエスト/レスポンス例 | 開発者 |

## クイックスタート

### 開発環境セットアップ（15分）
```bash
# 1. 前提ツールの確認
node --version  # 18以上
python --version  # 3.9以上
sam --version  # SAM CLI

# 2. 依存関係のインストール
cd frontend && npm install
cd ../backend && pip install -r src/requirements.txt

# 3. 環境変数の設定
cp frontend/.env.example frontend/.env.local
# .env.local を編集（詳細は setup/local-development.md）

# 4. ローカル実行
sam local start-api --port 3001 &
cd frontend && npm run dev
```

### 本番デプロイ（30分）
```bash
# 1. AWS 認証設定
aws configure

# 2. バックエンドデプロイ
sam build && sam deploy --guided

# 3. フロントエンドデプロイ
cd frontend && vercel --prod
```

詳細は [環境プロビジョニングガイド](setup/environment-provisioning.md) を参照してください。

## よくある質問

### Q: 認証エラーが発生する
A: [認証ガイド](security/authentication-guide.md) の JWT 設定と ALLOWED_USERS 設定を確認してください。

### Q: ファイルアップロードが失敗する
A: [ストレージセキュリティガイド](security/storage-and-files.md) のファイル検証ルールを確認してください。

### Q: デプロイが失敗する
A: [GitHub OIDC 連携ガイド](setup/github-oidc-aws.md) の IAM Role 設定を確認してください。

## サポート・フィードバック

- **技術的な問題**: [運用ランブック](operations/runbook.md) の障害対応手順を参照
- **セキュリティに関する懸念**: [プラットフォーム強化ガイド](security/platform-hardening.md) を確認
- **ドキュメントの改善提案**: GitHub Issues でフィードバックをお寄せください

## 結論

このドキュメント体系は、Secure Excel Unlock プロジェクトの開発・運用・セキュリティ管理を効率的に行うための包括的なガイドを提供します。各カテゴリは相互に関連しており、クロスリンクにより必要な情報へ素早くアクセスできます。