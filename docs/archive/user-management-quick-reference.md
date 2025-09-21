# ユーザー管理クイックリファレンス

## 🚀 よく使うコマンド

### 新規ユーザー追加
```bash
# 基本的な追加
./scripts/manage-users.sh add "user@example.com" --environment production

# バックアップ付きで追加
./scripts/manage-users.sh add "user@example.com" --environment production --backup --reason "新規採用"

# 複数ユーザーを一括追加
./scripts/manage-users.sh add-batch "user1@example.com,user2@example.com" --environment production
```

### ユーザー削除
```bash
# 基本的な削除
./scripts/manage-users.sh remove "user@example.com" --environment production

# ログ記録付きで削除
./scripts/manage-users.sh remove "user@example.com" --environment production --log-change --reason "退職"
```

### ユーザー一覧確認
```bash
# 表形式で表示
./scripts/manage-users.sh list --environment production --format table

# 全環境の一覧
./scripts/manage-users.sh list-all --format table
```

### アクセステスト
```bash
# ユーザーのアクセス権限をテスト
./scripts/test-user-access.sh "user@example.com" --environment production

# 削除されたユーザーのテスト（アクセス拒否を確認）
./scripts/test-user-access.sh "removed-user@example.com" --environment production --expect-denied
```

## 🚨 緊急時対応

### 全ユーザーアクセス停止
```bash
./scripts/emergency-user-management.sh lockdown --environment production --reason "security-incident"
```

### 特定ユーザーの即座無効化
```bash
./scripts/emergency-user-management.sh disable-user "suspicious@example.com" --environment production --reason "unauthorized-access"
```

### 管理者のみアクセス許可
```bash
./scripts/emergency-user-management.sh admin-only --environment production --force
```

### 緊急状態の確認
```bash
./scripts/emergency-user-management.sh status --environment production
```

### 緊急ロックダウンの解除
```bash
./scripts/emergency-user-management.sh unlock --environment production
```

## 📊 監査・レポート

### 基本的な監査レポート
```bash
./scripts/audit-users.sh --environment production --output-format html
```

### 詳細な監査レポート
```bash
./scripts/audit-users.sh --environment production --detailed --include-logs --output-format html
```

### 全環境の監査
```bash
./scripts/audit-users.sh --environment all --output-format json
```

## 🔧 設定確認・メンテナンス

### 設定の妥当性検証
```bash
./scripts/manage-users.sh validate --environment production
```

### バックアップ作成
```bash
./scripts/manage-users.sh backup --environment production
```

### 現在の設定をAWS CLIで直接確認
```bash
# Parameter Store確認
aws ssm get-parameter --name "/excel-unlocker/allowed-users" --region ap-northeast-1

# Lambda関数の環境変数確認
aws lambda get-function-configuration --function-name "excel-unlock-function-production" --region ap-northeast-1 --query "Environment.Variables.ALLOWED_USERS"
```

## 📋 チェックリスト

### 新規ユーザー追加時
- [ ] Googleアカウントのメールアドレスを正確に確認
- [ ] 業務上の必要性を確認
- [ ] 上長の承認を取得
- [ ] バックアップ付きで追加実行
- [ ] アクセステストで動作確認
- [ ] ユーザーに利用方法を通知

### ユーザー削除時
- [ ] 削除対象ユーザーを確認
- [ ] 削除理由を記録
- [ ] バックアップ付きで削除実行
- [ ] アクセステストで削除確認
- [ ] 関係者に削除完了を通知

### 緊急時対応
- [ ] インシデントの性質を確認
- [ ] 適切な緊急コマンドを選択
- [ ] 実行前に影響範囲を確認
- [ ] 緊急対応を実行
- [ ] インシデントログを記録
- [ ] 関係者に状況を報告

### 定期監査
- [ ] 月次監査レポートを生成
- [ ] ユーザー一覧の妥当性を確認
- [ ] 不要なユーザーがないかチェック
- [ ] セキュリティ問題がないか確認
- [ ] 監査結果を記録・保管

## 🔗 関連ファイル

### スクリプト
- `scripts/manage-users.sh` - メインのユーザー管理スクリプト
- `scripts/emergency-user-management.sh` - 緊急時対応スクリプト
- `scripts/test-user-access.sh` - アクセステストスクリプト
- `scripts/audit-users.sh` - 監査レポート生成スクリプト

### ドキュメント
- `docs/user-management-operations-guide.md` - 詳細な運用ガイド
- `docs/authentication-integration-guide.md` - 認証システムガイド
- `docs/troubleshooting-diagnostic-guide.md` - トラブルシューティングガイド

### ログファイル
- `logs/user-management.log` - ユーザー管理操作ログ
- `logs/emergency-user-management.log` - 緊急時対応ログ
- `logs/user-changes.log` - ユーザー変更履歴
- `logs/user-access-test.log` - アクセステストログ
- `logs/user-audit.log` - 監査ログ

### バックアップ・レポート
- `backups/user-management/` - 通常のバックアップファイル
- `backups/emergency/` - 緊急時バックアップファイル
- `reports/` - 監査レポートファイル

## ⚠️ 重要な注意事項

1. **本番環境での操作は慎重に**: 必ずドライランで確認してから実行
2. **バックアップの重要性**: 重要な変更前には必ずバックアップを作成
3. **緊急時の連絡**: 緊急対応後は必ず関係者に報告
4. **定期監査の実施**: 月次での監査を欠かさず実行
5. **ログの確認**: 操作後は必ずログで結果を確認

## 📞 サポート・連絡先

- **主管理者**: hironomac2025@gmail.com
- **緊急時連絡先**: （組織の規定に従う）
- **ドキュメント**: `docs/user-management-operations-guide.md`

---

**最終更新**: 2025年1月19日  
**バージョン**: 1.0