# トラブルシューティング診断ガイド

## 🔍 概要

Excel Unlocker セットアップ・運用時に発生する問題の**体系的な診断フロー**と**解決方法**を提供します。問題を素早く特定し、効率的に解決するためのガイドです。

---

## 🚨 緊急時クイック診断（5分以内）

### 症状別クイック診断

#### 🔴 アプリが全く動かない
```bash
# 1. 基本接続確認（30秒）
curl -I https://your-domain.com
# → 200 OK が返るか確認

# 2. DNS確認（30秒）
nslookup your-domain.com
# → 正しいIPアドレスが返るか確認

# 3. SSL証明書確認（30秒）
curl -I https://your-domain.com
# → SSL エラーがないか確認
```

**即座に確認すべき項目**:
- [ ] Vercel デプロイメント状況
- [ ] ドメイン設定
- [ ] DNS伝播状況
- [ ] SSL証明書の有効性

#### 🟡 ログインできない
```bash
# 1. Google OAuth設定確認（1分）
# Google Cloud Console → 認証情報 → OAuth クライアントID
# - JavaScript生成元に現在のドメインが含まれているか
# - リダイレクトURIが正確か

# 2. 環境変数確認（1分）
# Vercel → Settings → Environment Variables
# - GOOGLE_CLIENT_ID が設定されているか
# - NEXTAUTH_URL が正しいか
# - NEXTAUTH_SECRET が設定されているか
```

**即座に確認すべき項目**:
- [ ] Google OAuth設定
- [ ] Vercel環境変数
- [ ] ブラウザのCookie設定
- [ ] ネットワーク接続

#### 🟠 ファイル処理が失敗する
```bash
# 1. API接続確認（1分）
curl -X GET https://your-api-gateway-url/health
# → API Gateway が応答するか確認

# 2. Lambda関数確認（1分）
# AWS Console → Lambda → 関数一覧
# - 関数が存在するか
# - 最近のエラーログがないか

# 3. S3バケット確認（1分）
aws s3 ls s3://your-bucket-name
# → バケットにアクセスできるか確認
```

**即座に確認すべき項目**:
- [ ] API Gateway の状態
- [ ] Lambda関数の実行状況
- [ ] S3バケットのアクセス権限
- [ ] ファイルサイズ制限

---

## 🔧 段階的診断フロー

### レベル1: 基本接続診断（5-10分）

#### ステップ1: フロントエンド接続確認
```bash
# 1. サイトアクセス確認
curl -I https://your-domain.com
# 期待値: HTTP/2 200

# 2. 静的リソース確認
curl -I https://your-domain.com/_next/static/
# 期待値: HTTP/2 200 または 404（正常）

# 3. API ルート確認
curl -I https://your-domain.com/api/auth/session
# 期待値: HTTP/2 200
```

**診断結果の判定**:
- ✅ すべて200: フロントエンド正常
- ❌ 404/500: Vercelデプロイメント問題
- ❌ DNS_PROBE_FINISHED_NXDOMAIN: DNS設定問題
- ❌ SSL_ERROR: 証明書問題

#### ステップ2: バックエンド接続確認
```bash
# 1. API Gateway 確認
curl -X GET https://your-api-gateway-url/
# 期待値: {"message": "Forbidden"} または CORS エラー（正常）

# 2. 署名付きURL生成確認
curl -X POST https://your-api-gateway-url/presigned-urls \
  -H "Content-Type: application/json" \
  -H "X-User-Email: your-email@example.com" \
  -d '{"fileName":"test.xlsx","fileSize":1024,"contentType":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}'
# 期待値: {"uploadUrl": "...", "fileKey": "..."}

# 3. Lambda関数直接確認
aws lambda invoke --function-name excel-unlock-function-production \
  --payload '{"test": true}' response.json
cat response.json
# 期待値: 正常なレスポンス
```

**診断結果の判定**:
- ✅ 正常なレスポンス: バックエンド正常
- ❌ 403 Forbidden: 認証・認可問題
- ❌ 500 Internal Server Error: Lambda関数問題
- ❌ タイムアウト: Lambda設定問題

### レベル2: 認証・認可診断（10-15分）

#### ステップ1: Google OAuth設定診断
```bash
# 1. OAuth設定確認スクリプト
cat > check_oauth.js << 'EOF'
const clientId = process.env.GOOGLE_CLIENT_ID;
const redirectUri = process.env.NEXTAUTH_URL + '/api/auth/callback/google';

console.log('Client ID:', clientId);
console.log('Redirect URI:', redirectUri);
console.log('OAuth URL:', `https://accounts.google.com/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid%20email%20profile`);
EOF

