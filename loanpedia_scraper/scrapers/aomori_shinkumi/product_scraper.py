# -*- coding: utf-8 -*-
"""
青森県信用組合商品スクレイパー
"""

import hashlib
import time
import requests
import urllib3
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import logging

from .config import (
    INSTITUTION_CODE, INSTITUTION_NAME, INSTITUTION_TYPE, WEBSITE_URL,
    LOAN_PRODUCTS, SCRAPING_CONFIG
)
from .html_parser import AomoriShinkumiHtmlParser

# SSL警告を無効化
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class AomoriShinkumiScraper:
    """青森県信用組合のローン情報スクレイパー"""

    def __init__(self):
        self.institution_code = INSTITUTION_CODE
        self.institution_name = INSTITUTION_NAME
        self.institution_type = INSTITUTION_TYPE
        self.website_url = WEBSITE_URL
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """HTTPセッションを作成"""
        session = requests.Session()
        verify_ssl = SCRAPING_CONFIG.get("verify_ssl", True)
        if isinstance(verify_ssl, bool):
            session.verify = verify_ssl

        user_agent = SCRAPING_CONFIG.get("user_agent", "")
        if isinstance(user_agent, (str, bytes)):
            session.headers.update({
                "User-Agent": user_agent
            })
        return session

    def scrape_loan_info(self) -> Dict[str, Any]:
        """全ローン商品の情報をスクレイピング"""
        logger.info(f"青森県信用組合のスクレイピングを開始")

        products = []
        failed_products = []

        for product_config in LOAN_PRODUCTS:
            try:
                logger.info(f"商品スクレイピング開始: {product_config['name']}")
                product_data = self._scrape_single_product(product_config)

                if product_data and product_data.get("scraping_status") == "success":
                    products.append(product_data)
                    logger.info(f"✅ {product_config['name']} スクレイピング成功")
                else:
                    failed_products.append(product_config['name'])
                    logger.warning(f"⚠️ {product_config['name']} スクレイピング失敗")

                # リクエスト間隔を空ける
                time.sleep(1)

            except Exception as e:
                logger.error(f"❌ {product_config['name']} でエラー: {e}")
                failed_products.append(product_config['name'])

        # 結果をまとめて返す
        result = {
            "institution_code": self.institution_code,
            "institution_name": self.institution_name,
            "institution_type": self.institution_type,
            "website_url": self.website_url,
            "scraping_status": "success",
            "scraped_at": datetime.now().isoformat(),
            "products": products,
            "total_products": len(products),
            "failed_products": failed_products,
            "success_rate": len(products) / len(LOAN_PRODUCTS) * 100 if LOAN_PRODUCTS else 0
        }

        logger.info(f"スクレイピング完了: {len(products)}/{len(LOAN_PRODUCTS)} 商品取得成功")
        return result

    def _scrape_single_product(self, product_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """単一商品の情報をスクレイピング"""
        url = product_config["url"]

        try:
            # リトライ機能付きでHTTPリクエスト
            response = self._make_request_with_retry(url)
            if not response:
                return None

            soup = BeautifulSoup(response.content, "html.parser")

            # 基本情報を構築
            product_data = self._build_base_product_data(product_config, url, response, soup)

            # HTMLパーサーでデータ抽出
            parser = AomoriShinkumiHtmlParser()
            extracted_data = parser.extract_table_data(soup)
            product_data.update(extracted_data)

            # 商品名を再抽出（より正確に）
            product_name = parser.extract_product_name(soup)
            product_data["name"] = product_name
            product_data["product_name"] = product_name

            # カテゴリを判定
            category = parser.determine_loan_category(product_name, url)
            product_data["category"] = category
            product_data["loan_category"] = category

            # 特徴を抽出
            features = parser.extract_special_features(soup)
            product_data["special_features"] = "; ".join(features) if features else ""

            # デフォルト値の設定
            self._set_default_values(product_data, category)

            return product_data

        except Exception as e:
            logger.error(f"商品スクレイピングエラー ({url}): {e}")
            return {
                "scraping_status": "failed",
                "error": str(e),
                "url": url
            }

    def _make_request_with_retry(self, url: str) -> Optional[requests.Response]:
        """リトライ機能付きHTTPリクエスト"""
        retry_count = SCRAPING_CONFIG.get("retry_count", 3)
        timeout = SCRAPING_CONFIG.get("timeout", 30)
        retry_delay = SCRAPING_CONFIG.get("retry_delay", 1)

        if not isinstance(retry_count, int):
            retry_count = 3
        if not isinstance(timeout, (int, float)):
            timeout = 30
        if not isinstance(retry_delay, (int, float)):
            retry_delay = 1

        for attempt in range(retry_count):
            try:
                response: requests.Response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                logger.warning(f"リクエスト失敗 (試行 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        return None

    def _build_base_product_data(
        self,
        product_config: Dict[str, str],
        url: str,
        response: requests.Response,
        soup: BeautifulSoup
    ) -> Dict[str, Any]:
        """基本商品データを構築"""
        html_text = response.text
        extracted_text = soup.get_text().strip()

        return {
            # 金融機関情報
            "institution_code": self.institution_code,
            "institution_name": self.institution_name,
            "institution_type": self.institution_type,
            "website_url": self.website_url,

            # 商品基本情報
            "product_id": product_config["product_id"],
            "name": product_config["name"],
            "product_name": product_config["name"],
            "category": product_config["category"],
            "loan_category": product_config["category"],

            # スクレイピング情報
            "source_url": url,
            "html_content": html_text,
            "extracted_text": extracted_text,
            "content_hash": hashlib.md5(html_text.encode()).hexdigest(),
            "scraping_status": "success",
            "scraped_at": datetime.now().isoformat(),

            # その他
            "interest_type": "変動金利"  # デフォルト
        }

    def _set_default_values(self, product_data: Dict[str, Any], category: str) -> None:
        """カテゴリに応じたデフォルト値を設定"""
        # 金利のデフォルト値
        if "min_interest_rate" not in product_data:
            if category == "カード":
                product_data["min_interest_rate"] = 4.0
                product_data["max_interest_rate"] = 14.8
            elif category in ["フリー", "多目的"]:
                product_data["min_interest_rate"] = 3.4
                product_data["max_interest_rate"] = 14.8
            else:
                product_data["min_interest_rate"] = 2.0
                product_data["max_interest_rate"] = 14.8

        # 融資額のデフォルト値
        if "min_loan_amount" not in product_data:
            product_data["min_loan_amount"] = 100000  # 10万円
            if category == "カード":
                product_data["max_loan_amount"] = 3000000  # 300万円
            else:
                product_data["max_loan_amount"] = 10000000  # 1000万円

        # 年齢のデフォルト値
        if "min_age" not in product_data:
            product_data["min_age"] = 20
            product_data["max_age"] = 80

        # その他のデフォルト値
        if "guarantor_requirements" not in product_data:
            product_data["guarantor_requirements"] = "原則不要（保証会社の保証を受けられる方）"

        if "income_requirements" not in product_data:
            product_data["income_requirements"] = "継続した収入のある方"