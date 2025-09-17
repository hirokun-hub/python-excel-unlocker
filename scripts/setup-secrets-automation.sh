#!/bin/bash

# GitHub Secrets と AWS/Vercel 設定の半自動化スクリプト
# 手作業が必要な部分を明確に分離し、自動化可能な部分を最大化

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_manual() {
    echo -e "${PURPLE}[手作業必要]${NC} $1"
}

# 設定ファイル
CONFIG_FILE=".deployment-config.json"

log_info "🚀 Excel Unlocker デプロイメント設定の半自動化を開始します"

# 1. 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    local missing_tools=()
    
    # 必要なツールの確認
    if ! command -v aws &> /dev/null; then
        missing_tools+=("AWS CLI")
    fi
    
    if ! command -v gh &> /dev/null; then
        missing_tools+=("GitHub CLI")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if ! command -v openssl &> /dev/null; then
        missing_tools+=("openssl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "以下のツールがインストールされていません:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        echo
        log_info "インストール方法:"
        echo "  - AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        echo "  - GitHub CLI: brew install gh (macOS) または https://cli.github.com/"
        echo "  - jq: brew install jq (macOS)"
        echo "  - openssl: 通常はプリインストール済み"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# 2. 設定ファイルの初期化
init_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_info "設定ファイルを初期化中..."
        cat > "$CONFIG_FILE" << 'EOF'
{
  "project_name": "excel-unlocker",
  "aws_region": "ap-northeast-1",
  "environments": {
    "development": {
      "stack_name": "excel-unlocker-api-dev",
      "allowed_users": "hironomac2025@gmail.com"
    },
    "staging": {
      "stack_name": "excel-unlocker-api-staging", 
      "allowed_users": "hironomac2025@gmail.com,staging-user@example.com"
    },
    "production": {
      "stack_name": "excel-unlocker-api-prod",
      "allowed_users": "hironomac2025@gmail.com,user2@nsc.co.jp,user3@nsc.co.jp"
    }
  },
  "secrets": {
    "generated": {},
    "manual": {}
  }
}
EOF
        log_success "設定ファイルを作成しました: $CONFIG_FILE"
    else
        log_info "既存の設定ファイルを使用します: $CONFIG_FILE"
    fi
}

# 3. 自動生成可能なシークレットの作成
generate_secrets() {
    log_info "自動生成可能なシークレットを作成中..."
    
    # NEXTAUTH_SECRET の生成
    NEXTAUTH_SECRET=$(openssl rand -base64 32)
    jq --arg secret "$NEXTAUTH_SECRET" '.secrets.generated.NEXTAUTH_SECRET = $secret' "$CONFIG_FILE" > tmp.$$.json && mv tmp.$$.json "$CONFIG_FILE"
    
    log_success "NEXTAUTH_SECRET を生成しました"
    
    # AWS アカウントID取得
    if aws sts get-caller-identity &> /dev/null; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        AWS_REGION=$(aws configure get region || echo "ap-northeast-1")
        
        jq --arg account "$AWS_ACCOUNT_ID" --arg region "$AWS_REGION" \
           '.aws.account_id = $account | .aws.region = $region' "$CONFIG_FILE" > tmp.$$.json && mv tmp.$$.json "$CONFIG_FILE"
        
        log_success "AWS情報を取得しました (Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION)"
    else
        log_warning "AWS認証が設定されていません。後で手動設定が必要です。"
    fi
}

# 4. 手作業が必要な項目のガイド表示
show_manual_steps() {
    log_manual "以下の項目は手作業での設定が必要です:"
    echo
    
    echo "📋 Google OAuth設定 (Google Cloud Console)"
    echo "   1. https://console.cloud.google.com/ にアクセス"
    echo "   2. プロジェクト選択 → APIとサービス → OAuth同意画面"
    echo "   3. 認証情報 → OAuth クライアントID作成"
    echo "   4. 承認済みのリダイレクトURI:"
    echo "      - https://your-domain.com/api/auth/callback/google"
    echo "      - https://*.vercel.app/api/auth/callback/google"
    echo "   5. 承認済みのJavaScript生成元:"
    echo "      - https://your-domain.com"
    echo "      - https://*.vercel.app"
    echo
    
    echo "📋 Vercel設定 (vercel.com)"
    echo "   1. https://vercel.com/dashboard にアクセス"
    echo "   2. プロジェクト → Settings → Git → Disconnect (自動デプロイ停止)"
    echo "   3. https://vercel.com/account/tokens でトークン作成"
    echo "   4. プロジェクト → Settings → General で ID確認"
    echo
    
    echo "📋 AWS IAM設定 (AWS Console)"
    echo "   1. https://console.aws.amazon.com/iam/ にアクセス"
    echo "   2. ユーザー → ユーザーを追加 → github-deploy-bot"
    echo "   3. プログラムによるアクセス有効化"
    echo "   4. 最小権限ポリシーをアタッチ (後述)"
    echo
    
    read -p "上記の手作業を完了したら Enter を押してください..."
}

