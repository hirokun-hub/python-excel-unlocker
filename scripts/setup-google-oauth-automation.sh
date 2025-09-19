#!/bin/bash

# Google OAuth自動設定スクリプト
# 使用方法: ./scripts/setup-google-oauth-automation.sh

set -e

echo "🔐 Google OAuth自動設定を開始します..."

# 設定ファイル
CONFIG_FILE=".deployment-config.json"

# プロジェクト名の取得
if [ -f "$CONFIG_FILE" ]; then
    PROJECT_NAME=$(jq -r '.project.name // "excel-unlocker"' "$CONFIG_FILE")
else
    PROJECT_NAME="excel-unlocker"
fi

echo "📋 Google OAuth設定手順（自動化可能な部分）"
echo "=================================="

# 1. gcloud CLI確認
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI がインストールされていません"
    echo "📥 インストール手順:"
    echo "   macOS: brew install google-cloud-sdk"
    echo "   その他: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI が利用可能です"

# 2. ログイン確認
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo "🔑 Google Cloud にログインしてください:"
    gcloud auth login
fi

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
echo "✅ ログイン済み: $ACCOUNT"

# 3. プロジェクト設定
echo "🏗️  Google Cloud プロジェクトの設定..."

# 既存プロジェクト確認
EXISTING_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$EXISTING_PROJECT" ]; then
    echo "📝 新しいプロジェクトを作成します"
    
    # プロジェクトID生成（ユニークにするため）
    TIMESTAMP=$(date +%s)
    PROJECT_ID="${PROJECT_NAME}-${TIMESTAMP}"
    
    echo "🆔 プロジェクトID: $PROJECT_ID"
    
    # プロジェクト作成
    gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"
    gcloud config set project "$PROJECT_ID"
    
    echo "✅ プロジェクト作成完了: $PROJECT_ID"
else
    PROJECT_ID="$EXISTING_PROJECT"
    echo "✅ 既存プロジェクトを使用: $PROJECT_ID"
fi

# 4. 必要なAPIの有効化
echo "🔌 必要なAPIを有効化中..."
gcloud services enable iamcredentials.googleapis.com

# 5. OAuth同意画面の設定（手動部分の案内）
echo ""
echo "⚠️  以下は手動設定が必要です:"
echo "=================================="
echo "1. Google Cloud Console にアクセス:"
echo "   https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT_ID"
echo ""
echo "2. OAuth同意画面を設定:"
echo "   - User Type: External を選択"
echo "   - アプリ名: $PROJECT_NAME"
echo "   - ユーザーサポートメール: $ACCOUNT"
echo "   - 承認済みドメイン: localhost (開発用)"
echo ""
echo "3. スコープ設定:"
echo "   - ../auth/userinfo.email"
echo "   - ../auth/userinfo.profile"
echo "   - openid"
echo ""

# 6. OAuth認証情報作成の準備
echo "4. OAuth 2.0 クライアントID作成:"
echo "   https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo ""
echo "   - アプリケーションの種類: ウェブアプリケーション"
echo "   - 名前: $PROJECT_NAME Web Client"
echo "   - 承認済みのリダイレクトURI:"
echo "     - http://localhost:3000/api/auth/callback/google (開発用)"
echo "     - https://your-domain.com/api/auth/callback/google (本番用)"
echo ""

# 7. 設定完了後の手順
echo "5. 設定完了後、以下の値を取得してください:"
echo "   - クライアントID (GOOGLE_CLIENT_ID)"
echo "   - クライアントシークレット (GOOGLE_CLIENT_SECRET)"
echo ""

# 8. 自動設定可能な部分
echo "🤖 自動設定可能な部分を実行中..."

# NextAuth.js シークレット生成
NEXTAUTH_SECRET=$(openssl rand -base64 32)
echo "✅ NEXTAUTH_SECRET を生成しました"

# 環境変数テンプレート更新
ENV_FILE="frontend/.env.local"
if [ ! -f "$ENV_FILE" ]; then
    cp "frontend/.env.example" "$ENV_FILE"
fi

# NextAuth.js シークレット設定
sed -i.bak "s/NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=$NEXTAUTH_SECRET/" "$ENV_FILE"
echo "✅ $ENV_FILE を更新しました"

# 設定情報を保存
if [ ! -f "$CONFIG_FILE" ]; then
    echo '{}' > "$CONFIG_FILE"
fi

# jqで設定を更新
jq --arg project_id "$PROJECT_ID" \
   --arg nextauth_secret "$NEXTAUTH_SECRET" \
   '.google.project_id = $project_id | .google.nextauth_secret = $nextauth_secret' \
   "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"

echo ""
echo "🎉 自動設定完了！"
echo "=================================="
echo "📁 設定ファイル: $ENV_FILE"
echo "📋 プロジェクトID: $PROJECT_ID"
echo "🔑 NextAuth.js シークレット: 設定済み"
echo ""
echo "⏭️  次のステップ:"
echo "1. 上記の手動設定を完了してください"
echo "2. GOOGLE_CLIENT_ID と GOOGLE_CLIENT_SECRET を $ENV_FILE に設定"
echo "3. ./scripts/setup-complete-automation.sh を実行"
echo ""