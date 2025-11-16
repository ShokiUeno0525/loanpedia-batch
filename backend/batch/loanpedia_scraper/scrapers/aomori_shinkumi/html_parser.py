# -*- coding: utf-8 -*-
"""
青森県信用組合HTMLパーサー
"""

import re
import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AomoriShinkumiHtmlParser:
    """青森県信用組合のHTMLパーシング専用クラス"""

    @staticmethod
    def extract_product_name(soup: BeautifulSoup) -> str:
        """商品名を抽出"""
        h1_elem = soup.find("h1")
        if h1_elem:
            text = h1_elem.get_text().strip()
            # "青森県信用組合 「商品名」" 形式から商品名のみ抽出
            match = re.search(r'青森県信用組合\s*[「""](.+?)[」""]', text)
            if match:
                return match.group(1)
            return text

        # タイトルからフォールバック
        title_elem = soup.find("title")
        if title_elem:
            text = title_elem.get_text().strip()
            if "青森県信用組合" in text:
                match = re.search(r'青森県信用組合[「""](.+?)[」""]', text)
                if match:
                    return match.group(1)

        return "不明な商品"

    @staticmethod
    def extract_table_data(soup: BeautifulSoup) -> Dict[str, Any]:
        """テーブルから構造化データを抽出"""
        result = {}
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    header = cells[0].get_text().strip()
                    content = cells[1].get_text().strip()

                    # 金利情報の抽出
                    if "適用金利" in header or "金利" in header:
                        rate_info = AomoriShinkumiHtmlParser._parse_interest_rate(content)
                        if rate_info:
                            result.update(rate_info)

                    # 借入金額の抽出
                    elif "借入金額" in header or "融資金額" in header:
                        amount_info = AomoriShinkumiHtmlParser._parse_loan_amount(content)
                        if amount_info:
                            result.update(amount_info)

                    # 年齢条件の抽出
                    elif "借入時年令" in header or "年齢" in header:
                        age_info = AomoriShinkumiHtmlParser._parse_age_condition(content)
                        if age_info:
                            result.update(age_info)

                    # 申込資格の抽出
                    elif "申込資格" in header:
                        result["eligibility_requirements"] = content

                    # 保証人要件の抽出
                    elif "連帯保証人" in header or "保証人" in header:
                        result["guarantor_requirements"] = content

                    # 資金使途の抽出
                    elif "資金使途" in header:
                        result["fund_usage"] = content

        return result

    @staticmethod
    def _parse_interest_rate(content: str) -> Optional[Dict[str, float]]:
        """金利情報をパース"""
        # 優遇金利や引き下げ関連の文言は除外
        if any(word in content for word in ['引下げ', '引下', '優遇', '割引', '最大', 'まで']):
            logger.info(f"⚠️ 優遇金利条件をスキップ: {content[:50]}...")
            return None

        # "3.4% ～ 14.8%" 形式の基本金利範囲
        rate_match = re.search(r'(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]', content)
        if rate_match:
            min_rate = float(rate_match.group(1))
            max_rate = float(rate_match.group(2))

            # 合理的な金利範囲かチェック（1.0% - 20.0%）
            if 1.0 <= min_rate <= 20.0 and 1.0 <= max_rate <= 20.0 and min_rate <= max_rate:
                logger.info(f"✅ 金利範囲抽出: {min_rate}% - {max_rate}%")
                return {
                    "min_interest_rate": min_rate,
                    "max_interest_rate": max_rate
                }
            else:
                logger.warning(f"⚠️ 不正な金利範囲をスキップ: {min_rate}% - {max_rate}%")

        # 単一金利（引き下げ条件でない場合のみ）
        single_rate_match = re.search(r'年\s*(\d+\.\d+)\s*[%％]', content)
        if single_rate_match:
            rate = float(single_rate_match.group(1))
            if 1.0 <= rate <= 20.0:
                logger.info(f"✅ 年利抽出: {rate}%")
                return {
                    "min_interest_rate": rate,
                    "max_interest_rate": rate
                }

        return None

    @staticmethod
    def _parse_loan_amount(content: str) -> Optional[Dict[str, int]]:
        """融資金額をパース"""
        # カードローン特有の複数金額表示への対応
        # "10万円以上100万円以下(10万円単位)、150万円、200万円" 形式
        if '万円以下' in content and ('、' in content or '万円' in content.split('万円以下')[1]):
            # 基本範囲を抽出
            range_match = re.search(r'(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以下', content)
            if range_match:
                min_amount = int(range_match.group(1).replace(',', '')) * 10000
                base_max = int(range_match.group(2).replace(',', '')) * 10000

                # 追加の金額（150万円、200万円等）を検索
                additional_amounts = re.findall(r'(\d+(?:,\d{3})*)\s*万円', content.split('万円以下')[1])
                if additional_amounts:
                    # 最大の追加金額を取得
                    max_additional = max([int(amt.replace(',', '')) for amt in additional_amounts]) * 10000
                    max_amount = max(base_max, max_additional)
                else:
                    max_amount = base_max

                logger.info(f"✅ カードローン融資金額範囲抽出: {min_amount:,}円 - {max_amount:,}円")
                return {
                    "min_loan_amount": min_amount,
                    "max_loan_amount": max_amount
                }

        # 通常の "10万円以上1,000万円以下" 形式
        amount_match = re.search(r'(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以下', content)
        if amount_match:
            min_amount = int(amount_match.group(1).replace(',', '')) * 10000
            max_amount = int(amount_match.group(2).replace(',', '')) * 10000
            logger.info(f"✅ 融資金額範囲抽出: {min_amount:,}円 - {max_amount:,}円")
            return {
                "min_loan_amount": min_amount,
                "max_loan_amount": max_amount
            }

        # "最高○○万円" 形式
        max_only_match = re.search(r'最高.*?(\d+(?:,\d{3})*)\s*万円', content)
        if max_only_match:
            max_amount = int(max_only_match.group(1).replace(',', '')) * 10000
            logger.info(f"✅ 最高融資金額抽出: {max_amount:,}円")
            return {
                "min_loan_amount": 100000,  # デフォルト最低額
                "max_loan_amount": max_amount
            }

        return None

    @staticmethod
    def _parse_age_condition(content: str) -> Optional[Dict[str, int]]:
        """年齢条件をパース"""
        # "満20歳以上" 形式
        min_age_match = re.search(r'満(\d+)歳以上', content)
        if min_age_match:
            min_age = int(min_age_match.group(1))

            # 完済時年齢を探す
            max_age_match = re.search(r'満(\d+)歳未満', content)
            if max_age_match:
                max_age = int(max_age_match.group(1)) - 1  # 未満なので-1
            else:
                max_age = 80  # デフォルト

            logger.info(f"✅ 年齢条件抽出: {min_age}歳 - {max_age}歳")
            return {
                "min_age": min_age,
                "max_age": max_age
            }

        return None

    @staticmethod
    def extract_special_features(soup: BeautifulSoup) -> List[str]:
        """特徴を抽出"""
        features = []
        full_text = soup.get_text()

        feature_patterns = [
            ("WEB完結", "WEB完結対応"),
            ("来店不要", "来店不要"),
            ("保証料込", "保証料込み"),
            ("繰上返済", "繰上返済対応"),
            ("自動更新", "自動更新"),
            ("ATM", "ATM利用可能")
        ]

        for pattern, feature in feature_patterns:
            if pattern in full_text:
                features.append(feature)

        return features

    @staticmethod
    def determine_loan_category(product_name: str, url: str) -> str:
        """商品名とURLから適切なカテゴリを判定"""
        name_lower = product_name.lower()
        url_lower = url.lower()

        if "カード" in product_name or "card" in url_lower:
            return "カード"
        elif "フリー" in product_name or "自由" in product_name:
            return "フリー"
        elif "多目的" in product_name:
            return "多目的"
        elif "住宅" in product_name or "housing" in url_lower:
            return "住宅"
        elif "教育" in product_name or "education" in url_lower:
            return "教育"
        elif "マイカー" in product_name or "自動車" in product_name or "car" in url_lower:
            return "自動車"
        else:
            return "その他"