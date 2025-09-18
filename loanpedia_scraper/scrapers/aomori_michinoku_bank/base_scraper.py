# -*- coding: utf-8 -*-
"""
青森みちのく銀行スクレイピング共通基盤

すべてのスクレイパーが継承する基底クラスと共通ユーティリティ
card.pyの改善された抽出ロジックを基準とした実装
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from abc import ABC
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class BaseLoanScraper(ABC):
    """
    青森みちのく銀行のローン情報スクレイピング基底クラス
    
    共通の抽出ロジックと設定を提供し、各ローン商品固有の処理は
    継承クラスでオーバーライドする
    """

    def __init__(self, institution_code: str = "0117"):
        self.institution_code = institution_code
        self.institution_name = "青森みちのく銀行"
        self.website_url = "https://www.am-bk.co.jp/"
        self.institution_type = "銀行"
        
        # HTTPセッションの初期化
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """共通のHTTPセッションを作成"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        return session
    
    def get_default_url(self) -> str:
        """各スクレイパー固有のデフォルトURLを返す（既定実装）"""
        return "https://www.am-bk.co.jp/kojin/loan/"
    
    def get_loan_type(self) -> str:
        """ローンタイプを返す（例: 'カードローン', '教育ローン', 'マイカーローン'）（既定実装）"""
        return "ローン"
    
    def get_loan_category(self) -> str:
        """ローンカテゴリを返す（既定実装）"""
        return "その他ローン"
    
    def get_interest_type(self) -> str:
        """金利タイプを返す（オーバーライド可能）"""
        return "変動金利"
    
    def scrape_loan_info(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        ローン情報をスクレイピングする共通メソッド
        
        Args:
            url: スクレイピング対象URL（Noneの場合はデフォルトURL使用）
            
        Returns:
            Dict: データモデル準拠の抽出情報
        """
        if url is None:
            url = self.get_default_url()
            
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # データモデル準拠の基本情報を構築
            item = self._build_base_item(url, response, soup)
            
            # 共通の抽出処理を実行
            self._extract_all_info(soup, item)
            
            return item
            
        except requests.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            return {"scraping_status": "failed", "error": str(e)}
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return {"scraping_status": "failed", "error": str(e)}
    
    def _build_base_item(self, url: str, response: requests.Response, soup: BeautifulSoup) -> Dict[str, Any]:
        """基本項目を構築"""
        # レスポンス本文（テストのMockにtextが無い場合も考慮）
        html_text = getattr(response, "text", None)
        if not isinstance(html_text, str):
            try:
                raw = getattr(response, "content", b"")
                html_text = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else ""
            except Exception:
                html_text = ""

        return {
            # financial_institutions テーブル用データ
            "institution_code": self.institution_code,
            "institution_name": self.institution_name,
            "website_url": self.website_url,
            "institution_type": self.institution_type,
            
            # raw_loan_data テーブル用データ
            "source_url": url,
            "html_content": html_text,
            "extracted_text": soup.get_text().strip(),
            "content_hash": hashlib.md5(html_text.encode()).hexdigest(),
            "scraping_status": "success",
            "scraped_at": datetime.now().isoformat(),
            
            # loan_products テーブル用の基本データ
            "product_name": self._extract_product_name(soup),
            "loan_type": self.get_loan_type(),
            "category": self.get_loan_category(),
            "loan_category": self.get_loan_category(),  # 互換キー
            "interest_type": self.get_interest_type(),
        }
    
    def _extract_all_info(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """すべての情報を抽出（改良版統合）"""
        # まず改良版構造化抽出を試行
        structured_data = self._extract_structured_content(soup)
        if structured_data:
            item.update(structured_data)
            logger.info("✅ 構造化抽出でデータを取得しました")
        
        # 不足している情報を従来の方法で補完
        if "min_interest_rate" not in item or "max_interest_rate" not in item:
            self._extract_interest_rates(soup, item)
        if "min_loan_amount" not in item or "max_loan_amount" not in item:
            self._extract_loan_amounts(soup, item)
        if "min_loan_term_months" not in item or "max_loan_term_months" not in item:
            self._extract_loan_periods(soup, item)
        
        # その他の情報は従来通り
        self._extract_age_requirements(soup, item)
        self._extract_detailed_requirements(soup, item)
        self._extract_repayment_method(soup, item)
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """商品名を抽出（共通実装）"""
        # titleタグから抽出
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text().strip()
            if any(keyword in title_text for keyword in ["ローン", "カード"]):
                return title_text
        
        # h1タグから抽出
        h1_elem = soup.find("h1")
        if h1_elem:
            h1_text = h1_elem.get_text().strip()
            if any(keyword in h1_text for keyword in ["ローン", "カード"]):
                return h1_text
        
        # デフォルト名（継承クラスでオーバーライド推奨）
        return f"青森みちのく{self.get_loan_type()}"
    
    def _extract_interest_rates(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """金利情報を抽出（card.pyの改良版を基準）"""
        full_text = soup.get_text()
        
        # 共通金利パターン（優先順位順）
        rate_patterns = [
            (r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "基本金利範囲"),
            (r"(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "金利範囲"),
            (r"金利.*?(\d+\.\d+)\s*[%％].*?(\d+\.\d+)\s*[%％]", "金利テーブル"),
            (r"変動金利.*?(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "変動金利"),
        ]
        
        for pattern, description in rate_patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    item["min_interest_rate"] = float(groups[0])
                    item["max_interest_rate"] = float(groups[1])
                    logger.info(
                        f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return
        
        # テーブルから金利を抽出
        self._extract_rates_from_table(soup, item)
        
        # 商品固有のデフォルト値設定（継承クラスでオーバーライド）
        if "min_interest_rate" not in item:
            default_rates = self._get_default_interest_rates()
            item["min_interest_rate"] = default_rates[0]
            item["max_interest_rate"] = default_rates[1]
            logger.info("⚠️ 金利情報が取得できませんでした。デフォルト値を使用")
    
    def _extract_rates_from_table(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """テーブルから金利情報を抽出"""
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                for cell in cells:
                    cell_text = cell.get_text().strip()
                    if "%" in cell_text:
                        rate_match = re.search(r"(\d+\.\d+)\s*[%％]", cell_text)
                        if rate_match:
                            rate = float(rate_match.group(1))
                            if "min_interest_rate" not in item:
                                item["min_interest_rate"] = rate
                                item["max_interest_rate"] = rate
                            else:
                                item["min_interest_rate"] = min(item["min_interest_rate"], rate)
                                item["max_interest_rate"] = max(item["max_interest_rate"], rate)
        
        if "min_interest_rate" in item:
            logger.info(
                f"✅ テーブルから金利抽出: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
            )
    
    def _extract_loan_amounts(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """融資金額を抽出（card.pyの改良版を使用）"""
        full_text = soup.get_text()
        logger.info(f"🔍 融資金額抽出開始 - テキストサンプル: {full_text[:200]}...")
        
        # 改善された正規表現パターン（優先順位順）
        amount_patterns = [
            # 「10万円～1,000万円」「10万～1000万円」形式
            (r"(\d+(?:,\d{3})*)\s*万円?\s*[〜～から]\s*(\d+(?:,\d{3})*)\s*万円", "範囲指定（万円単位）"),
            # 「100,000円～10,000,000円」形式 
            (r"(\d+(?:,\d{3})*)\s*円\s*[〜～から]\s*(\d+(?:,\d{3})*)\s*円", "範囲指定（円単位）"),
            # 「最高1,000万円」「限度額1000万円」形式
            (r"(?:最高|限度額|上限|最大)\s*(\d+(?:,\d{3})*)\s*万円", "上限のみ（万円単位）"),
            # 「最高10,000,000円」形式
            (r"(?:最高|限度額|上限|最大)\s*(\d+(?:,\d{3})*)\s*円", "上限のみ（円単位）"),
        ]
        
        for pattern, pattern_type in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                logger.info(f"🎯 パターンマッチ: {pattern_type} - マッチ内容: {match.group()}")
                
                groups = match.groups()
                if len(groups) == 2:
                    # 範囲指定の場合
                    min_amount = int(groups[0].replace(",", ""))
                    max_amount = int(groups[1].replace(",", ""))
                    
                    # 万円単位か円単位かで調整
                    if "万円" in pattern:
                        item["min_loan_amount"] = min_amount * 10000
                        item["max_loan_amount"] = max_amount * 10000
                    else:
                        item["min_loan_amount"] = min_amount
                        item["max_loan_amount"] = max_amount
                        
                elif len(groups) == 1:
                    # 上限のみの場合
                    max_amount = int(groups[0].replace(",", ""))
                    
                    # 万円単位か円単位かで調整
                    if "万円" in pattern:
                        default_min = self._get_default_min_loan_amount()
                        item["min_loan_amount"] = default_min
                        item["max_loan_amount"] = max_amount * 10000
                    else:
                        default_min = self._get_default_min_loan_amount()
                        item["min_loan_amount"] = default_min
                        item["max_loan_amount"] = max_amount
                
                logger.info(
                    f"✅ 融資金額範囲 ({pattern_type}): {item['min_loan_amount']:,}円 - {item['max_loan_amount']:,}円"
                )
                return
        
        # デフォルト値設定（継承クラスでオーバーライド）
        default_amounts = self._get_default_loan_amounts()
        item["min_loan_amount"] = default_amounts[0]
        item["max_loan_amount"] = default_amounts[1]
        logger.info("⚠️ 融資金額が取得できませんでした。デフォルト値を使用")
    
    def _extract_loan_periods(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """融資期間を抽出"""
        full_text = soup.get_text()
        
        # 共通期間パターン
        period_patterns = [
            (r"(\d+)\s*年.*?自動更新", "自動更新期間"),
            (r"契約期間.*?(\d+)\s*年", "契約期間"),
            (r"最大\s*(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "年月形式"),
            (r"最大\s*(\d+)\s*年", "最長年数"),
            (r"(\d+)\s*年間", "年間契約"),
        ]
        
        for pattern, pattern_type in period_patterns:
            match = re.search(pattern, full_text)
            if match:
                if pattern_type == "年月形式" and len(match.groups()) >= 2:
                    years = int(match.group(1))
                    months = int(match.group(2))
                    max_months = years * 12 + months
                    item["min_loan_term_months"] = self._get_default_min_loan_term()
                    item["max_loan_term_months"] = max_months
                else:
                    years = int(match.group(1))
                    item["min_loan_term_months"] = self._get_default_min_loan_term()
                    item["max_loan_term_months"] = years * 12
                
                logger.info(
                    f"✅ 融資期間: {item.get('min_loan_term_months', 0)}ヶ月 - {item.get('max_loan_term_months', 0)}ヶ月 ({pattern_type})"
                )
                return
        
        # デフォルト値設定
        default_terms = self._get_default_loan_terms()
        item["min_loan_term_months"] = default_terms[0]
        item["max_loan_term_months"] = default_terms[1]
        logger.info("⚠️ 融資期間が取得できませんでした。デフォルト値を使用")
    
    def _extract_age_requirements(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """年齢制限を抽出"""
        full_text = soup.get_text()
        
        age_patterns = [
            r"満(\d+)歳以上.*?満(\d+)歳未満",
            r"満(\d+)歳以上.*?満(\d+)歳以下", 
            r"(\d+)歳以上.*?(\d+)歳以下",
            r"(\d+)歳[〜～](\d+)歳",
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, full_text)
            if match:
                item["min_age"] = int(match.group(1))
                max_age_value = int(match.group(2))
                
                # 「未満」の場合は-1する（75歳未満 = 74歳以下）
                if "未満" in pattern:
                    item["max_age"] = max_age_value - 1
                else:
                    item["max_age"] = max_age_value
                
                logger.info(f"✅ 年齢制限: {item['min_age']}歳 - {item['max_age']}歳")
                return
        
        # デフォルト値
        default_ages = self._get_default_age_range()
        item["min_age"] = default_ages[0]
        item["max_age"] = default_ages[1]
    
    def _extract_detailed_requirements(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """収入条件、保証人要件、商品特徴を抽出"""
        full_text = soup.get_text()
        
        # 収入条件
        income_requirements = []
        if "安定した収入" in full_text:
            income_requirements.append("安定した収入があること")
        if "継続的な収入" in full_text:
            income_requirements.append("継続的な収入があること")
        
        item["income_requirements"] = "; ".join(income_requirements) if income_requirements else "安定した収入があること"
        
        # 保証人要件（継承クラスでカスタマイズ可能）
        item["guarantor_requirements"] = self._extract_guarantor_requirements(full_text)
        
        # 商品特徴（継承クラスでカスタマイズ可能）
        item["special_features"] = self._extract_special_features(full_text)
        
        logger.info(f"✅ 商品特徴: {item['special_features']}")
    
    def _extract_guarantor_requirements(self, full_text: str) -> str:
        """保証人要件を抽出（継承クラスでオーバーライド可能）"""
        if "保証人" in full_text and "不要" in full_text:
            return "原則不要（保証会社が保証）"
        elif "保証会社" in full_text:
            return "保証会社による保証"
        return ""
    
    def _extract_special_features(self, full_text: str) -> str:
        """商品特徴を抽出（継承クラスでオーバーライド可能）"""
        features = []
        
        # 共通特徴
        if "WEB" in full_text and ("申込" in full_text or "完結" in full_text):
            features.append("WEB申込対応")
        if "来店不要" in full_text:
            features.append("来店不要")
        if "ATM" in full_text:
            features.append("ATM利用可能")
        
        return "; ".join(features)
    
    def _extract_repayment_method(self, soup: BeautifulSoup, item: Dict[str, Any]) -> None:
        """返済方法を抽出"""
        full_text = soup.get_text()
        
        repayment_methods = []
        if "自動振替" in full_text:
            repayment_methods.append("口座自動振替")
        if "元利均等" in full_text:
            repayment_methods.append("元利均等返済")
        if "随時返済" in full_text:
            repayment_methods.append("随時返済可能")
        
        if not repayment_methods:
            repayment_methods.append(self._get_default_repayment_method())
        
        item["repayment_method"] = "; ".join(repayment_methods)
        logger.info(f"✅ 返済方法: {item['repayment_method']}")
    
    # 継承クラスでオーバーライドするべきデフォルト値メソッド
    def _get_default_interest_rates(self) -> Tuple[float, float]:
        """デフォルト金利範囲"""
        return (2.0, 14.5)
    
    def _get_default_loan_amounts(self) -> Tuple[int, int]:
        """デフォルト融資金額範囲"""
        return (100000, 10000000)  # 10万円〜1000万円
    
    def _get_default_min_loan_amount(self) -> int:
        """デフォルト最小融資額"""
        return 100000  # 10万円
    
    def _get_default_loan_terms(self) -> Tuple[int, int]:
        """デフォルト融資期間範囲（ヶ月）"""
        return (12, 36)  # 1年〜3年
    
    def _get_default_min_loan_term(self) -> int:
        """デフォルト最小融資期間（ヶ月）"""
        return 12  # 1年
    
    def _get_default_age_range(self) -> Tuple[int, int]:
        """デフォルト年齢範囲"""
        return (20, 75)
    
    def _get_default_repayment_method(self) -> str:
        """デフォルト返済方法"""
        return "口座自動振替"

    # =========================
    # 改良版抽出ロジック統合
    # =========================
    
    def _extract_structured_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        構造化コンテンツの抽出（改良版）
        """
        result: Dict[str, Any] = {}
        
        # 1. テーブルデータを最優先で抽出
        table_data = self._extract_loan_table_data(soup)
        result.update(table_data)
        
        # 2. 詳細金利テーブルで補完
        if "min_interest_rate" not in result:
            detailed_rates = self._extract_detailed_rate_table(soup)
            if detailed_rates:
                result["min_interest_rate"] = detailed_rates[0]
                result["max_interest_rate"] = detailed_rates[1]
        
        # 3. 商品概要で補完
        overview_data = self._extract_product_overview(soup)
        
        # 4. 製品固有の抽出ロジック
        product_type = self._get_product_type(self.get_default_url())
        if product_type:
            result.update(self._extract_product_specific_data(soup, product_type))
        
        return result
    
    def _extract_loan_table_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """テーブル形式のローンデータを抽出"""
        result: Dict[str, Any] = {}
        
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
                            result["min_loan_term_months"] = 12
                            logger.info(f"✅ テーブルから融資期間: {result['max_loan_term_months']}ヶ月")
        
        return result
    
    def _extract_detailed_rate_table(self, soup: BeautifulSoup) -> Optional[Tuple[float, float]]:
        """詳細金利テーブルから金利範囲を抽出"""
        tables = soup.find_all('table')
        rates = []
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                for cell in cells:
                    cell_text = cell.get_text().strip()
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
    
    def _extract_product_overview(self, soup: BeautifulSoup) -> Dict[str, str]:
        """商品概要セクションからデータを抽出"""
        overview_data = {}
        
        overview_headers = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'商品概要|商品詳細|商品内容'))
        
        for header in overview_headers:
            next_elements = header.find_all_next()
            
            for elem in next_elements[:20]:
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
    
    def _get_product_type(self, url: str | None = None) -> str:
        """商品タイプを判定（URL優先、なければ型情報から推測）"""
        if url:
            u = url.lower()
            if "mycar" in u:
                return "mycar"
            if "education" in u:
                return "education"
            if "freeloan" in u:
                return "freeloan"
        # フォールバック: 型情報から推測
        loan_type = self.get_loan_type()
        loan_category = self.get_loan_category()
        if "カードローン" in loan_category:
            return "card"
        if "教育" in loan_type:
            return "education"
        if "自動車" in loan_type or "マイカー" in loan_category:
            return "mycar"
        return "general"
    
    def _extract_product_specific_data(self, soup: BeautifulSoup, product_type: str) -> Dict[str, Any]:
        """商品タイプに応じた固有データの抽出"""
        result: Dict[str, Any] = {}
        full_text = soup.get_text()
        
        if product_type == 'card':
            if "3年自動更新" in full_text:
                result["loan_term_note"] = "3年自動更新"
            if "専用カード" in full_text:
                result["card_issuance"] = True
        
        elif product_type == 'education':
            if "在学中" in full_text and "利息のみ" in full_text:
                result["interest_only_during_study"] = True
            if "WEB完結" in full_text:
                web_limit_match = re.search(r"WEB.*?(\d+(?:,\d{3})*)\s*万円", full_text)
                if web_limit_match:
                    result["web_completion_limit"] = int(web_limit_match.group(1).replace(",", "")) * 10000
        
        elif product_type == 'mycar':
            if "繰上返済手数料無料" in full_text:
                result["early_repayment_fee_free"] = True
            if "ボーナス返済" in full_text:
                result["bonus_repayment_available"] = True
        
        return result


