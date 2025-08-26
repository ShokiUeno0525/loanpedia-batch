# -*- coding: utf-8 -*-
"""
青森みちのく銀行 改良版共通抽出ロジック

各ローン商品ページから統一的にデータを抽出するための改良版実装
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class ImprovedExtractionMethods:
    """改良版抽出メソッド集"""

    @staticmethod
    def extract_loan_table_data(soup: BeautifulSoup) -> Dict[str, Any]:
        """
        テーブル形式のローンデータを抽出
        
        Returns:
            Dict: 抽出されたローンデータ
        """
        result = {}
        
        # すべてのテーブルを検索
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    header = cells[0].get_text().strip()
                    content = cells[1].get_text().strip()
                    
                    # 融資限度額の抽出
                    if "限度額" in header or "借入限度額" in header:
                        amount_match = re.search(r"(\d+(?:,\d{3})*)\s*[〜～]\s*(\d+(?:,\d{3})*)\s*万円", content)
                        if amount_match:
                            result["min_loan_amount"] = int(amount_match.group(1).replace(",", "")) * 10000
                            result["max_loan_amount"] = int(amount_match.group(2).replace(",", "")) * 10000
                            logger.info(f"✅ テーブルから融資限度額: {result['min_loan_amount']:,}円 - {result['max_loan_amount']:,}円")
                    
                    # 金利の抽出
                    elif "利率" in header or "金利" in header:
                        # 複数の金利パターンに対応
                        rate_patterns = [
                            r"(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]",  # 範囲
                            r"年\s*(\d+\.\d+)\s*[%％]",  # 単一年率
                            r"(\d+\.\d+)\s*[%％]",  # 単一率
                        ]
                        
                        for pattern in rate_patterns:
                            rate_match = re.search(pattern, content)
                            if rate_match:
                                groups = rate_match.groups()
                                if len(groups) == 2:
                                    result["min_interest_rate"] = float(groups[0])
                                    result["max_interest_rate"] = float(groups[1])
                                    logger.info(f"✅ テーブルから金利範囲: {result['min_interest_rate']}% - {result['max_interest_rate']}%")
                                elif len(groups) == 1:
                                    rate = float(groups[0])
                                    result["min_interest_rate"] = rate
                                    result["max_interest_rate"] = rate
                                    logger.info(f"✅ テーブルから単一金利: {rate}%")
                                break
                    
                    # 融資期間の抽出
                    elif "期間" in header or "返済期間" in header:
                        period_match = re.search(r"(\d+)\s*年", content)
                        if period_match:
                            years = int(period_match.group(1))
                            result["max_loan_term_months"] = years * 12
                            result["min_loan_term_months"] = 12  # デフォルト最小1年
                            logger.info(f"✅ テーブルから融資期間: {result['max_loan_term_months']}ヶ月")
        
        return result

    @staticmethod
    def extract_detailed_rate_table(soup: BeautifulSoup) -> Optional[Tuple[float, float]]:
        """
        詳細金利テーブルから金利範囲を抽出
        (カードローンの限度額別金利テーブル用)
        """
        tables = soup.find_all('table')
        rates = []
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                for cell in cells:
                    cell_text = cell.get_text().strip()
                    # 金利の数値を検索
                    rate_match = re.search(r"(\d+\.\d+)\s*[%％]", cell_text)
                    if rate_match:
                        rate = float(rate_match.group(1))
                        # 合理的な金利範囲内かチェック (0.1% - 20%)
                        if 0.1 <= rate <= 20.0:
                            rates.append(rate)
        
        if rates:
            min_rate = min(rates)
            max_rate = max(rates)
            logger.info(f"✅ 詳細テーブルから金利範囲: {min_rate}% - {max_rate}%")
            return (min_rate, max_rate)
        
        return None

    @staticmethod
    def extract_product_overview(soup: BeautifulSoup) -> Dict[str, str]:
        """
        商品概要セクションからデータを抽出
        """
        overview_data = {}
        
        # 商品概要の見出しを検索
        overview_headers = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'商品概要|商品詳細|商品内容'))
        
        for header in overview_headers:
            # 見出し後の内容を取得
            next_elements = header.find_all_next()
            
            for elem in next_elements[:20]:  # 最大20要素まで見る
                text = elem.get_text().strip()
                
                # 金利情報
                if "金利" in text or "利率" in text:
                    rate_match = re.search(r"(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", text)
                    if rate_match:
                        overview_data["interest_rate_range"] = f"{rate_match.group(1)}%-{rate_match.group(2)}%"
                
                # 融資限度額
                if "限度額" in text:
                    amount_match = re.search(r"(\d+(?:,\d{3})*)\s*万円", text)
                    if amount_match:
                        overview_data["max_limit"] = f"{amount_match.group(1)}万円"
                
                # 次のセクションに到達したら終了
                if elem.name in ['h2', 'h3', 'h4'] and elem != header:
                    break
        
        return overview_data

    @staticmethod
    def extract_structured_content(soup: BeautifulSoup, product_type: str) -> Dict[str, Any]:
        """
        商品タイプに応じた構造化コンテンツの抽出
        
        Args:
            soup: BeautifulSoup object
            product_type: 商品タイプ ('card', 'education', 'mycar' etc.)
            
        Returns:
            Dict: 抽出されたデータ
        """
        result = {}
        
        # 1. テーブルデータを最優先で抽出
        table_data = ImprovedExtractionMethods.extract_loan_table_data(soup)
        result.update(table_data)
        
        # 2. 詳細金利テーブルで補完
        if "min_interest_rate" not in result:
            detailed_rates = ImprovedExtractionMethods.extract_detailed_rate_table(soup)
            if detailed_rates:
                result["min_interest_rate"] = detailed_rates[0]
                result["max_interest_rate"] = detailed_rates[1]
        
        # 3. 商品概要で補完
        overview_data = ImprovedExtractionMethods.extract_product_overview(soup)
        
        # 4. 製品固有の抽出ロジック
        if product_type == 'card':
            result.update(ImprovedExtractionMethods._extract_card_specific(soup))
        elif product_type == 'education':
            result.update(ImprovedExtractionMethods._extract_education_specific(soup))
        elif product_type == 'mycar':
            result.update(ImprovedExtractionMethods._extract_mycar_specific(soup))
        
        return result

    @staticmethod
    def _extract_card_specific(soup: BeautifulSoup) -> Dict[str, Any]:
        """カードローン固有の抽出"""
        result = {}
        full_text = soup.get_text()
        
        # カードローン特有のフレーズ検索
        if "3年自動更新" in full_text:
            result["loan_term_note"] = "3年自動更新"
        
        if "専用カード" in full_text:
            result["card_issuance"] = True
        
        return result

    @staticmethod
    def _extract_education_specific(soup: BeautifulSoup) -> Dict[str, Any]:
        """教育ローン固有の抽出"""
        result = {}
        full_text = soup.get_text()
        
        # 教育ローン特有の特徴
        if "在学中" in full_text and "利息のみ" in full_text:
            result["interest_only_during_study"] = True
        
        if "WEB完結" in full_text:
            # WEB完結の限度額制限をチェック
            web_limit_match = re.search(r"WEB.*?(\d+(?:,\d{3})*)\s*万円", full_text)
            if web_limit_match:
                result["web_completion_limit"] = int(web_limit_match.group(1).replace(",", "")) * 10000
        
        return result

    @staticmethod
    def _extract_mycar_specific(soup: BeautifulSoup) -> Dict[str, Any]:
        """マイカーローン固有の抽出"""
        result = {}
        full_text = soup.get_text()
        
        # マイカーローン特有の特徴
        if "繰上返済手数料無料" in full_text:
            result["early_repayment_fee_free"] = True
        
        if "ボーナス返済" in full_text:
            result["bonus_repayment_available"] = True
        
        return result


def test_improved_extraction():
    """改良版抽出ロジックのテスト"""
    import requests
    
    test_urls = [
        ("カードローン", "https://www.am-bk.co.jp/kojin/loan/cardloan/"),
        ("教育カードローン", "https://www.am-bk.co.jp/kojin/loan/kyouikuloan/"),
    ]
    
    for name, url in test_urls:
        print(f"\n=== {name} テスト ===")
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 商品タイプの判定
            product_type = 'card' if 'cardloan' in url else 'education'
            
            # 改良版抽出実行
            extracted_data = ImprovedExtractionMethods.extract_structured_content(soup, product_type)
            
            print(f"抽出結果:")
            for key, value in extracted_data.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"エラー: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_improved_extraction()