node check_oauth.js
```

**確認項目**:
- [ ] GOOGLE_CLIENT_ID が正しく設定されている
- [ ] リダイレクトURIが Google Cloud Console の設定と一致
- [ ] OAuth URL にアクセスして認証画面が表示される

#### ステップ2: セッション管理診断
```bash
# 1. NextAuth設定確認
curl -X GET https://your-domain.com/api/auth/providers
# 期待値: {"google": {...}}

# 2. セッション確認
curl -X GET https://your-domain.com/api/auth/session \
  -H "Cookie: next-auth.session-token=your-session-token"
# 期待値: {"user": {...}} または null

# 3. CSRF トークン確認
curl -X GET https://your-domain.com/api/auth/csrf
# 期待値: {"csrfToken": "..."}
```

#### ステップ3: バックエンド認証診断
```bash
# 1. 許可ユーザーリスト確認
aws lambda get-function-configuration \
  --function-name excel-unlock-function-production \
  --query 'Environment.Variables.ALLOWED_USERS'
# 期待値: "user1@example.com,user2@example.com"

# 2. 認証ヘッダーテスト
curl -X POST https://your-api-gateway-url/presigned-urls \
  -H "Content-Type: application/json" \
  -H "X-User-Email: unauthorized@example.com" \
  -d '{"fileName":"test.xlsx","fileSize":1024,"contentType":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}'
# 期待値: 403 Forbidden
```

### レベル3: ファイル処理診断（15-20分）

#### ステップ1: S3アクセス診断
```bash
# 1. バケット存在確認
aws s3 ls s3://your-bucket-name/
# 期待値: バケット内容の一覧（空でも可）

# 2. バケットポリシー確認
aws s3api get-bucket-policy --bucket your-bucket-name
# 期待値: 適切なポリシー設定

# 3. CORS設定確認
aws s3api get-bucket-cors --bucket your-bucket-name
# 期待値: フロントエンドドメインを許可するCORS設定

# 4. 署名付きURL動作確認
# 生成されたuploadUrlに実際にファイルをアップロード
curl -X PUT "generated-upload-url" \
  --data-binary @test-file.xlsx \
  -H "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# 期待値: 200 OK
```

#### ステップ2: Lambda関数診断
```bash
# 1. 関数設定確認
aws lambda get-function-configuration \
  --function-name excel-unlock-function-production
# 確認項目: Timeout, Memory, Environment Variables

# 2. 最近のログ確認
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/excel"

aws logs tail /aws/lambda/excel-unlock-function-production \
  --since 1h --follow
# 確認項目: エラーメッセージ, 実行時間, メモリ使用量

# 3. テストイベント実行
aws lambda invoke \
  --function-name excel-unlock-function-production \
  --payload file://test-event.json \
  response.json
cat response.json
```

#### ステップ3: Excel処理診断
```bash
# 1. msoffcrypto-tool動作確認（ローカル）
cd backend
python3 -c "
import msoffcrypto
print('msoffcrypto-tool version:', msoffcrypto.__version__)
"

# 2. テストファイルでの処理確認
python3 -c "
import msoffcrypto
import io

# テストファイルを作成
with open('test.xlsx', 'rb') as f:
    file = msoffcrypto.OfficeFile(f)
    print('File is encrypted:', file.is_encrypted())
"
```

---

## 📊 エラーパターン別対処法

### Google OAuth エラー

#### `redirect_uri_mismatch`
```
🔍 原因: リダイレクトURIが Google Cloud Console に登録されていない

✅ 解決方法:
1. Google Cloud Console → APIとサービス → 認証情報
2. OAuth クライアントIDを編集
3. 承認済みのリダイレクトURIに以下を追加:
   - https://your-domain.com/api/auth/callback/google
   - https://*.vercel.app/api/auth/callback/google

🔧 確認コマンド:
curl -X GET "https://accounts.google.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https://your-domain.com/api/auth/callback/google&response_type=code&scope=openid%20email%20profile"
```

#### `origin_mismatch`
```
🔍 原因: JavaScript生成元が登録されていない

✅ 解決方法:
1. OAuth クライアントIDを編集
2. 承認済みのJavaScript生成元に以下を追加:
   - https://your-domain.com
   - https://*.vercel.app

🔧 確認方法:
ブラウザの開発者ツールでConsoleエラーを確認
```

#### `access_denied`
```
🔍 原因: テストユーザーに登録されていない

✅ 解決方法:
1. Google Cloud Console → APIとサービス → OAuth 同意画面
2. テストユーザーセクションでユーザーを追加
3. 本番公開する場合は審査申請が必要

🔧 確認方法:
OAuth同意画面の設定を確認
```

### AWS エラー

#### `AccessDenied`
```
🔍 原因: IAM権限不足

