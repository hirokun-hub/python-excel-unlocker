# 📚 Excel Unlocker ドキュメント索引

このファイルは、Excel Unlockerプロジェクトの全ドキュメントへの統一アクセスポイントです。目的別・作業別に整理されているので、必要な情報を素早く見つけることができます。

## 🚀 クイックスタート

| 目的 | ドキュメント | 説明 |
|------|-------------|------|
| **すぐに始めたい** | [ローカル開発ガイド](local-development-guide.md) | 開発環境の構築と動作確認 |
| **デプロイしたい** | [デプロイメントガイド](deployment-guide.md) | 段階的デプロイメント手順 |
| **自動化したい** | [自動化セットアップガイド](automation-setup-guide.md) | ワンコマンドでの環境構築 |
| **手作業で設定したい** | [手作業参照ガイド](manual-setup-reference-guide.md) | 詳細な手動設定手順 |

## 📋 カテゴリ別ドキュメント

### 🏗️ セットアップ・環境構築

| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [🔰 初心者向け完全セットアップガイド](beginner-complete-setup-guide.md) | 技術知識不要の詳細セットアップ手順 | **初心者・社内展開** |
| [✅ セットアップチェックリスト](setup-checklist.md) | 設定完了確認用チェックリスト | **初心者・管理者** |
| [❓ よくある質問（FAQ）](beginner-faq.md) | 初心者向けFAQ集 | **初心者・全員** |
| [🔧 トラブルシューティング診断フローチャート](troubleshooting-flowchart.md) | 問題解決用診断フロー | **初心者・管理者** |
| [ローカル開発ガイド](local-development-guide.md) | 開発環境の構築・テスト実行 | 開発者 |
| [自動化セットアップガイド](automation-setup-guide.md) | 完全自動化による環境構築 | 開発者・運用者 |
| [手作業参照ガイド](manual-setup-reference-guide.md) | 手動設定の詳細手順 | 開発者・運用者 |
| [設定テンプレート](configuration-templates.md) | 各種設定ファイルのテンプレート | 開発者 |
| [手作業設定索引](manual-setup-index.md) | 手作業設定の一覧 | 開発者 |

### 🚀 デプロイメント・運用

| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [デプロイメントガイド](deployment-guide.md) | 段階的デプロイメント手順 | 運用者 |
| [実装完了サマリー](implementation-complete-summary.md) | プロジェクト完了状況の概要 | 全員 |
| [統合テストガイド](integration-testing-guide.md) | 統合テスト実行手順 | 開発者・QA |
| [トラブルシューティング診断ガイド](troubleshooting-diagnostic-guide.md) | 問題解決手順 | 運用者 |

### 🔐 セキュリティ・認証

| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [JWT認証移行](jwt-authentication-migration.md) | JWT認証システムの実装 | 開発者 |
| [認証統合ガイド](authentication-integration-guide.md) | 認証システムの統合手順 | 開発者 |
| [フロントエンドトークンセキュリティ](frontend-token-security-implementation.md) | フロントエンドのトークン保護 | 開発者 |
| [GitHub OIDC移行](github-oidc-migration.md) | GitHub OIDCによるセキュア認証 | 運用者 |
| [CORS セキュリティ強化](cors-security-hardening.md) | CORS設定の厳格化 | 開発者 |
| [CSP実装ガイド](csp-implementation-guide.md) | Content Security Policy設定 | 開発者 |
| [セキュリティ強化](security-enhancements.md) | 包括的セキュリティ対策 | 開発者・運用者 |

### 🛡️ ファイル・データセキュリティ

| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [ファイルセキュリティ実装](file-security-implementation.md) | ファイル安全性チェック | 開発者 |
| [S3制約アップロード実装](s3-constrained-upload-implementation.md) | S3アップロード制約 | 開発者 |
| [レート制限・WAF実装サマリー](rate-limiting-waf-implementation-summary.md) | DDoS・総当たり攻撃対策 | 運用者 |
| [レート制限・WAFガイド](rate-limiting-waf-guide.md) | レート制限の詳細設定 | 運用者 |

### 👥 ユーザー管理・運用

| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [ユーザー管理運用ガイド](user-management-operations-guide.md) | ユーザー管理の運用手順 | 管理者 |
| [ユーザー管理クイックリファレンス](user-management-quick-reference.md) | ユーザー管理の簡易手順 | 管理者 |

### 🤖 自動化・効率化