# ========== AomorimichinokuBankScraper 実装 ==========

class AomorimichinokuBankScraper(BaseLoanScraper):
    """
    青森みちのく銀行の統合スクレイパー
    各ローン商品の共通インターフェースを提供
    """
    
    def __init__(self, product_type: str = "general", institution_code: str = "0117"):
        super().__init__(institution_code)
        self.product_type = product_type
        
    def get_default_url(self) -> str:
        """商品タイプに応じたデフォルトURL"""
        urls = {
            "mycar": "https://www.am-bk.co.jp/kojin/loan/mycarloan/",
            "education": "https://www.am-bk.co.jp/kojin/loan/kyouikuloan_hanpuku/",
            "freeloan": "https://www.am-bk.co.jp/kojin/loan/freeloan/",
            "omatomeloan": "https://www.am-bk.co.jp/kojin/loan/omatomeloan/",
        }
        return urls.get(self.product_type, "https://www.am-bk.co.jp/kojin/loan/")
    
    def get_loan_type(self) -> str:
        """商品タイプに応じたローンタイプ"""
        types = {
            "mycar": "マイカーローン",
            "education": "教育ローン",
            "education_deed": "教育ローン",
            "education_card": "教育カードローン",
            "freeloan": "フリーローン",
            "omatomeloan": "おまとめローン",
        }
        return types.get(self.product_type, "ローン")
    
    def get_loan_category(self) -> str:
        """商品タイプに応じたカテゴリ"""
        categories = {
            "mycar": "目的別ローン",
            "education": "目的別ローン", 
            "education_deed": "目的別ローン",
            "education_card": "カードローン",
            "freeloan": "多目的ローン",
            "omatomeloan": "おまとめローン",
        }
        return categories.get(self.product_type, "その他ローン")
    
    def _get_default_interest_rates(self) -> Tuple[float, float]:
        """商品タイプ別のデフォルト金利範囲"""
        rates = {
            "mycar": (1.8, 3.8),
            "education": (2.3, 3.8),
            "education_deed": (2.3, 3.8),
            "education_card": (3.5, 5.5),
            "freeloan": (6.8, 14.5),
            "omatomeloan": (6.8, 12.5),
        }
        return rates.get(self.product_type, (2.0, 14.5))
    
    def _get_default_loan_amounts(self) -> Tuple[int, int]:
        """商品タイプ別のデフォルト融資金額範囲"""
        amounts = {
            "mycar": (100000, 10000000),      # 10万円〜1000万円
            "education": (100000, 5000000),   # 10万円〜500万円
            "education_deed": (100000, 5000000),
            "education_card": (100000, 3000000),  # 10万円〜300万円
            "freeloan": (100000, 5000000),    # 10万円〜500万円
            "omatomeloan": (100000, 5000000),
        }
        return amounts.get(self.product_type, (100000, 5000000))
    
    def _get_default_loan_terms(self) -> Tuple[int, int]:
        """商品タイプ別のデフォルト融資期間範囲（ヶ月）"""
        terms = {
            "mycar": (6, 120),        # 6ヶ月〜10年
            "education": (12, 180),   # 1年〜15年
            "education_deed": (12, 180),
            "education_card": (12, 36),   # 1年〜3年（自動更新）
            "freeloan": (6, 84),      # 6ヶ月〜7年
            "omatomeloan": (6, 120),  # 6ヶ月〜10年
        }
        return terms.get(self.product_type, (12, 84))
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aomori_michinoku_bank/base_scraper.py
# 共通スクレイパー基底（セッション/標準I/F）
# なぜ: 銀行/金庫間での再利用性と整合性の確保のため
# 関連: product_scraper.py, http_client.py, html_parser.py