# 5. 対話式設定収集
collect_manual_config() {
    log_info "手作業で取得した設定値を入力してください:"
    echo
    
    # Google OAuth
    read -p "Google Client ID: " GOOGLE_CLIENT_ID
    read -p "Google Client Secret: " GOOGLE_CLIENT_SECRET
    
    # Vercel
    read -p "Vercel Token: " VERCEL_TOKEN
    read -p "Vercel Org ID: " VERCEL_ORG_ID
    read -p "Vercel Project ID: " VERCEL_PROJECT_ID
    
    # AWS
    read -p "AWS Access Key ID: " AWS_ACCESS_KEY_ID
    read -p "AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
    
    # 設定ファイルに保存
    jq --arg gci "$GOOGLE_CLIENT_ID" \
       --arg gcs "$GOOGLE_CLIENT_SECRET" \
       --arg vt "$VERCEL_TOKEN" \
       --arg vo "$VERCEL_ORG_ID" \
       --arg vp "$VERCEL_PROJECT_ID" \
       --arg aki "$AWS_ACCESS_KEY_ID" \
       --arg ask "$AWS_SECRET_ACCESS_KEY" \
       '.secrets.manual.GOOGLE_CLIENT_ID = $gci |
        .secrets.manual.GOOGLE_CLIENT_SECRET = $gcs |
        .secrets.manual.VERCEL_TOKEN = $vt |
        .secrets.manual.VERCEL_ORG_ID = $vo |
        .secrets.manual.VERCEL_PROJECT_ID = $vp |
        .secrets.manual.AWS_ACCESS_KEY_ID = $aki |
        .secrets.manual.AWS_SECRET_ACCESS_KEY = $ask' "$CONFIG_FILE" > tmp.$$.json && mv tmp.$$.json "$CONFIG_FILE"
    
    log_success "設定値を保存しました"
}

# 6. GitHub Secrets の自動設定
setup_github_secrets() {
    log_info "GitHub Secrets を自動設定中..."
    
    # GitHub CLI認証確認
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLIの認証が必要です"
        log_info "以下のコマンドを実行してください: gh auth login"
        exit 1
    fi
    
    # 設定値を読み込み
    NEXTAUTH_SECRET=$(jq -r '.secrets.generated.NEXTAUTH_SECRET' "$CONFIG_FILE")
    GOOGLE_CLIENT_ID=$(jq -r '.secrets.manual.GOOGLE_CLIENT_ID' "$CONFIG_FILE")
    GOOGLE_CLIENT_SECRET=$(jq -r '.secrets.manual.GOOGLE_CLIENT_SECRET' "$CONFIG_FILE")
    VERCEL_TOKEN=$(jq -r '.secrets.manual.VERCEL_TOKEN' "$CONFIG_FILE")
    VERCEL_ORG_ID=$(jq -r '.secrets.manual.VERCEL_ORG_ID' "$CONFIG_FILE")
    VERCEL_PROJECT_ID=$(jq -r '.secrets.manual.VERCEL_PROJECT_ID' "$CONFIG_FILE")
    AWS_ACCESS_KEY_ID=$(jq -r '.secrets.manual.AWS_ACCESS_KEY_ID' "$CONFIG_FILE")
    AWS_SECRET_ACCESS_KEY=$(jq -r '.secrets.manual.AWS_SECRET_ACCESS_KEY' "$CONFIG_FILE")
    
    # GitHub Secrets設定
    local secrets=(
        "AWS_ACCESS_KEY_ID:$AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY:$AWS_SECRET_ACCESS_KEY"
        "VERCEL_TOKEN:$VERCEL_TOKEN"
        "VERCEL_ORG_ID:$VERCEL_ORG_ID"
        "VERCEL_PROJECT_ID:$VERCEL_PROJECT_ID"
        "GOOGLE_CLIENT_ID:$GOOGLE_CLIENT_ID"
        "GOOGLE_CLIENT_SECRET:$GOOGLE_CLIENT_SECRET"
        "NEXTAUTH_SECRET:$NEXTAUTH_SECRET"
    )
    
    for secret in "${secrets[@]}"; do
        IFS=':' read -r key value <<< "$secret"
        if [[ -n "$value" && "$value" != "null" ]]; then
            echo "$value" | gh secret set "$key"
            log_success "GitHub Secret設定完了: $key"
        else
            log_warning "スキップ: $key (値が空)"
        fi
    done
}