| ドキュメント | 内容 | 対象者 |
|-------------|------|--------|
| [タスク自動化ガイド](task-automation-guide.md) | タスク完了時の自動コミット・プッシュ | 開発者 |
| [クイックリファレンススクリーンショット](quick-reference-screenshots.md) | 設定画面のスクリーンショット集 | 全員 |

## 🔧 ランブック（運用手順書）

詳細な運用手順は [`runbook/`](runbook/) ディレクトリに整理されています：

| ランブック | 内容 | 対象者 |
|-----------|------|--------|
| [Google OAuth設定](runbook/google-oauth-setup.md) | Google OAuth設定の詳細手順 | 開発者・運用者 |
| [Vercelプロジェクト設定](runbook/vercel-project-setup_and-detach-github.md) | Vercel設定とGit連携解除 | 開発者・運用者 |
| [GitHub Actions・AWS・Vercel設定](runbook/github-actions_secrets-and-iam-for-aws_and-vercel.md) | CI/CD設定の詳細手順 | 運用者 |

## 📁 アーカイブ

過去のドキュメントや参考資料は [`archive/`](archive/) ディレクトリに保管されています：

- **開発資料**: 設計書・企画書・技術調査資料
- **統合資料**: 過去の統合テスト・プロジェクト資料
- **セキュリティ資料**: セキュリティ分析・対策資料

## 🎯 作業フロー別ガイド

### 🔰 初心者・社内展開
1. [🔰 初心者向け完全セットアップガイド](beginner-complete-setup-guide.md) - 技術知識不要の環境構築
2. [✅ セットアップチェックリスト](setup-checklist.md) - 設定完了確認
3. [❓ よくある質問（FAQ）](beginner-faq.md) - 問題解決
4. [🔧 トラブルシューティング診断フローチャート](troubleshooting-flowchart.md) - 問題診断

### 新規開発者のオンボーディング
1. [ローカル開発ガイド](local-development-guide.md) - 環境構築
2. [認証統合ガイド](authentication-integration-guide.md) - 認証システム理解
3. [統合テストガイド](integration-testing-guide.md) - テスト実行

### 本番環境デプロイ
1. [自動化セットアップガイド](automation-setup-guide.md) - 自動化環境構築
2. [デプロイメントガイド](deployment-guide.md) - 段階的デプロイ
3. [ユーザー管理運用ガイド](user-management-operations-guide.md) - ユーザー管理

### セキュリティ強化
1. [セキュリティ強化](security-enhancements.md) - 包括的対策
2. [JWT認証移行](jwt-authentication-migration.md) - 認証強化
3. [ファイルセキュリティ実装](file-security-implementation.md) - ファイル保護

### トラブルシューティング
1. [トラブルシューティング診断ガイド](troubleshooting-diagnostic-guide.md) - 問題診断
2. [統合テストガイド](integration-testing-guide.md) - 動作確認
3. [ローカル開発ガイド](local-development-guide.md) - ローカル検証

## 📊 ドキュメント管理情報

- **最終更新**: 2025年1月19日
- **総ドキュメント数**: 29個（メインドキュメント）+ ランブック3個 + アーカイブ
- **管理者**: 開発チーム
- **更新頻度**: 機能追加・変更時に随時更新
- **新規追加**: 初心者向けドキュメント4個（セットアップガイド、チェックリスト、FAQ、診断フロー）

## 💡 ドキュメント利用のコツ

### 🔍 目的別の探し方
- **🔰 初めて設定する** → [初心者向け完全セットアップガイド](beginner-complete-setup-guide.md)
- **❓ 問題を解決したい** → [よくある質問（FAQ）](beginner-faq.md) → [診断フローチャート](troubleshooting-flowchart.md)
- **✅ 設定を確認したい** → [セットアップチェックリスト](setup-checklist.md)
- **すぐに動かしたい** → クイックスタートから選択
- **詳細を知りたい** → カテゴリ別から該当分野を選択
- **手順を確認したい** → ランブックを参照
- **過去の経緯を知りたい** → アーカイブを確認

### 📝 ドキュメント更新時のお願い
1. 新しいドキュメントを追加した場合は、このindex.mdも更新してください
2. ドキュメント名は日本語で内容が分かるように命名してください
3. 古くなったドキュメントはarchive/に移動してください

---

**このindex.mdを起点として、プロジェクトの全ドキュメントに効率的にアクセスできます。**
**迷った時は、まずこのファイルに戻って目的に合ったドキュメントを探してください。**