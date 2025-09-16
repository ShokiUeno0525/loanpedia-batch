"""東奥信用金庫向けPDFスクレイパー

PDFから金利表を抽出し、構造化されたローン商品データに変換する。
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from . import http_client
from .config import get_pdf_urls, pick_profile_from_pdf, INSTITUTION_INFO
from .models import build_base_item, merge_product_fields
from .pdf_parser import extract_from_pdf_url

logger = logging.getLogger(__name__)

# 共通ヘッダー
HEADERS = {
    "Accept": "application/pdf,*/*",
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
}


class TououShinkinScraper:
    """
    東奥信用金庫のPDF商品カタログから金利表を抽出する専用スクレイパー
    """

    def __init__(self, save_to_db: bool = False, db_config: Optional[Dict[str, Any]] = None):
        self.save_to_db = save_to_db
        self.db_config = db_config
        self.session = http_client.build_session(HEADERS)

    def scrape_loan_info(self, url: Optional[str] = None) -> Dict[str, Any]:
        """ローン情報をスクレイピングして構造化データとして返す"""
        item = build_base_item()

        # 組織情報を追加
        item.update(INSTITUTION_INFO)

        results: List[Dict[str, Any]] = []
        db_saved_ids: List[int] = []

        # DB設定の初期化（必要な場合）
        LoanDatabase = None
        get_database_config = None
        if self.save_to_db:
            try:
                from loanpedia_scraper.database.loan_database import LoanDatabase as _LD, get_database_config as _gdc
                LoanDatabase = _LD
                get_database_config = _gdc
            except Exception as e:
                logger.warning(f"DB modules not available, continue without DB saving: {e}")
                self.save_to_db = False

        # DB設定の補完
        if self.save_to_db and not self.db_config and get_database_config:
            try:
                self.db_config = get_database_config()
            except Exception as e:
                logger.warning(f"Failed to load DB config, disable saving: {e}")
                self.save_to_db = False

        def save_pdf_result_if_needed(base: Dict[str, Any], parsed: Dict[str, Any], source_url: str):
            """PDF結果をDBに保存するヘルパー"""
            if not self.save_to_db or not LoanDatabase or not self.db_config:
                return
            try:
                loan_data = {
                    **base,
                    **parsed,
                    "source_url": source_url,
                    "pdf_content": "PDF data extracted",  # PDF内容のプレースホルダー
                }

                with LoanDatabase(self.db_config) as db:
                    if db:
                        saved_id = db.save_loan_data(loan_data)
                        if saved_id:
                            db_saved_ids.append(int(saved_id))
            except Exception as e:
                logger.warning(f"Failed to save PDF result to DB: {e}")

        # PDF URLsから情報を抽出
        pdf_urls = [url] if url else get_pdf_urls()

        for pdf_url in pdf_urls:
            try:
                logger.info(f"Processing PDF: {pdf_url}")

                # PDFプロファイルを取得
                profile = pick_profile_from_pdf(pdf_url)

                # PDFからデータを抽出
                pdf_records = extract_from_pdf_url(pdf_url)

                for record in pdf_records:
                    # プロファイル情報を追加
                    enhanced_record = {**record, **profile}

                    # ベース項目とマージ
                    merged = merge_product_fields(item, enhanced_record)
                    results.append(merged)

                    # DB保存
                    save_pdf_result_if_needed(item, enhanced_record, pdf_url)

            except Exception as e:
                logger.warning(f"PDF parse failed for {pdf_url}: {e}")
                continue

        # 結果の検証と返却
        if not results:
            logger.info("No loan products extracted from PDFs")
            return {
                **item,
                "products": [],
                "scraping_status": "success",
                "db_saved_ids": db_saved_ids if self.save_to_db else None
            }

        logger.info(f"Successfully extracted {len(results)} loan products")
        return {
            **item,
            "products": results,
            "scraping_status": "success",
            "db_saved_ids": db_saved_ids if self.save_to_db else None
        }