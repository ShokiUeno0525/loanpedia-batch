#!/bin/bash
# /deploy.sh
# AWS SAMでLambda群をビルド/デプロイする
# なぜ: 一貫した確認付きデプロイを行うため
# 関連: template.yaml, docker-compose.yml, setup_instructions.md, test-lambda.sh

# AWS Lambda デプロイメントスクリプト
# ローン情報スクレイピングバッチシステム

set -e

echo "🚀 ローン情報スクレイピングシステムのデプロイを開始します"

# カラーコード定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 設定
AWS_REGION="ap-northeast-1"
STACK_NAME="loanpedia-batch"

# 必要なコマンドの確認
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 コマンドが見つかりません。インストールしてください。${NC}"
        exit 1
    fi
}

echo "📋 必要なツールの確認中..."
check_command sam
check_command aws

# AWS認証確認
echo "🔐 AWS認証の確認中..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS認証が設定されていません。aws configure を実行してください。${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS認証確認完了${NC}"

# Lambda用ディレクトリにscrapersとdatabaseをコピー
echo "📦 依存関係のコピー中..."
# 注意: scrapers と database は backend/batch/loanpedia_scraper/ と backend/batch/database/ にあります
# 既にディレクトリ構造内に含まれているため、コピー不要
echo -e "${GREEN}✅ 依存関係は既にディレクトリ構造内に含まれています${NC}"

# SAM build
echo "🔨 SAM ビルド中..."
sam build --use-container

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SAM ビルドに失敗しました${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SAM ビルド完了${NC}"

# デプロイ確認
echo -e "${YELLOW}⚠️  デプロイを実行しますか？ (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "デプロイをキャンセルしました"
    exit 0
fi

# SAM deploy
echo "🚀 SAM デプロイ中..."
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        ParameterKey=Environment,ParameterValue=production \
    --confirm-changeset \
    --resolve-s3

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SAM デプロイに失敗しました${NC}"
    exit 1
fi

echo -e "${GREEN}✅ デプロイ完了！${NC}"

# スタック情報の表示
echo "📊 デプロイされたリソース:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo -e "${GREEN}🎉 デプロイが正常に完了しました！${NC}"
echo ""
echo "📅 スケジュール設定:"
echo "  - 全スクレイパー: 30日ごとに自動実行"
echo "  - 各金融機関別スクレイパー: 30日ごとに自動実行"
echo ""
echo "🔧 手動実行:"
echo "  aws lambda invoke --function-name ${STACK_NAME}-LoanpediaScraperFunction-* response.json"
echo ""
echo "📈 ログ確認:"
echo "  aws logs tail /aws/lambda/${STACK_NAME}-LoanpediaScraperFunction-* --follow"
