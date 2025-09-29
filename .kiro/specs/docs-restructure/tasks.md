# ドキュメント再構成実装計画

## 実装タスク

- [x] 1. ドキュメント構造の準備とエントリーポイント作成
  - 新しいディレクトリ構造の作成（architecture/setup/security/operations/testing/reference）
  - docs/README.md のエントリーポイント作成（全体像、ガイドライン、カテゴリリンク）
  - _要件: 1.1, 1.2, 1.3_

- [x] 2. アーキテクチャドキュメントの作成
  - [x] 2.1 システム全体構成の文書化
    - docs/architecture/solution-overview.md の作成（システム構成図、データフロー、技術スタック）
    - Next.js + Lambda + S3 + Google OAuth の構成図をMermaidで作成
    - _要件: 2.1_

  - [x] 2.2 バックエンドサービス詳細の文書化
    - docs/architecture/backend-services.md の作成（Lambda関数責務、AWSリソース説明）
    - template.yaml の主要リソース解説とS3バケット構成説明
    - _要件: 2.2_

  - [x] 2.3 フロントエンドアプリ構成の文書化
    - docs/architecture/frontend-app.md の作成（App Router、認証フロー、Google Drive API連携）
    - Auth.js設定とJWT伝搬方法の詳細説明
    - _要件: 2.3_

- [ ] 3. セットアップガイドの体系化
  - [x] 3.1 ローカル開発環境ガイドの作成
    - docs/setup/local-development.md の作成（前提ツール、.env.local設定、SAM Local連携）
    - 現在のpackage.jsonとrequirements.txtに基づく正確な手順記載
    - _要件: 3.1_

  - [x] 3.2 環境プロビジョニングガイドの作成
    - docs/setup/environment-provisioning.md の作成（AWSデプロイ、Vercel設定、環境別設定）
    - samconfig.tomlとtemplate.yamlに基づく環境別パラメータ説明
    - _要件: 3.2_

  - [x] 3.3 GitHub OIDC連携ガイドの作成
    - docs/setup/github-oidc-aws.md の作成（IAM Role設計、trust policy、ワークフロー連携）
    - 現在のdeploy-aws.ymlとtemplate.yamlのOIDC設定に基づく手順
    - _要件: 3.3_

- [ ] 4. セキュリティドキュメントの強化
  - [ ] 4.1 認証ガイドの作成
    - docs/security/authentication-guide.md の作成（JWT認証、Google OAuth、ALLOWED_USERS）
    - auth_utils.pyとauth.tsの実装に基づく正確な認証フロー説明
    - _要件: 4.1_

  - [ ] 4.2 ストレージ・ファイルセキュリティガイドの作成
    - docs/security/storage-and-files.md の作成（S3署名付きURL、ファイル検証、クリーンアップ）
    - get_upload_url.pyとunlock.pyの実装に基づくセキュリティ機能説明
    - _要件: 4.2_

  - [ ] 4.3 プラットフォーム強化ガイドの作成
    - docs/security/platform-hardening.md の作成（CORS、WAF、監視、Secrets管理）
    - template.yamlのWAF設定とCloudWatch設定に基づく説明
    - _要件: 4.3_

- [ ] 5. 運用ドキュメントの実用化
  - [ ] 5.1 運用ランブックの作成
    - docs/operations/runbook.md の作成（定常運用、障害対応、API疎通確認コマンド）
    - CloudWatch Dashboard、アラーム設定に基づく監視手順
    - _要件: 5.1, 5.3_

  - [ ] 5.2 ユーザー管理ガイドの作成
    - docs/operations/user-management.md の作成（ALLOWED_USERS更新、監査、アクセステスト）
    - auth_utils.pyの実装に基づくユーザー管理機能説明
    - _要件: 5.2_

- [ ] 6. テストドキュメントの整備
  - [-] 6.1 テスト戦略概要の作成
    - docs/testing/overview.md の作成（テスト分類、統合テスト、モック方針）
    - 現在のpackage.jsonのテストスクリプトに基づく実行方法説明
    - _要件: 6.1, 6.3_

  - [ ] 6.2 フロントエンドテストガイドの作成
    - docs/testing/frontend.md の作成（Jest/RTL、Playwright、モックAPI）
    - package.jsonのテスト設定とPlaywright設定に基づく詳細手順
    - _要件: 6.2_

- [ ] 7. リファレンスドキュメントの充実
  - [ ] 7.1 設定マトリックスの作成
    - docs/reference/configuration-matrix.md の作成（環境別設定表、SAMパラメータ対応）
    - samconfig.toml、template.yaml、package.jsonに基づく設定項目一覧
    - _要件: 7.1_

  - [ ] 7.2 スクリプトカタログの作成
    - docs/reference/script-catalog.md の作成（scripts/配下スクリプト一覧、使用方法）
    - 実際のscripts/ディレクトリ内容に基づくスクリプト説明
    - _要件: 7.2_

  - [ ] 7.3 APIカタログの作成
    - docs/reference/api-catalog.md の作成（エンドポイント、リクエスト/レスポンス例）
    - get_upload_url.pyとunlock.pyの実装に基づくAPI仕様説明
    - _要件: 7.3_

- [ ] 8. ドキュメント品質保証と最終調整
  - [ ] 8.1 コード整合性チェック
    - 全ドキュメントの内容と実際のコードベースの整合性確認
    - 環境変数名、API仕様、設定項目の一致確認
    - _要件: 8.2_

  - [ ] 8.2 書式統一とリンク整備
    - ステアリングルールに従った書式統一の確認
    - ドキュメント間のクロスリンク設定
    - _要件: 8.1, 8.3_

  - [ ] 8.3 最終レビューと公開準備
    - 全ドキュメントの最終レビューと修正
    - 既存ドキュメントのアーカイブ移動確認
    - _要件: 8.1, 8.2, 8.3_