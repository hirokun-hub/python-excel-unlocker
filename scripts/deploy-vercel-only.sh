#!/bin/bash

# Vercel単体デプロイスクリプト
# AWS設定は一切触らず、Vercelのみに集中

set -e

echo "🚀 Vercel単体デプロイを開始します..."
echo "=================================="

# 色付きログ
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. 前提条件確認
log_info "前提条件を確認中..."

# Vercel CLI確認
if ! command -v vercel &> /dev/null; then
    log_error "Vercel CLI がインストールされていません"
    echo "インストール方法:"
    echo "  npm install -g vercel"
    exit 1
fi

# ログイン確認
if ! vercel whoami &> /dev/null; then
    log_info "Vercelにログインしてください:"
    vercel login
fi

VERCEL_USER=$(vercel whoami)
log_success "Vercelログイン済み: $VERCEL_USER"

# 2. 環境変数確認
log_info "環境変数を確認中..."

FRONTEND_ENV="frontend/.env.local"
if [ ! -f "$FRONTEND_ENV" ]; then
    log_error "フロントエンド環境変数ファイルが見つかりません: $FRONTEND_ENV"
    exit 1
fi

# 必要な環境変数をチェック
REQUIRED_VARS=("NEXTAUTH_SECRET" "GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_SECRET")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "$FRONTEND_ENV" || grep -q "^${var}=your-" "$FRONTEND_ENV"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log_error "以下の環境変数が未設定です:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "設定方法:"
    echo "  1. $FRONTEND_ENV を編集"
    echo "  2. Google OAuth設定を完了"
    exit 1
fi

log_success "必要な環境変数が設定されています"

# 3. フロントエンドディレクトリに移動
cd frontend

# 4. ビルドテスト
log_info "ビルドテストを実行中..."
if npm run build; then
    log_success "ビルド成功"
else
    log_error "ビルドに失敗しました"
    exit 1
fi

# 5. Vercelプロジェクト設定
log_info "Vercelプロジェクト設定を確認中..."

if [ ! -f ".vercel/project.json" ]; then
    log_info "Vercelプロジェクトを初期化します..."
    vercel --confirm
else
    log_success "Vercelプロジェクト設定済み"
fi

# 6. 環境変数をVercelに設定
log_info "Vercel環境変数を設定中..."

# .env.localから環境変数を読み取り
while IFS='=' read -r key value; do
    # コメント行と空行をスキップ
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # 値のクォートを除去
    value=$(echo "$value" | sed 's/^["'\'']//' | sed 's/["'\'']$//')
    
    # Vercelに設定（production環境）
    if [[ -n $value && $value != "your-"* ]]; then
        echo "Setting $key..."
        vercel env add "$key" production <<< "$value" 2>/dev/null || true
        vercel env add "$key" preview <<< "$value" 2>/dev/null || true
    fi
done < "../$FRONTEND_ENV"

log_success "Vercel環境変数設定完了"

# 7. デプロイ実行
log_info "Vercelデプロイを実行中..."

# プレビューデプロイ
log_info "プレビューデプロイ実行中..."
PREVIEW_URL=$(vercel --confirm | grep -o 'https://[^[:space:]]*')

if [ -n "$PREVIEW_URL" ]; then
    log_success "プレビューデプロイ成功: $PREVIEW_URL"
    
    # 本番デプロイ確認
    echo ""
    read -p "本番環境にデプロイしますか？ (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "本番デプロイ実行中..."
        PROD_URL=$(vercel --prod --confirm | grep -o 'https://[^[:space:]]*')
        
        if [ -n "$PROD_URL" ]; then
            log_success "本番デプロイ成功: $PROD_URL"
        else
            log_warning "本番デプロイURLの取得に失敗しました"
        fi
    else
        log_info "本番デプロイをスキップしました"
    fi
else
    log_error "プレビューデプロイに失敗しました"
    exit 1
fi

# 8. 結果表示
echo ""
log_success "🎉 Vercelデプロイ完了！"
echo "=================================="
echo ""
echo "📱 デプロイされたURL:"
if [ -n "$PREVIEW_URL" ]; then
    echo "  プレビュー: $PREVIEW_URL"
fi
if [ -n "$PROD_URL" ]; then
    echo "  本番環境: $PROD_URL"
fi
echo ""
echo "🔍 次のステップ:"
echo "  1. デプロイされたURLでGoogle OAuth動作確認"
echo "  2. 問題なければAWS設定に進む"
echo "  3. AWS設定後にフロントエンド・バックエンド連携テスト"
echo ""
echo "⚙️  Vercel設定確認:"
echo "  vercel env ls"
echo "  vercel domains ls"
echo ""

# 元のディレクトリに戻る
cd ..

log_info "Vercel単体デプロイが完了しました"