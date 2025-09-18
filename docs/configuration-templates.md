# 設定値テンプレート集

## 📋 概要

Excel Unlocker セットアップ時に使用する**コピー&ペースト可能な設定値テンプレート**を提供します。各サービスの設定画面で直接使用できる形式で記載しています。

> **⚠️ 重要**: テンプレート内の `your-*` や `example.com` などは実際の値に置き換えてください。

---

## 🔐 Google Cloud Console 設定テンプレート

### OAuth 同意画面設定

#### アプリ情報
```
アプリ名: Secure Excel Unlock
ユーザーサポートメール: your-email@example.com
アプリのロゴ: （任意）
アプリドメイン: your-domain.com
承認済みドメイン: 
  your-domain.com
  vercel.app
デベロッパーの連絡先情報: your-email@example.com
```

#### スコープ設定
```
選択するスコープ:
  ✅ ../auth/userinfo.email
  ✅ ../auth/userinfo.profile
  ✅ openid
  ✅ ../auth/drive.file
```

#### テストユーザー
```
テストユーザーのメールアドレス:
  your-email@example.com
  user2@example.com
  user3@example.com
```

### OAuth クライアントID設定

#### 基本設定
```
アプリケーションの種類: ウェブアプリケーション
名前: secure-excel-unlock-web-client
```

#### 承認済みのJavaScript生成元
```
https://your-domain.com
https://*.vercel.app
http://localhost:3000
http://localhost:3001
```

#### 承認済みのリダイレクトURI
```
https://your-domain.com/api/auth/callback/google
https://*.vercel.app/api/auth/callback/google
http://localhost:3000/api/auth/callback/google
http://localhost:3001/api/auth/callback/google
```

---

## ☁️ AWS 設定テンプレート

### IAM ユーザー設定

#### ユーザー基本情報
```
ユーザー名: github-deploy-bot
アクセスの種類: ✅ プログラムによるアクセス
AWS Management Console へのアクセス: ❌ チェックしない
```

### IAM ポリシー（JSON）

#### 最小権限ポリシー
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:CreateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeChangeSet",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:GetTemplate",
        "cloudformation:UpdateStack",
        "cloudformation:ValidateTemplate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:DeleteObject",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutBucketCORS",
        "s3:PutBucketPolicy",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::excel-unlocker-*",
        "arn:aws:s3:::excel-unlocker-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListTags",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:*:function:excel-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:DELETE",
        "apigateway:GET",
        "apigateway:PATCH",
        "apigateway:POST",
        "apigateway:PUT"
      ],
      "Resource": "arn:aws:apigateway:ap-northeast-1::*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:AttachRolePolicy",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:DetachRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "iam:TagRole"
      ],
      "Resource": "arn:aws:iam::*:role/excel-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "arn:aws:logs:ap-northeast-1:*:log-group:/aws/lambda/excel-*"
    }
  ]
}
```

#### ポリシー情報
```
ポリシー名: ExcelUnlockerDeployPolicy
説明: Excel Unlocker deployment policy with minimal permissions
```

### S3 バケット設定

#### バケット基本設定
```
バケット名: excel-unlocker-bucket-production-{account-id}-ap-northeast-1
リージョン: アジアパシフィック (東京) ap-northeast-1
オブジェクト所有者: ACL無効（推奨）
パブリックアクセス設定: ✅ パブリックアクセスをすべてブロック
バケットのバージョニング: 無効
デフォルト暗号化: Amazon S3 マネージドキー (SSE-S3)
```

#### バケットポリシー（JSON）
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::excel-unlocker-bucket-production-{account-id}-ap-northeast-1",
        "arn:aws:s3:::excel-unlocker-bucket-production-{account-id}-ap-northeast-1/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

#### CORS設定（JSON）
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedOrigins": [
      "https://your-domain.com",
      "https://*.vercel.app",
      "http://localhost:3000",
      "http://localhost:3001"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

---

## 🚀 Vercel 設定テンプレート

### プロジェクト基本設定

#### プロジェクト情報
```
Project Name: excel-unlocker
Framework Preset: Next.js
Root Directory: frontend
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Development Command: npm run dev
```

### 環境変数設定

#### Production 環境変数
```
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/prod
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your-generated-secret-32-chars-long
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

