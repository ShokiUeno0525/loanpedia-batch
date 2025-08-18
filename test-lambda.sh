#!/bin/bash

# Lambda関数のローカルテスト用スクリプト

set -e

echo "🧪 Lambda関数のローカルテストを開始します"

# カラーコード定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 設定
STACK_NAME="loanpedia-batch"

# テストイベントファイルの存在確認
if [ ! -f "events/aoimori_shinkin_test.json" ]; then
    echo -e "${YELLOW}⚠️  テストイベントファイルが見つかりません。デフォルトイベントを作成します${NC}"
    mkdir -p events
    cat > events/test_all.json << 'EOF'
{
  "source": "aws.events",
  "detail-type": "Scheduled Event",
  "detail": {}
}
EOF
    
    cat > events/test_single.json << 'EOF'
{
  "institution": "aoimori_shinkin",
  "source": "manual",
  "detail-type": "Manual Test"
}
EOF
fi

# 依存関係のコピー
echo "📦 依存関係のコピー中..."
if [ -d "scrapers" ]; then
    cp -r scrapers loanpedia_scraper/ 2>/dev/null || true
fi

if [ -d "database" ]; then
    cp -r database loanpedia_scraper/ 2>/dev/null || true
fi

# SAM build
echo "🔨 SAM ローカルビルド中..."
sam build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SAM ビルドに失敗しました${NC}"
    exit 1
fi

# テスト選択
echo ""
echo "テストする関数を選択してください:"
echo "1) 全スクレイパー統合実行 (LoanpediaScraperFunction)"
echo "2) 青い森信用金庫 (AoimoriShinkinScraperFunction)"
echo "3) 青森みちのく銀行 (AomorimichinokuBankScraperFunction)"
echo "4) 東奥信用金庫 (TououshinkinScraperFunction)"
echo "5) 青森県信用組合 (AomorikenshinyoukumiaiScraperFunction)"
echo ""
read -p "選択してください (1-5): " choice

case $choice in
    1)
        FUNCTION_NAME="LoanpediaScraperFunction"
        EVENT_FILE="events/test_all.json"
        ;;
    2)
        FUNCTION_NAME="AoimoriShinkinScraperFunction"
        EVENT_FILE="events/aoimori_shinkin_test.json"
        if [ ! -f "$EVENT_FILE" ]; then
            EVENT_FILE="events/test_single.json"
        fi
        ;;
    3)
        FUNCTION_NAME="AomorimichinokuBankScraperFunction"
        EVENT_FILE="events/test_single.json"
        ;;
    4)
        FUNCTION_NAME="TououshinkinScraperFunction"
        EVENT_FILE="events/test_single.json"
        ;;
    5)
        FUNCTION_NAME="AomorikenshinyoukumiaiScraperFunction"
        EVENT_FILE="events/test_single.json"
        ;;
    *)
        echo -e "${RED}❌ 無効な選択です${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}🚀 ${FUNCTION_NAME} をテスト実行します...${NC}"
echo ""

# SAM local invoke
sam local invoke "$FUNCTION_NAME" --event "$EVENT_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ テスト実行完了！${NC}"
else
    echo ""
    echo -e "${RED}❌ テスト実行に失敗しました${NC}"
    exit 1
fi

echo ""
echo "💡 ヒント:"
echo "  - ログを確認してエラーがないかチェックしてください"
echo "  - 実際のWebサイトにアクセスするため、ネットワーク接続が必要です"
echo "  - 金融機関のサイト構造が変更された場合、スクレイパーの更新が必要です"