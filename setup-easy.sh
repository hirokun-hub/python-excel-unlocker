#!/bin/bash

# Excel Unlocker 簡易セットアップ（初心者向け）
# 社内展開用統合セットアップスクリプトの簡易起動ラッパー

set -e

# 色付きログ出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔰 Excel Unlocker 簡易セットアップ 🔰              ║
║                                                              ║
║              初心者向け・ワンクリック環境構築                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo

echo -e "${BLUE}📋 このスクリプトについて:${NC}"
echo "  - 技術的な知識がなくても Excel Unlocker を簡単にセットアップできます"
echo "  - 対話式で必要な設定を案内します"
echo "  - エラーが発生した場合は詳細な解決方法を表示します"
echo

echo -e "${GREEN}🚀 セットアップを開始しますか？${NC}"
echo "  所要時間: 約15-30分（手作業含む）"
echo

read -p "続行しますか？ (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "セットアップをキャンセルしました。"
    exit 0
fi

echo
echo -e "${CYAN}統合セットアップスクリプトを起動しています...${NC}"
echo

# 統合セットアップスクリプトの実行
exec ./scripts/setup-integrated-deployment.sh "$@"