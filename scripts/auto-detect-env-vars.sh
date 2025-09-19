#!/bin/bash

# 環境変数自動検出・設定スクリプト
# デプロイ後に動的に生成される値を自動検出して設定

set -e

echo "🔍 環境変数の自動検出を開始します..."

# 設定ファイル
CONFIG_FILE=".deployment-config.json"
BACKEND_ENV="backend/.env.local"
FRONTEND_ENV="frontend/.env.local"

# 1. AWS設定確認
echo "☁️  AWS設定を確認中..."

# AWSアカウントID取得
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ AWS認証が設定されていません"
    echo "💡 aws configure を実行してください"
    exit 1
fi

echo "✅ AWSアカウントID: $AWS_ACCOUNT_ID"

# AWSリージョン取得
AWS_REGION=$(aws configure get region 2>/dev/null || echo "ap-northeast-1")
echo "✅ AWSリージョン: $AWS_REGION"

# 2. S3バケット名の自動検出
echo "🪣 S3バケット名を検出中..."

# 既存のS3バケット検索
BUCKET_NAME=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'excel-unlocker')].Name" --output text 2>/dev/null | head -n1 || echo "")

if [ -z "$BUCKET_NAME" ]; then
    # バケット名生成
    BUCKET_NAME="excel-unlocker-bucket-development-${AWS_ACCOUNT_ID}-${AWS_REGION}"
    echo "📝 生成されるバケット名: $BUCKET_NAME"
else
    echo "✅ 既存バケット検出: $BUCKET_NAME"
fi

# 3. CloudFormationスタック情報の取得
echo "📚 CloudFormationスタック情報を取得中..."

STACK_NAME="excel-unlocker-api"
API_GATEWAY_URL=""

# スタック存在確認
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" >/dev/null 2>&1; then
    echo "✅ スタック検出: $STACK_NAME"
    
    # API Gateway URL取得
    API_GATEWAY_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$API_GATEWAY_URL" ]; then
        echo "✅ API Gateway URL: $API_GATEWAY_URL"
    else
        echo "⚠️  API Gateway URLが見つかりません（デプロイ後に再実行してください）"
    fi
else
    echo "⚠️  CloudFormationスタックが見つかりません（デプロイ後に再実行してください）"
fi

# 4. 環境変数ファイルの更新
echo "📝 環境変数ファイルを更新中..."

# バックエンド環境変数更新
if [ ! -f "$BACKEND_ENV" ]; then
    cp "backend/.env.example" "$BACKEND_ENV"
fi

# S3バケット名設定
sed -i.bak "s/S3_BUCKET_NAME=.*/S3_BUCKET_NAME=$BUCKET_NAME/" "$BACKEND_ENV"
sed -i.bak "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" "$BACKEND_ENV"

echo "✅ バックエンド環境変数を更新: $BACKEND_ENV"

# フロントエンド環境変数更新
if [ ! -f "$FRONTEND_ENV" ]; then
    cp "frontend/.env.example" "$FRONTEND_ENV"
fi

# API Gateway URL設定（存在する場合のみ）
if [ -n "$API_GATEWAY_URL" ]; then
    sed -i.bak "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$API_GATEWAY_URL|" "$FRONTEND_ENV"
    echo "✅ API Gateway URL を設定: $API_GATEWAY_URL"
fi

echo "✅ フロントエンド環境変数を更新: $FRONTEND_ENV"

# 5. 設定情報の保存
if [ ! -f "$CONFIG_FILE" ]; then
    echo '{}' > "$CONFIG_FILE"
fi

jq --arg aws_account_id "$AWS_ACCOUNT_ID" \
   --arg aws_region "$AWS_REGION" \
   --arg bucket_name "$BUCKET_NAME" \
   --arg api_gateway_url "$API_GATEWAY_URL" \
   '.aws.account_id = $aws_account_id | 
    .aws.region = $aws_region | 
    .aws.s3_bucket_name = $bucket_name | 
    .aws.api_gateway_url = $api_gateway_url' \
   "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"

# 6. 結果表示
echo ""
echo "🎉 環境変数自動検出完了！"
echo "=================================="
echo "🆔 AWSアカウントID: $AWS_ACCOUNT_ID"
echo "🌏 AWSリージョン: $AWS_REGION"
echo "🪣 S3バケット名: $BUCKET_NAME"
if [ -n "$API_GATEWAY_URL" ]; then
    echo "🌐 API Gateway URL: $API_GATEWAY_URL"
else
    echo "⚠️  API Gateway URL: 未設定（デプロイ後に再実行）"
fi
echo ""

# 7. 次のステップ案内
echo "⏭️  次のステップ:"
if [ -z "$API_GATEWAY_URL" ]; then
    echo "1. sam deploy を実行してバックエンドをデプロイ"
    echo "2. このスクリプトを再実行してAPI Gateway URLを取得"
    echo "3. フロントエンドをデプロイ"
else
    echo "1. フロントエンドをデプロイ"
    echo "2. 動作確認を実行"
fi
echo ""

# 8. 不足している環境変数の確認
echo "🔍 不足している環境変数の確認..."

MISSING_VARS=()

# Google OAuth設定確認
if ! grep -q "GOOGLE_CLIENT_ID=.*apps.googleusercontent.com" "$FRONTEND_ENV"; then
    MISSING_VARS+=("GOOGLE_CLIENT_ID")
fi

if ! grep -q "GOOGLE_CLIENT_SECRET=.*" "$FRONTEND_ENV" || grep -q "GOOGLE_CLIENT_SECRET=your-google-client-secret" "$FRONTEND_ENV"; then
    MISSING_VARS+=("GOOGLE_CLIENT_SECRET")
fi

# NextAuth.js シークレット確認
if grep -q "NEXTAUTH_SECRET=your-nextauth-secret-here" "$FRONTEND_ENV"; then
    MISSING_VARS+=("NEXTAUTH_SECRET")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "⚠️  以下の環境変数が未設定です:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "💡 Google OAuth設定を完了するには:"
    echo "   ./scripts/setup-google-oauth-automation.sh"
    echo ""
else
    echo "✅ 全ての必要な環境変数が設定されています"
fi

echo "📁 設定ファイル:"
echo "   - バックエンド: $BACKEND_ENV"
echo "   - フロントエンド: $FRONTEND_ENV"
echo "   - 設定情報: $CONFIG_FILE"