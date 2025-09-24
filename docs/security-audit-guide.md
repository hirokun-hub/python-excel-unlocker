# セキュリティ監査ガイド

## 概要

このガイドでは、Excel Password Removerプロジェクトのセキュリティ設定を定期的に監査するための手順を説明します。

## 🎯 監査の目的

- **セキュリティリスクの早期発見**: 設定ミスや脆弱性の特定
- **コンプライアンス確保**: セキュリティ要件への準拠確認
- **継続的改善**: セキュリティ設定の最適化
- **インシデント予防**: 問題の事前対策

## 📋 監査対象

### 1. GitHub OIDC設定
- OIDCプロバイダーの存在と設定
- IAMロールの信頼ポリシー
- ブランチ制限の適切性
- 最小権限原則の適用状況

### 2. GitHub Secrets管理
- 必要なシークレットの設定状況
- 未使用シークレットの特定
- 非推奨シークレットの確認
- セキュアな認証方式の採用

### 3. アクセス制御
- リポジトリレベルでの制限
- ブランチ保護の設定
- 権限の最小化
- 定期的な権限レビュー

## 🚀 監査実行手順

### クイックスタート

```bash
# 包括的セキュリティ監査の実行
./scripts/security-audit-comprehensive.py
```

### 個別監査

```bash
# GitHub OIDC設定の監査
./scripts/security-audit-github-oidc.py

# GitHub Secrets管理の監査
./scripts/security-audit-github-secrets.py
```

## 📊 監査スケジュール

### 定期監査
- **月次監査**: 包括的セキュリティ監査
- **週次チェック**: GitHub Secrets使用状況確認
- **リリース前**: 全項目の確認

### 臨時監査
- **新機能追加時**: 関連するセキュリティ設定の確認
- **インシデント発生時**: 全面的なセキュリティ見直し
- **チームメンバー変更時**: アクセス権限の再確認

## 🔍 監査項目詳細

### GitHub OIDC設定監査

#### 確認項目
1. **OIDCプロバイダーの存在**
   ```bash
   aws iam list-open-id-connect-providers
   ```

2. **IAMロールの信頼ポリシー**
   ```bash
   aws iam get-role --role-name GitHubActionsRole
   ```

3. **ブランチ制限の設定**
   - `main`ブランチからのアクセス許可
   - `develop`ブランチからのアクセス許可
   - ワイルドカード使用の適切性

4. **最小権限ポリシー**
   - CloudFormation操作権限
   - Lambda関数管理権限
   - S3バケット操作権限
   - API Gateway操作権限

#### 期待される結果
- ✅ OIDCプロバイダーが設定済み
- ✅ IAMロールが適切な信頼ポリシーを持つ
- ✅ ブランチ制限が適切に設定
- ✅ 最小権限の原則が適用

### GitHub Secrets管理監査

#### 確認項目
1. **必要なシークレット**
   - `AWS_GITHUB_ACTIONS_ROLE_ARN` (OIDC使用時)
   - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (アクセスキー使用時)
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
   - `ALLOWED_USERS`

2. **未使用シークレット**
   - ワークフローで参照されていないシークレット
   - 非推奨となったシークレット

3. **セキュリティ設定**
   - OIDC vs アクセスキー認証の選択
   - シークレットの定期更新状況

#### 期待される結果
- ✅ 必要なシークレットがすべて設定済み
- ✅ 未使用シークレットが整理済み
- ✅ セキュアな認証方式を採用
- ✅ 定期的な更新が実施

## 📈 セキュリティスコア評価

### スコア基準

| スコア | 評価 | 状態 | 対応 |
|--------|------|------|------|
| 80-100 | 優秀 | 🟢 良好 | 定期監査継続 |
| 60-79 | 良好 | 🟡 改善推奨 | 中優先度項目の対応 |
| 40-59 | 要改善 | 🟠 注意 | 高優先度項目の即座対応 |
| 0-39 | 危険 | 🔴 緊急 | 全面的な見直し |

### 評価項目と重み

| 項目 | 重み | 説明 |
|------|------|------|
| GitHub OIDC | 30% | OIDC認証の適切な設定 |
| Secrets管理 | 25% | シークレットの適切な管理 |
| アクセス制御 | 20% | 権限の適切な制限 |
| 監視 | 15% | ログ記録と監視 |
| コンプライアンス | 10% | 文書化と手順整備 |

## 🛠️ 問題対応手順

### 高優先度問題（即座対応）

1. **OIDCプロバイダー未設定**
   ```bash
   ./scripts/setup-github-oidc.sh
   ```

2. **必要なシークレット不足**
   ```bash
   ./scripts/setup-github-secrets.sh
   ```

3. **危険な権限設定**
   - IAMポリシーの見直し
   - 最小権限の原則適用

### 中優先度問題（計画的対応）

1. **未使用シークレットの整理**
   ```bash
   # 監査結果から生成されたスクリプトを実行
   ./github-secrets-audit-YYYYMMDD_HHMMSS-cleanup.sh
   ```

2. **ブランチ制限の最適化**
   - 信頼ポリシーの更新
   - 特定ブランチへの制限強化

### 低優先度問題（定期対応）

1. **文書の更新**
   - セキュリティ手順の見直し
   - 監査結果の記録

2. **監視機能の強化**
   - CloudTrail設定の確認
   - アラート設定の追加

## 📝 監査結果の記録

### 監査ログの保存

```bash
# 監査結果は自動的に以下の形式で保存されます
comprehensive-security-audit-YYYYMMDD_HHMMSS.json
comprehensive-security-audit-YYYYMMDD_HHMMSS-report.md
```

### 記録すべき情報

1. **監査実行日時**
2. **セキュリティスコア**
3. **発見された問題**
4. **実施した対応**
5. **次回監査予定**

### レポート共有

- **月次レポート**: チーム全体への共有
- **四半期レポート**: 管理層への報告
- **年次レポート**: セキュリティ方針の見直し

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. AWS CLI認証エラー

```bash
# AWS認証情報の確認
aws sts get-caller-identity

# 認証情報の再設定
aws configure
```

#### 2. GitHub CLI認証エラー

```bash
# GitHub認証状態の確認
gh auth status

# 再認証
gh auth logout
gh auth login
```

#### 3. Python環境エラー

```bash
# 仮想環境の再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

#### 4. 権限不足エラー

- **GitHub**: リポジトリの管理者権限を確認
- **AWS**: IAMユーザーの権限を確認
- **Vercel**: アカウントの権限を確認

## 📚 参考資料

### 内部文書
- [GitHub Secrets設定ガイド](./github-secrets-setup-guide.md)
- [GitHub OIDC移行ガイド](./github-oidc-migration.md)
- [セキュリティ強化ガイド](./security-enhancements.md)

### 外部リソース
- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

## 🎯 継続的改善

### 監査プロセスの改善

1. **自動化の拡張**
   - CI/CDパイプラインへの組み込み
   - 定期実行の自動化

2. **監査項目の追加**
   - 新しいセキュリティ要件への対応
   - 業界標準の取り込み

3. **レポート機能の強化**
   - ダッシュボードの作成
   - 傾向分析の追加

### チーム教育

1. **セキュリティ意識の向上**
   - 定期的な勉強会
   - セキュリティ事例の共有

2. **手順の習得**
   - 監査手順のハンズオン
   - 問題対応の演習

---

**注意**: このガイドは定期的に更新されます。最新版を確認してください。

**次回監査予定**: 毎月第1営業日に実施