✅ 解決方法:
1. IAMユーザーのポリシーを確認
2. 必要な権限を追加:
   - CloudFormation: Full Access
   - Lambda: Full Access
   - S3: Bucket Access
   - IAM: PassRole

🔧 確認コマンド:
aws iam list-attached-user-policies --user-name github-deploy-bot
aws iam get-policy-version --policy-arn arn:aws:iam::account:policy/ExcelUnlockerDeployPolicy --version-id v1
```

#### `BucketAlreadyExists`
```
🔍 原因: S3バケット名が既に使用されている

✅ 解決方法:
1. template.yaml のバケット名を変更
2. アカウントIDやタイムスタンプを含む一意な名前に変更:
   excel-unlocker-bucket-production-{account-id}-{timestamp}

🔧 確認コマンド:
aws s3 ls | grep excel-unlocker
```

#### `LambdaTimeout`
```
🔍 原因: Lambda関数の実行時間制限

✅ 解決方法:
1. template.yaml でTimeout値を増加:
   Timeout: 900  # 15分
2. メモリサイズを増加:
   MemorySize: 1024  # 1GB

🔧 確認コマンド:
aws lambda get-function-configuration --function-name excel-unlock-function-production
```

### Vercel エラー

#### `Build failed`
```
🔍 原因: 環境変数未設定またはビルドエラー

✅ 解決方法:
1. Vercel → Settings → Environment Variables で必要な変数を確認
2. ビルドログを確認してエラー箇所を特定
3. 依存関係の問題の場合は package.json を確認

🔧 確認方法:
Vercel ダッシュボードの Deployments タブでビルドログを確認
```

#### `Domain verification failed`
```
🔍 原因: DNS設定が正しくない

✅ 解決方法:
1. ドメインプロバイダーでCNAMEレコードを確認
2. 設定: app.example.com CNAME cname.vercel-dns.com
3. DNS伝播を待つ（最大48時間）

🔧 確認コマンド:
nslookup app.example.com
dig app.example.com CNAME
```

#### `Function timeout`
```
🔍 原因: Vercel Serverless Function のタイムアウト

✅ 解決方法:
1. vercel.json で関数のタイムアウトを設定:
{
  "functions": {
    "pages/api/**/*.js": {
      "maxDuration": 30
    }
  }
}

🔧 確認方法:
Vercel Function ログでタイムアウトエラーを確認
```

### GitHub Actions エラー

#### `Secret not found`
```
🔍 原因: Repository Secret の名前が間違っている

✅ 解決方法:
1. GitHub → Settings → Secrets and variables → Actions
2. Secret名を正確に確認（大文字小文字、アンダースコア）
3. ワークフローファイルでの参照名と一致させる

🔧 確認方法:
GitHub Actions のログで参照しているSecret名を確認
```

#### `AWS credentials not found`
```
🔍 原因: AWS認証情報が正しく設定されていない

✅ 解決方法:
1. AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY を確認
2. IAMユーザーのアクセスキーが有効か確認
3. 必要に応じて新しいアクセスキーを生成

🔧 確認コマンド:
aws sts get-caller-identity --profile github-actions
```

#### `Vercel deployment failed`
```
🔍 原因: Vercel認証またはプロジェクト設定エラー

✅ 解決方法:
1. VERCEL_TOKEN の有効性を確認
2. VERCEL_ORG_ID と VERCEL_PROJECT_ID を確認
3. Vercel CLI でローカルテスト:
   vercel --token $VERCEL_TOKEN

🔧 確認方法:
GitHub Actions ログでVercel CLIの出力を確認
```

---

## 🔍 高度な診断ツール

### ログ分析スクリプト

#### CloudWatch ログ分析
```bash
#!/bin/bash
# cloudwatch-log-analyzer.sh

FUNCTION_NAME="excel-unlock-function-production"
LOG_GROUP="/aws/lambda/$FUNCTION_NAME"

echo "=== 最近1時間のエラーログ ==="
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --start-time $(date -d "1 hour ago" +%s)000 \
  --filter-pattern "ERROR" \
  --query 'events[*].[timestamp,message]' \
  --output table

echo "=== パフォーマンス統計 ==="
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP" \
  --start-time $(date -d "1 hour ago" +%s)000 \
  --filter-pattern "REPORT" \
  --query 'events[*].message' \
  --output text | \
  grep -o 'Duration: [0-9.]*' | \
  awk '{sum+=$2; count++} END {print "平均実行時間:", sum/count "ms"}'
```

#### Vercel デプロイメント分析
```bash
#!/bin/bash
# vercel-deployment-analyzer.sh

