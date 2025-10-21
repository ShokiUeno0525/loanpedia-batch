#!/bin/bash
# 全体デプロイスクリプト
# CDK（Aurora） → SAM（Lambda）の順にデプロイ

set -e  # エラー時に停止

echo "========================================="
echo "Loanpedia 全体デプロイ"
echo "========================================="

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. CDKでAuroraデプロイ
echo -e "\n${YELLOW}[1/3] CDKでAurora Serverless v2をデプロイ中...${NC}"
cd cdk

# 依存関係チェック
if [ ! -d "node_modules" ]; then
    echo "npm依存関係をインストール中..."
    npm install
fi

# CDKデプロイ
echo "CDKデプロイ実行中（15-20分かかる場合があります）..."
npx cdk deploy --require-approval never

# Outputsを取得
echo -e "\n${GREEN}CDKデプロイ完了！${NC}"
echo "CloudFormation Outputsを確認中..."
aws cloudformation describe-stacks \
    --stack-name LoanpediaAuroraStack \
    --query 'Stacks[0].Outputs' \
    --output table

cd ..

# 2. データベース初期化（テーブル作成）
echo -e "\n${YELLOW}[2/3] データベース初期化中...${NC}"
echo "注意: テーブル作成スクリプトは手動で実行してください"
echo "  scripts/init_database.py を実行"

# 3. SAMでLambdaデプロイ
echo -e "\n${YELLOW}[3/3] SAMでLambda関数をデプロイ中...${NC}"

# SAMビルド
echo "SAMビルド実行中..."
sam build

# SAMデプロイ
echo "SAMデプロイ実行中..."
sam deploy --no-confirm-changeset

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}✓ 全体デプロイ完了！${NC}"
echo -e "${GREEN}=========================================${NC}"

# デプロイ後の確認事項
echo -e "\n次のステップ:"
echo "1. データベーステーブルの作成:"
echo "   python scripts/init_database.py"
echo ""
echo "2. Lambda関数のテスト:"
echo "   sam logs -n AomorimichinokuBankScraperFunction --tail"
echo ""
echo "3. 手動実行:"
echo "   aws lambda invoke --function-name <function-name> --payload '{}' response.json"