#### Preview 環境変数
```
NEXT_PUBLIC_API_URL=https://staging-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/staging
NEXTAUTH_URL=https://*.vercel.app
NEXTAUTH_SECRET=your-generated-secret-32-chars-long
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

#### Development 環境変数
```
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-generated-secret-32-chars-long
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

### ドメイン設定

#### カスタムドメイン
```
ドメイン: app.example.com
DNS設定: CNAME app.example.com cname.vercel-dns.com
SSL証明書: 自動生成（Let's Encrypt）
```

### Build & Development Settings

#### ビルド設定
```
Framework Preset: Next.js
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Development Command: npm run dev
Root Directory: frontend
```

---

## 🔧 GitHub 設定テンプレート

### Repository Secrets

#### AWS関連
```
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=ap-northeast-1
```

#### Vercel関連
```
VERCEL_TOKEN=vc_1234567890abcdef_example_only
VERCEL_ORG_ID=team_7g8h9i0j_example
VERCEL_PROJECT_ID=prj_KLMNoP123_example
```

#### Google OAuth関連
```
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

#### NextAuth関連
```
NEXTAUTH_SECRET=your-generated-secret-32-chars-long
```

#### アプリケーション設定
```
ALLOWED_USERS=your-email@example.com,user2@example.com,user3@example.com
S3_BUCKET_NAME=excel-unlocker-bucket-production-{account-id}-ap-northeast-1
```

### GitHub Actions ワークフロー設定

#### 環境設定（Environments）
```
Environment Name: production
Protection Rules: ✅ Required reviewers (1)
Environment Secrets: 本番用の機密情報
Environment Variables: 本番用の設定値

Environment Name: staging  
Protection Rules: なし
Environment Secrets: ステージング用の機密情報
Environment Variables: ステージング用の設定値

Environment Name: development
Protection Rules: なし
Environment Secrets: 開発用の機密情報
Environment Variables: 開発用の設定値
```

---

## 🛠️ ローカル開発環境テンプレート

### .env.local（フロントエンド）
```bash
# NextAuth設定
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-generated-secret-32-chars-long

# Google OAuth設定
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz

# API設定
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_USE_MOCK_API=false

# デバッグ設定
NODE_ENV=development
NEXT_PUBLIC_DEBUG=true
```

### .env.local（バックエンド）
```bash
# AWS設定
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=excel-unlocker-bucket-development-{account-id}-ap-northeast-1

# アプリケーション設定
ALLOWED_USERS=your-email@example.com,user2@example.com
LOG_LEVEL=DEBUG

# Lambda設定
LAMBDA_TIMEOUT=900
LAMBDA_MEMORY_SIZE=1024
```

### samconfig.toml
```toml
version = 0.1

[default]
[default.global]
[default.global.parameters]
stack_name = "excel-unlocker-api-dev"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket-{random}"
s3_prefix = "excel-unlocker-api"
region = "ap-northeast-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
parameter_overrides = [
  "Environment=development",
  "AllowedUsers=your-email@example.com",
  "S3BucketName=excel-unlocker-bucket-development-{account-id}-ap-northeast-1"
]

[staging]
[staging.global]
[staging.global.parameters]
stack_name = "excel-unlocker-api-staging"
parameter_overrides = [
  "Environment=staging",
  "AllowedUsers=your-email@example.com,staging-user@example.com",
  "S3BucketName=excel-unlocker-bucket-staging-{account-id}-ap-northeast-1"
]

[production]
[production.global]
[production.global.parameters]
stack_name = "excel-unlocker-api-prod"
parameter_overrides = [
  "Environment=production",
  "AllowedUsers=your-email@example.com,user2@nsc.co.jp,user3@nsc.co.jp",
  "S3BucketName=excel-unlocker-bucket-production-{account-id}-ap-northeast-1"
]
```

---

## 📱 モバイル・レスポンシブ設定

### Viewport設定
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
```

### PWA設定（manifest.json）
```json
{
  "name": "Secure Excel Unlock",
  "short_name": "Excel Unlock",
  "description": "パスワード付きExcelファイルを安全に解除",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

---

## 🔒 セキュリティ設定テンプレート

### Content Security Policy
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline' https://accounts.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://accounts.google.com https://*.execute-api.ap-northeast-1.amazonaws.com; frame-src https://accounts.google.com;
```