PROJECT_ID="your-project-id"

echo "=== 最近のデプロイメント ==="
vercel deployments list --token $VERCEL_TOKEN

echo "=== 失敗したデプロイメント ==="
vercel deployments list --token $VERCEL_TOKEN | grep ERROR

echo "=== ビルドログ取得 ==="
DEPLOYMENT_ID=$(vercel deployments list --token $VERCEL_TOKEN | head -2 | tail -1 | awk '{print $1}')
vercel logs $DEPLOYMENT_ID --token $VERCEL_TOKEN
```

### 統合ヘルスチェック

#### 全体ヘルスチェックスクリプト
```bash
#!/bin/bash
# health-check.sh

echo "🔍 Excel Unlocker ヘルスチェック開始"
echo "=================================="

# 1. フロントエンド確認
echo "1. フロントエンド接続確認..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://your-domain.com)
if [ "$FRONTEND_STATUS" = "200" ]; then
  echo "✅ フロントエンド: 正常"
else
  echo "❌ フロントエンド: エラー (HTTP $FRONTEND_STATUS)"
fi

# 2. API Gateway確認
echo "2. API Gateway接続確認..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://your-api-gateway-url/)
if [ "$API_STATUS" = "403" ] || [ "$API_STATUS" = "200" ]; then
  echo "✅ API Gateway: 正常"
else
  echo "❌ API Gateway: エラー (HTTP $API_STATUS)"
fi

# 3. Lambda関数確認
echo "3. Lambda関数確認..."
LAMBDA_STATUS=$(aws lambda get-function --function-name excel-unlock-function-production --query 'Configuration.State' --output text 2>/dev/null)
if [ "$LAMBDA_STATUS" = "Active" ]; then
  echo "✅ Lambda関数: 正常"
else
  echo "❌ Lambda関数: エラー ($LAMBDA_STATUS)"
fi

# 4. S3バケット確認
echo "4. S3バケット確認..."
S3_STATUS=$(aws s3 ls s3://your-bucket-name/ 2>/dev/null && echo "OK" || echo "ERROR")
if [ "$S3_STATUS" = "OK" ]; then
  echo "✅ S3バケット: 正常"
else
  echo "❌ S3バケット: エラー"
fi

# 5. Google OAuth確認
echo "5. Google OAuth確認..."
OAUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/api/auth/providers)
if [ "$OAUTH_STATUS" = "200" ]; then
  echo "✅ Google OAuth: 正常"
else
  echo "❌ Google OAuth: エラー (HTTP $OAUTH_STATUS)"
fi

echo "=================================="
echo "🎯 ヘルスチェック完了"
```

---

## 📞 エスカレーション手順

### レベル1: 自己解決（30分以内）
1. このガイドの該当セクションを確認
2. クイック診断を実行
3. よくあるエラーパターンと照合
4. 基本的な設定を再確認

### レベル2: コミュニティサポート（1-2時間）
1. Stack Overflow で類似問題を検索
2. GitHub Issues で関連する問題を確認
3. Discord/Slack コミュニティで質問
4. 公式ドキュメントの最新情報を確認

### レベル3: 専門サポート（1日以内）
1. 各サービスの公式サポートに連絡
2. 詳細なログとエラーメッセージを準備
3. 再現手順を明確に記述
4. 環境情報（OS、ブラウザ、バージョン）を提供

### 緊急時対応（即座）
1. サービス停止の場合は即座にロールバック
2. セキュリティ問題の場合は該当機能を無効化
3. データ損失の可能性がある場合は即座に調査
4. ユーザーへの影響を最小限に抑える措置を実施

---

## 📋 診断チェックリスト

### 事前確認項目
- [ ] 問題の発生時刻を記録
- [ ] 影響範囲を特定（全ユーザー/特定ユーザー/特定機能）
- [ ] エラーメッセージを正確に記録
- [ ] 再現手順を明確化
- [ ] 最近の変更内容を確認

### 基本診断項目
- [ ] フロントエンド接続確認
- [ ] バックエンド接続確認
- [ ] 認証システム確認
- [ ] データベース/ストレージ確認
- [ ] 外部サービス連携確認

### 詳細診断項目
- [ ] ログファイル分析
- [ ] パフォーマンス指標確認
- [ ] セキュリティ設定確認
- [ ] 依存関係確認
- [ ] 環境変数確認

### 解決後確認項目
- [ ] 問題の根本原因を特定
- [ ] 修正内容を文書化
- [ ] 再発防止策を検討
- [ ] 監視・アラート設定を見直し
- [ ] 関係者への報告

---

**🎯 このガイドを使用して、問題を体系的に診断し、効率的に解決してください！**