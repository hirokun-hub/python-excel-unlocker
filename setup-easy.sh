#!/bin/bash

# Excel Unlocker かんたんセットアップ（初心者向け）
# 小学生でもわかる！安心・安全・自動セットアップ

set -e

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

clear

echo -e "${CYAN}"
cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                🎉 Excel Unlocker かんたんセットアップ 🎉                     ║
║                                                                              ║
║                   たった1つのコマンドで全て完了！                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo

echo -e "${GREEN}👶 初心者の方へ：安心してください！${NC}"
echo
echo "  ✅ このコマンド1つで全て完了します"
echo "  ✅ 何も壊れません・安全です"
echo "  ✅ 小学生でも使えるように作りました"
echo "  ✅ 分からなくても大丈夫です"
echo

echo -e "${BLUE}🎯 このツールで何ができるの？${NC}"
echo "  📱 スマホ・タブレット・パソコンでExcelのパスワードを解除"
echo "  🚀 複数のファイルを一度に処理"
echo "  ☁️  Google Driveに直接保存"
echo "  🔒 安全・安心のセキュリティ"
echo

echo -e "${PURPLE}⏱️  どのくらい時間がかかるの？${NC}"
echo "  🏃‍♂️ 全体：約15-20分"
echo "  📝 あなたがやること：最初の設定のみ（5-10分）"
echo "  🤖 自動でやること：あとは全部おまかせ（10-15分）"
echo "  ☕ 待ち時間：コーヒーを飲んでお待ちください"
echo

echo -e "${YELLOW}🔧 最初に少しだけ手作業が必要です${NC}"
echo "  🔑 Google設定（5分）：ログイン機能の設定"
echo "  ☁️  AWS設定（3分）：ファイル保存場所の設定"
echo "  🚀 Vercel設定（2分）：ウェブ公開の設定"
echo "  💡 詳しい手順は画面に表示されます"
echo

echo -e "${GREEN}🛡️  安心・安全について${NC}"
echo "  ✅ 何も壊れません・削除されません"
echo "  ✅ いつでも元に戻すことができます"
echo "  ✅ あなたのファイルは安全に保護されます"
echo "  ✅ 全て無料で利用できます"
echo

echo -e "${WHITE}🚀 準備はいいですか？${NC}"
echo
echo "このスクリプトを実行すると："
echo "  1️⃣  必要なソフトウェアをチェック"
echo "  2️⃣  簡単な質問に答える（3つだけ）"
echo "  3️⃣  設定ファイルを作成"
echo "  4️⃣  自動でExcelツールをセットアップ"
echo "  5️⃣  動作確認テスト"
echo "  6️⃣  完了！"
echo

# 確認質問（初心者向け）
while true; do
    echo -n "セットアップを開始しますか？ はい/いいえ (はい): "
    read -r response
    
    if [[ -z "$response" ]]; then
        response="はい"
    fi
    
    case "$response" in
        [Yy]|[Yy][Ee][Ss]|はい|ハイ|yes|YES)
            echo
            echo -e "${GREEN}🎉 セットアップを開始します！${NC}"
            break
            ;;
        [Nn]|[Nn][Oo]|いいえ|イイエ|no|NO)
            echo
            echo -e "${BLUE}📋 セットアップをキャンセルしました${NC}"
            echo
            echo "次にすること："
            echo "  📚 詳しい説明を読む: docs/beginner-complete-setup-guide.md"
            echo "  ❓ 質問がある場合: docs/beginner-faq.md"
            echo "  🔄 準備ができたら: もう一度このスクリプトを実行"
            echo
            echo -e "${GREEN}準備ができたらいつでもお待ちしています！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}「はい」または「いいえ」で答えてください（英語のy/nでもOKです）${NC}"
            ;;
    esac
done

echo
echo -e "${CYAN}🚀 かんたんセットアップを起動しています...${NC}"
echo
echo -e "${YELLOW}💡 これから画面に表示される指示に従ってください${NC}"
echo -e "${YELLOW}💡 分からないことがあっても大丈夫です${NC}"
echo -e "${YELLOW}💡 エラーが出ても解決方法を教えてくれます${NC}"
echo

# 統合セットアップスクリプトの実行
exec ./scripts/setup-integrated-deployment.sh "$@"