# 7. AWS IAMポリシーの生成
generate_iam_policy() {
    log_info "AWS IAM最小権限ポリシーを生成中..."
    
    AWS_ACCOUNT_ID=$(jq -r '.aws.account_id' "$CONFIG_FILE")
    AWS_REGION=$(jq -r '.aws.region' "$CONFIG_FILE")
    
    cat > "aws-iam-policy.json" << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:Describe*",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:GetTemplate"
      ],
      "Resource": [
        "arn:aws:cloudformation:${AWS_REGION}:${AWS_ACCOUNT_ID}:stack/excel-unlocker-api-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:PutBucketPolicy",
        "s3:PutBucketCORS",
        "s3:PutBucketEncryption",
        "s3:PutBucketVersioning",
        "s3:PutLifecycleConfiguration"
      ],
      "Resource": [
        "arn:aws:s3:::excel-unlocker-bucket-*",
        "arn:aws:s3:::excel-unlocker-bucket-*/*",
        "arn:aws:s3:::aws-sam-cli-managed-default-samclisourcebucket-*",
        "arn:aws:s3:::aws-sam-cli-managed-default-samclisourcebucket-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Resource": [
        "arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:excel-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:*"
      ],
      "Resource": [
        "arn:aws:apigateway:${AWS_REGION}::/restapis/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy"
      ],
      "Resource": [
        "arn:aws:iam::${AWS_ACCOUNT_ID}:role/excel-unlocker-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DeleteAlarms",
        "cloudwatch:PutDashboard",
        "cloudwatch:DeleteDashboards"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:DeleteTopic",
        "sns:Subscribe",
        "sns:Unsubscribe",
        "sns:SetTopicAttributes"
      ],
      "Resource": [
        "arn:aws:sns:${AWS_REGION}:${AWS_ACCOUNT_ID}:ExcelUnlocker-*"
      ]
    }
  ]
}
EOF
    
    log_success "IAMポリシーを生成しました: aws-iam-policy.json"
    log_manual "このポリシーをAWS IAMユーザー 'github-deploy-bot' にアタッチしてください"
}

# 8. 設定確認とテスト
verify_setup() {
    log_info "設定確認とテストを実行中..."
    
    # GitHub Secrets確認
    log_info "GitHub Secrets確認中..."
    if gh secret list | grep -q "AWS_ACCESS_KEY_ID"; then
        log_success "GitHub Secrets設定確認完了"
    else
        log_error "GitHub Secrets設定に問題があります"
        return 1
    fi
    
    # AWS認証確認
    log_info "AWS認証確認中..."
    if aws sts get-caller-identity &> /dev/null; then
        log_success "AWS認証確認完了"
    else
        log_error "AWS認証に問題があります"
        return 1
    fi
    
    log_success "全ての設定確認が完了しました！"
}

# 9. 次のステップ案内
show_next_steps() {
    log_success "🎉 デプロイメント設定の半自動化が完了しました！"
    echo
    log_info "次のステップ:"
    echo "1. 初回デプロイ実行:"
    echo "   ./scripts/setup-deployment.sh"
    echo
    echo "2. GitHub Actions確認:"
    echo "   - リポジトリ → Actions → Deploy Full Stack"
    echo "   - 手動実行でテストデプロイ"
    echo
    echo "3. Vercel環境変数設定:"
    echo "   - vercel.com → プロジェクト → Settings → Environment Variables"
    echo "   - Production/Preview環境の設定"
    echo
    echo "4. 本番デプロイ:"
    echo "   ./scripts/deploy.sh production all"
    echo
    log_info "詳細は docs/deployment-guide.md を参照してください"
}

# メイン実行
main() {
    check_prerequisites
    init_config
    generate_secrets
    show_manual_steps
    collect_manual_config
    setup_github_secrets
    generate_iam_policy
    verify_setup
    show_next_steps
}

# スクリプト実行
main "$@"