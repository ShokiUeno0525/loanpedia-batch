"""青い森信用金庫向けのプロダクトスクレイパーエントリポイント"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from .config import HEADERS, START, get_product_urls, get_pdf_urls
from . import http_client
from .html_parser import parse_html_document
from .pdf_parser import extract_from_pdf_url
from .models import build_base_item, merge_product_fields

logger = logging.getLogger(__name__)


class AoimoriShinkinScraper:
    """
    HTMLページの解析と、必要に応じたPDF（金利表）抽出を統合して実行する高レベルスクレイパー
    """

    def __init__(self, save_to_db: bool = False, db_config: Optional[Dict[str, Any]] = None):
        self.save_to_db = save_to_db
        self.db_config = db_config
        self.session = http_client.build_session(HEADERS)

    def scrape_loan_info(self, url: Optional[str] = None) -> Dict[str, Any]:
        item = build_base_item()

        results: List[Dict[str, Any]] = []
        html_error: Optional[str] = None
        db_saved_ids: List[int] = []

        # DB未使用時に不要な依存を避けるため遅延インポート
        LoanDatabase = None  # type: ignore
        get_database_config = None  # type: ignore
        if self.save_to_db:
            try:
                from loanpedia_scraper.database.loan_database import LoanDatabase as _LD, get_database_config as _gdc  # type: ignore
                LoanDatabase = _LD  # type: ignore
                get_database_config = _gdc  # type: ignore
            except Exception as e:
                logger.warning(f"DB modules not available, continue without DB saving: {e}")
                self.save_to_db = False

        # 保存が有効な場合に db_config を補完
        if self.save_to_db and not self.db_config and get_database_config:
            try:
                self.db_config = get_database_config()  # type: ignore
            except Exception as e:
                logger.warning(f"Failed to load DB config, disable saving: {e}")
                self.save_to_db = False

        # HTML由来の単一結果を正規化して保存するヘルパー
        def save_html_result_if_needed(base: Dict[str, Any], parsed: Dict[str, Any], source_url: str, page_title: Optional[str], html_text: str):
            if not self.save_to_db or not LoanDatabase or not self.db_config:
                return
            try:
                # DBレイヤが期待するキーへマッピング
                loan_data: Dict[str, Any] = {
                    **base,
                    **parsed,
                    "source_url": source_url,
                    "page_title": page_title or "",
                    "html_content": html_text or "",
                }
                # 期間キーの命名差異を吸収
                if "min_loan_term_months" in loan_data and "min_loan_period_months" not in loan_data:
                    loan_data["min_loan_period_months"] = loan_data["min_loan_term_months"]
                if "max_loan_term_months" in loan_data and "max_loan_period_months" not in loan_data:
                    loan_data["max_loan_period_months"] = loan_data["max_loan_term_months"]

                with LoanDatabase(self.db_config) as db:  # type: ignore
                    if db:
                        saved_id = db.save_loan_data(loan_data)  # type: ignore
                        if saved_id:
                            db_saved_ids.append(int(saved_id))
            except Exception as e:
                logger.warning(f"Failed to save HTML result to DB: {e}")

        # 1) HTMLページ: 明示URL > 設定された商品URL一覧 > STARTのフォールバック
        attempted = False
        if url:
            attempted = True
            try:
                resp = http_client.get(self.session, url, timeout=15)
                soup = BeautifulSoup(resp.content, "html.parser")
                html_part = parse_html_document(soup)
                # DB保存用にタイトル/本文を取得
                page_title = None
                try:
                    title_el = soup.find("title")
                    page_title = title_el.get_text(strip=True) if title_el else None
                except Exception:
                    page_title = None
                html_text = getattr(resp, "text", None) or resp.content.decode("utf-8", errors="ignore")

                merged = merge_product_fields(item, {**html_part, "source_url": url})
                results.append(merged)
                save_html_result_if_needed(item, html_part, url, page_title, html_text)
            except Exception as e:
                html_error = str(e)
                logger.warning(f"HTML parse skipped/failed: {e}")
        else:
            plist = get_product_urls()
            if plist:
                attempted = True
                for p in plist:
                    purl = str(p.get("url") or "")
                    try:
                        resp = http_client.get(self.session, purl, timeout=15)
                        soup = BeautifulSoup(resp.content, "html.parser")
                        html_part = parse_html_document(soup)
                        item_with_name = {**html_part}
                        if p.get("name") and not item_with_name.get("product_name"):
                            item_with_name["product_name"] = str(p["name"])
                        # タイトルとHTML本文
                        page_title = None
                        try:
                            title_el = soup.find("title")
                            page_title = title_el.get_text(strip=True) if title_el else None
                        except Exception:
                            page_title = None
                        html_text = getattr(resp, "text", None) or resp.content.decode("utf-8", errors="ignore")

                        merged = merge_product_fields(item, {**item_with_name, "source_url": purl})
                        results.append(merged)
                        save_html_result_if_needed(item, item_with_name, purl, page_title or "", html_text)
                    except Exception as e:
                        html_error = str(e)
                        logger.warning(f"HTML parse skipped/failed for {purl}: {e}")
            elif START:
                attempted = True
                try:
                    resp = http_client.get(self.session, START, timeout=15)
                    soup = BeautifulSoup(resp.content, "html.parser")
                    html_part = parse_html_document(soup)
                    page_title = None
                    try:
                        title_el = soup.find("title")
                        page_title = title_el.get_text(strip=True) if title_el else None
                    except Exception:
                        page_title = None
                    html_text = getattr(resp, "text", None) or resp.content.decode("utf-8", errors="ignore")

                    merged = merge_product_fields(item, {**html_part, "source_url": START})
                    results.append(merged)
                    save_html_result_if_needed(item, html_part, START, page_title, html_text)
                except Exception as e:
                    html_error = str(e)
                    logger.warning(f"HTML parse skipped/failed: {e}")

        # 2) PDFテーブル（環境変数で有効化されている場合のみ）
        for pdf_url in get_pdf_urls():
            try:
                pdf_rows = extract_from_pdf_url(pdf_url)
                for r in pdf_rows:
                    results.append(merge_product_fields(item, r))
            except Exception as e:
                logger.warning(f"PDF parse skipped/failed for {pdf_url}: {e}")

        # エラー方針: テストモードではHTMLエラーがあれば失敗を返す
        import os
        if os.getenv("SCRAPING_TEST_MODE") == "true" and html_error:
            return {**item, "status": "failed", "error": html_error}

        # それ以外: 収集ゼロなら空で成功、HTMLエラーのみなら失敗
        if not results:
            if html_error:
                return {**item, "status": "failed", "error": html_error}
            # 空のproductsでも成功とみなす
            return {**item, "products": [], "scraping_status": "success", "db_saved_ids": db_saved_ids if self.save_to_db else None}
        return {**item, "products": results, "scraping_status": "success", "db_saved_ids": db_saved_ids if self.save_to_db else None}
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aoimori_shinkin/product_scraper.py
# 青い森信用金庫のメインスクレイパー（製品抽出）
# なぜ: 金利/条件/メタ情報を統合し標準構造化データを生成するため
# 関連: http_client.py, html_parser.py, pdf_parser.py, ../../database/loan_database.py