### CORS設定（API Gateway）
```yaml
Cors:
  AllowMethods: "'GET,POST,OPTIONS'"
  AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-User-Email'"
  AllowOrigin: "'https://your-domain.com,https://*.vercel.app'"
  AllowCredentials: true
  MaxAge: "'600'"
```

### Security Headers
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 🧪 テスト設定テンプレート

### Jest設定（jest.config.js）
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

### Playwright設定（playwright.config.ts）
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 📊 監視・アラート設定テンプレート

### CloudWatch アラーム設定
```json
{
  "AlarmName": "ExcelUnlocker-HighErrorRate",
  "AlarmDescription": "Excel Unlocker Lambda function error rate is high",
  "MetricName": "Errors",
  "Namespace": "AWS/Lambda",
  "Statistic": "Sum",
  "Period": 300,
  "EvaluationPeriods": 2,
  "Threshold": 5,
  "ComparisonOperator": "GreaterThanThreshold",
  "Dimensions": [
    {
      "Name": "FunctionName",
      "Value": "excel-unlock-function-production"
    }
  ],
  "AlarmActions": [
    "arn:aws:sns:ap-northeast-1:123456789012:excel-unlocker-alerts"
  ]
}
```

### SNS トピック設定
```json
{
  "TopicArn": "arn:aws:sns:ap-northeast-1:123456789012:excel-unlocker-alerts",
  "DisplayName": "Excel Unlocker Alerts",
  "Subscription": [
    {
      "Protocol": "email",
      "Endpoint": "admin@example.com"
    }
  ]
}
```

---

## 🔄 バックアップ・復旧設定テンプレート

### 設定値バックアップスクリプト
```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="./config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔄 設定値バックアップ開始..."

# GitHub Secrets
echo "GitHub Secrets:" > "$BACKUP_DIR/github-secrets.txt"
gh secret list >> "$BACKUP_DIR/github-secrets.txt"

# Vercel環境変数
echo "Vercel Environment Variables:" > "$BACKUP_DIR/vercel-env.txt"
vercel env ls >> "$BACKUP_DIR/vercel-env.txt"

# AWS設定
echo "AWS Lambda Functions:" > "$BACKUP_DIR/aws-config.txt"
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `excel`)].FunctionName' >> "$BACKUP_DIR/aws-config.txt"

echo "AWS S3 Buckets:" >> "$BACKUP_DIR/aws-config.txt"
aws s3 ls | grep excel-unlocker >> "$BACKUP_DIR/aws-config.txt"

# Google OAuth設定（手動確認用）
echo "Google OAuth設定確認項目:" > "$BACKUP_DIR/google-oauth-checklist.txt"
cat << 'EOF' >> "$BACKUP_DIR/google-oauth-checklist.txt"
□ OAuth同意画面設定
□ クライアントID設定
□ JavaScript生成元設定
□ リダイレクトURI設定
□ スコープ設定
□ テストユーザー設定
EOF

echo "✅ バックアップ完了: $BACKUP_DIR"
```

### 復旧手順チェックリスト
```
🚨 緊急復旧手順:

1. サービス停止確認
   □ 影響範囲の特定
   □ ユーザーへの通知

2. 原因調査
   □ ログ確認
   □ 最近の変更確認
   □ 外部サービス状況確認

3. 復旧作業
   □ 設定値の復元
   □ デプロイメントのロールバック
   □ データベース復旧（該当する場合）

4. 動作確認
   □ 基本機能テスト
   □ 認証機能テスト
   □ ファイル処理テスト

5. サービス再開
   □ 段階的な再開
   □ 監視強化
   □ ユーザーへの復旧通知

6. 事後対応
   □ 根本原因分析
   □ 再発防止策の実施
   □ ドキュメント更新
```

---

## 📚 設定値生成ツール

### NEXTAUTH_SECRET生成
```bash
# macOS/Linux
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"

# Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### S3バケット名生成
```bash
# アカウントIDを含む一意な名前
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
echo "excel-unlocker-bucket-production-${ACCOUNT_ID}-ap-northeast-1"
```

### API Gateway URL確認
```bash
# デプロイ済みのAPI Gateway URL取得
aws apigateway get-rest-apis --query 'items[?name==`excel-unlocker-api-prod`].{id:id,name:name}' --output table
```

---

**📋 これらのテンプレートを使用して、効率的に設定を行ってください！**

> **💡 ヒント**: 実際の値に置き換える際は、セキュリティを考慮して機密情報の取り扱いに注意してください。