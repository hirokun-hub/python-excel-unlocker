# ユーザー管理運用ガイド

## 概要

本ガイドは、Secure Excel Unlockアプリケーションのユーザーアクセス権限を管理するための包括的な運用手順書です。管理者が安全かつ効率的にユーザー管理を行うための手順、自動化スクリプト、緊急時対応方法を提供します。

## 目次

1. [ユーザー管理システムの概要](#ユーザー管理システムの概要)
2. [新規ユーザー追加手順](#新規ユーザー追加手順)
3. [ユーザー削除・無効化手順](#ユーザー削除無効化手順)
4. [緊急時アクセス権変更手順](#緊急時アクセス権変更手順)
5. [ユーザー一覧確認・監査手順](#ユーザー一覧確認監査手順)
6. [自動化スクリプトの使用方法](#自動化スクリプトの使用方法)
7. [AWS CLI直接操作手順（緊急時用）](#aws-cli直接操作手順緊急時用)
8. [トラブルシューティング](#トラブルシューティング)
9. [セキュリティベストプラクティス](#セキュリティベストプラクティス)

## ユーザー管理システムの概要

### 認証方式
- **認証プロバイダー**: Google OAuth 2.0
- **認証方式**: JWT（ID Token）による検証
- **アクセス制御**: 環境変数`ALLOWED_USERS`による招待制

### 権限管理の仕組み
```
Google OAuth認証 → JWT検証 → ALLOWED_USERSチェック → アクセス許可/拒否
```

### 環境別設定
| 環境 | スタック名 | 設定場所 |
|------|-----------|----------|
| 開発環境 | `excel-unlocker-api-development` | AWS Parameter Store |
| ステージング環境 | `excel-unlocker-api-staging` | AWS Parameter Store |
| 本番環境 | `excel-unlocker-api-production` | AWS Parameter Store |

## 新規ユーザー追加手順

### 手順1: ユーザー情報の確認

新規ユーザーを追加する前に、以下の情報を確認してください：

1. **Googleアカウントのメールアドレス** - 正確なメールアドレスを確認
2. **業務上の必要性** - アクセス権限付与の妥当性を確認
3. **承認者の確認** - 上長または管理者の承認を取得

### 手順2: 自動化スクリプトによる追加（推奨）

```bash
# ユーザー管理スクリプトを実行
./scripts/manage-users.sh add "new-user@example.com" --environment production

# 複数ユーザーを一括追加
./scripts/manage-users.sh add-batch "user1@example.com,user2@example.com" --environment production
```

### 手順3: 手動での追加手順

#### 3.1 現在のユーザーリストを確認
```bash
# AWS CLI で現在の設定を確認
aws ssm get-parameter --name "/excel-unlocker/allowed-users" --region ap-northeast-1
```

#### 3.2 新しいユーザーを追加
```bash
# 現在のリストに新しいユーザーを追加
CURRENT_USERS=$(aws ssm get-parameter --name "/excel-unlocker/allowed-users" --query "Parameter.Value" --output text --region ap-northeast-1)
NEW_USERS="${CURRENT_USERS},new-user@example.com"

# Parameter Storeを更新
aws ssm put-parameter \
  --name "/excel-unlocker/allowed-users" \
  --value "$NEW_USERS" \
  --type "String" \
  --overwrite \
  --region ap-northeast-1
```

#### 3.3 Lambda関数の環境変数を更新
```bash
# 開発環境
aws lambda update-function-configuration \
  --function-name "excel-get-upload-url-function-development" \
  --environment "Variables={ALLOWED_USERS=$NEW_USERS,S3_BUCKET_NAME=excel-unlocker-bucket-development-123456789012-ap-northeast-1,LOG_LEVEL=INFO,ENVIRONMENT=development,GOOGLE_CLIENT_ID=your-google-client-id,ALLOWED_ORIGIN=https://localhost:3000,ENABLE_BOT_PROTECTION=false}" \
  --region ap-northeast-1

aws lambda update-function-configuration \
  --function-name "excel-unlock-function-development" \
  --environment "Variables={ALLOWED_USERS=$NEW_USERS,S3_BUCKET_NAME=excel-unlocker-bucket-development-123456789012-ap-northeast-1,LOG_LEVEL=INFO,ENVIRONMENT=development,GOOGLE_CLIENT_ID=your-google-client-id,ALLOWED_ORIGIN=https://localhost:3000,ENABLE_BOT_PROTECTION=false}" \
  --region ap-northeast-1
```

### 手順4: 動作確認

```bash
# 新しいユーザーでのアクセステスト
./scripts/test-user-access.sh "new-user@example.com" --environment production
```

### 手順5: ユーザーへの通知

新規ユーザーに以下の情報を提供してください：

1. **アプリケーションURL**: https://excel-unlocker.vercel.app
2. **ログイン方法**: Googleアカウントでのログイン
3. **利用ガイド**: ユーザーマニュアルのURL
4. **サポート連絡先**: 管理者の連絡先

## ユーザー削除・無効化手順

### 手順1: 削除対象ユーザーの確認

```bash
# 現在のユーザーリストを確認
./scripts/manage-users.sh list --environment production
```

### 手順2: 自動化スクリプトによる削除（推奨）

```bash
# 単一ユーザーの削除
./scripts/manage-users.sh remove "user-to-remove@example.com" --environment production

# 複数ユーザーの一括削除
./scripts/manage-users.sh remove-batch "user1@example.com,user2@example.com" --environment production
```

### 手順3: 手動での削除手順

#### 3.1 現在のユーザーリストから対象ユーザーを除外
```bash
# 現在のリストを取得
CURRENT_USERS=$(aws ssm get-parameter --name "/excel-unlocker/allowed-users" --query "Parameter.Value" --output text --region ap-northeast-1)

# 対象ユーザーを除外した新しいリストを作成
NEW_USERS=$(echo "$CURRENT_USERS" | sed 's/user-to-remove@example.com,//g' | sed 's/,user-to-remove@example.com//g' | sed 's/user-to-remove@example.com//g')

# Parameter Storeを更新
aws ssm put-parameter \
  --name "/excel-unlocker/allowed-users" \
  --value "$NEW_USERS" \
  --type "String" \
  --overwrite \
  --region ap-northeast-1
```

#### 3.2 Lambda関数の環境変数を更新
```bash
# 本番環境の例
aws lambda update-function-configuration \
  --function-name "excel-get-upload-url-function-production" \
  --environment "Variables={ALLOWED_USERS=$NEW_USERS,S3_BUCKET_NAME=excel-unlocker-bucket-production-123456789012-ap-northeast-1,LOG_LEVEL=WARN,ENVIRONMENT=production,GOOGLE_CLIENT_ID=your-google-client-id,ALLOWED_ORIGIN=https://excel-unlocker.vercel.app,ENABLE_BOT_PROTECTION=true}" \
  --region ap-northeast-1
```

### 手順4: 削除確認

```bash
# 削除されたユーザーでのアクセステスト（アクセス拒否されることを確認）
./scripts/test-user-access.sh "user-to-remove@example.com" --environment production --expect-denied
```

## 緊急時アクセス権変更手順

### 緊急時の定義
- セキュリティインシデント発生時
- 不正アクセスの疑いがある場合
- 退職者の即座のアクセス無効化が必要な場合

### 緊急時対応手順

#### 手順1: 全ユーザーアクセス一時停止（最優先）
```bash
# 緊急時：全ユーザーアクセスを一時停止
./scripts/emergency-lockdown.sh --environment production --reason "security-incident"
```

#### 手順2: 特定ユーザーの即座無効化
```bash
# 特定ユーザーの緊急無効化
./scripts/emergency-disable-user.sh "suspicious-user@example.com" --environment production --reason "security-concern"
```

#### 手順3: 管理者のみアクセス許可
```bash
# 管理者のみに制限
aws ssm put-parameter \
  --name "/excel-unlocker/allowed-users" \
  --value "admin@example.com" \
  --type "String" \
  --overwrite \
  --region ap-northeast-1

# Lambda関数を即座に更新
./scripts/update-lambda-env.sh --environment production --users "admin@example.com"
```

#### 手順4: インシデント記録
```bash
# インシデントログの記録
./scripts/log-security-incident.sh \
  --type "user-access-emergency" \
  --affected-user "suspicious-user@example.com" \
  --action "immediate-disable" \
  --reason "security-concern" \
  --timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### 緊急時連絡先
- **主管理者**: hironomac2025@gmail.com
- **副管理者**: （設定されている場合）
- **エスカレーション先**: （組織の規定に従う）

## ユーザー一覧確認・監査手順

### 定期監査の実施

#### 月次監査手順
```bash
# 月次ユーザー監査レポートの生成
./scripts/generate-user-audit-report.sh --month $(date +%Y-%m) --environment production
```

#### 監査項目
1. **現在のアクティブユーザー数**
2. **最終アクセス日時**（CloudWatchログから抽出）
3. **権限変更履歴**
4. **異常なアクセスパターン**

### ユーザー一覧の確認方法

#### 方法1: 自動化スクリプトによる確認
```bash
# 全環境のユーザー一覧を表示
./scripts/manage-users.sh list-all

# 特定環境のユーザー一覧
./scripts/manage-users.sh list --environment production --format table
```

#### 方法2: AWS CLIによる直接確認
```bash
# Parameter Storeから直接確認
aws ssm get-parameter --name "/excel-unlocker/allowed-users" --region ap-northeast-1 --output table

# Lambda関数の環境変数から確認
aws lambda get-function-configuration --function-name "excel-unlock-function-production" --region ap-northeast-1 --query "Environment.Variables.ALLOWED_USERS"
```

### アクセスログの分析

#### CloudWatchログの確認
```bash
# 最近のアクセスログを確認
aws logs filter-log-events \
  --log-group-name "/aws/lambda/excel-unlock-function-production" \
  --start-time $(date -d '7 days ago' +%s)000 \
  --filter-pattern "Access granted" \
  --region ap-northeast-1
```

#### 異常アクセスの検出
```bash
# 異常なアクセスパターンを検出
./scripts/detect-anomalous-access.sh --environment production --days 7
```

## 自動化スクリプトの使用方法

### ユーザー管理スクリプト（manage-users.sh）

#### 基本的な使用方法
```bash
# ヘルプの表示
./scripts/manage-users.sh --help

# ユーザー追加
./scripts/manage-users.sh add "user@example.com" --environment production

# ユーザー削除
./scripts/manage-users.sh remove "user@example.com" --environment production

# ユーザー一覧表示
./scripts/manage-users.sh list --environment production

# 一括操作
./scripts/manage-users.sh add-batch "user1@example.com,user2@example.com" --environment production
```

#### 高度な使用方法
```bash
# ドライラン（実際の変更は行わない）
./scripts/manage-users.sh add "user@example.com" --environment production --dry-run

# バックアップ付きで実行
./scripts/manage-users.sh add "user@example.com" --environment production --backup

# 変更履歴の記録
./scripts/manage-users.sh add "user@example.com" --environment production --log-change
```

### 監査スクリプト（audit-users.sh）

```bash
# 基本的な監査レポート
./scripts/audit-users.sh --environment production

# 詳細な監査レポート
./scripts/audit-users.sh --environment production --detailed --output-format json

# 特定期間の監査
./scripts/audit-users.sh --environment production --start-date 2025-01-01 --end-date 2025-01-31
```

## AWS CLI直接操作手順（緊急時用）

### 前提条件
- AWS CLIがインストール・設定済み
- 適切なIAM権限を持つアカウントでログイン済み

### Parameter Storeの直接操作

#### 現在の設定確認
```bash
# 現在のALLOWED_USERSを確認
aws ssm get-parameter \
  --name "/excel-unlocker/allowed-users" \
  --region ap-northeast-1 \
  --output text \
  --query "Parameter.Value"
```

#### 設定の更新
```bash
# 新しいユーザーリストを設定
aws ssm put-parameter \
  --name "/excel-unlocker/allowed-users" \
  --value "user1@example.com,user2@example.com,user3@example.com" \
  --type "String" \
  --overwrite \
  --region ap-northeast-1
```

### Lambda関数の環境変数直接更新

#### 現在の環境変数確認
```bash
# 関数の環境変数を確認
aws lambda get-function-configuration \
  --function-name "excel-unlock-function-production" \
  --region ap-northeast-1 \
  --query "Environment.Variables"
```

#### 環境変数の更新
```bash
# ALLOWED_USERSのみを更新
aws lambda update-function-configuration \
  --function-name "excel-unlock-function-production" \
  --environment "Variables={ALLOWED_USERS=user1@example.com,S3_BUCKET_NAME=excel-unlocker-bucket-production-123456789012-ap-northeast-1,LOG_LEVEL=WARN,ENVIRONMENT=production,GOOGLE_CLIENT_ID=your-google-client-id,ALLOWED_ORIGIN=https://excel-unlocker.vercel.app,ENABLE_BOT_PROTECTION=true}" \
  --region ap-northeast-1
```

### 複数Lambda関数の一括更新

```bash
# 本番環境の全Lambda関数を更新
FUNCTIONS=("excel-get-upload-url-function-production" "excel-unlock-function-production")
NEW_USERS="user1@example.com,user2@example.com"

for FUNCTION in "${FUNCTIONS[@]}"; do
  echo "Updating $FUNCTION..."
  
  # 現在の環境変数を取得
  CURRENT_ENV=$(aws lambda get-function-configuration --function-name "$FUNCTION" --region ap-northeast-1 --query "Environment.Variables" --output json)
  
  # ALLOWED_USERSを更新
  UPDATED_ENV=$(echo "$CURRENT_ENV" | jq --arg users "$NEW_USERS" '.ALLOWED_USERS = $users')
  
  # Lambda関数を更新
  aws lambda update-function-configuration \
    --function-name "$FUNCTION" \
    --environment "Variables=$UPDATED_ENV" \
    --region ap-northeast-1
    
  echo "Updated $FUNCTION successfully"
done
```

## トラブルシューティング

### よくある問題と解決方法

#### 問題1: ユーザーがログインできない
**症状**: 正しいGoogleアカウントでログインしているが、「Access denied」エラーが表示される

**原因と解決方法**:
1. **メールアドレスの不一致**
   ```bash
   # 現在の設定を確認
   ./scripts/manage-users.sh list --environment production
   
   # ユーザーのメールアドレスを正確に確認
   # Google OAuth設定でのメールアドレスと完全一致する必要がある
   ```

2. **環境変数の更新遅延**
   ```bash
   # Lambda関数の環境変数を強制更新
   ./scripts/force-update-lambda-env.sh --environment production
   ```

3. **キャッシュの問題**
   ```bash
   # ユーザーにブラウザキャッシュのクリアを依頼
   # または、シークレットモードでのアクセスを試行
   ```

#### 問題2: 環境変数の更新が反映されない
**症状**: Parameter Storeは更新されているが、Lambda関数でアクセス拒否される

**解決方法**:
```bash
# Lambda関数の環境変数を直接確認
aws lambda get-function-configuration \
  --function-name "excel-unlock-function-production" \
  --region ap-northeast-1 \
  --query "Environment.Variables.ALLOWED_USERS"

# 必要に応じて手動で更新
./scripts/sync-lambda-env-from-ssm.sh --environment production
```

#### 問題3: 大量のユーザー管理
**症状**: ユーザー数が多くなり、管理が困難

**解決方法**:
```bash
# CSVファイルからの一括インポート
./scripts/import-users-from-csv.sh users.csv --environment production

# グループ管理機能の利用（将来実装予定）
./scripts/manage-user-groups.sh create "department-a" --users "user1@example.com,user2@example.com"
```

### ログの確認方法

#### CloudWatchログの確認
```bash
# 認証関連のログを確認
aws logs filter-log-events \
  --log-group-name "/aws/lambda/excel-unlock-function-production" \
  --filter-pattern "Access" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --region ap-northeast-1
```

#### エラーログの分析
```bash
# エラーパターンの分析
./scripts/analyze-auth-errors.sh --environment production --hours 24
```

## セキュリティベストプラクティス

### 1. 定期的な監査
- **月次**: 全ユーザーの権限確認
- **四半期**: アクセスログの詳細分析
- **年次**: セキュリティポリシーの見直し

### 2. 最小権限の原則
- 必要最小限のユーザーのみにアクセス権限を付与
- 定期的な権限の見直しと不要な権限の削除

### 3. 変更履歴の記録
```bash
# 全ての変更を記録
./scripts/manage-users.sh add "user@example.com" --environment production --log-change --reason "新規採用"
```

### 4. 緊急時対応の準備
- 緊急時連絡先の最新化
- 緊急時手順の定期的な訓練
- バックアップ管理者の指定

### 5. 自動化の活用
- 手動操作によるミスを防ぐため、可能な限り自動化スクリプトを使用
- 重要な操作には確認プロンプトを設ける

### 6. 監視とアラート
```bash
# 異常なアクセスパターンの監視設定
./scripts/setup-access-monitoring.sh --environment production --alert-email admin@example.com
```

## 付録

### A. 環境変数一覧
| 変数名 | 説明 | 例 |
|--------|------|-----|
| `ALLOWED_USERS` | 許可されたユーザーのメールアドレス（カンマ区切り） | `user1@example.com,user2@example.com` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `123456789012-abcdef.apps.googleusercontent.com` |
| `ENVIRONMENT` | デプロイ環境 | `production`, `staging`, `development` |
| `ALLOWED_ORIGIN` | 許可されたCORSオリジン | `https://excel-unlocker.vercel.app` |

### B. AWS リソース一覧
| リソース | 名前パターン | 説明 |
|----------|-------------|------|
| Lambda関数 | `excel-*-function-{environment}` | Excel処理用Lambda関数 |
| S3バケット | `excel-unlocker-bucket-{environment}-{account}-{region}` | ファイル保存用バケット |
| Parameter Store | `/excel-unlocker/allowed-users` | ユーザーリスト保存 |

### C. 関連ドキュメント
- [認証・API統合ガイド](authentication-integration-guide.md)
- [セキュリティ強化実装ガイド](security-enhancements.md)
- [デプロイメントガイド](deployment-guide.md)
- [トラブルシューティング診断ガイド](troubleshooting-diagnostic-guide.md)

---

**最終更新**: 2025年1月19日  
**バージョン**: 1.0  
**作成者**: システム管理者  
**承認者**: プロジェクト責任者