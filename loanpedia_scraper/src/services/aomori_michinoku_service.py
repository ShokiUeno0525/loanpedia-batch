"""
青森みちのく銀行 統合スクレイピング サービス

ハンドラーから呼び出される実行サービス。イベント解釈、対象選別、
スクレイパー実行、DB保存、レスポンス生成までを担当。
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def _to_event_dict(event: Any) -> Dict[str, Any]:
    if event is None:
        return {}
    if isinstance(event, str):
        try:
            return json.loads(event)
        except Exception:
            return {}
    if isinstance(event, dict):
        return event
    return {}


def _load_registry():
    """商品ごとのスクレイパーとメタのレジストリを構築"""
    # パス解決（Lambdaでは /var/task がモジュールルート）
    try:
        from scrapers.aomori_michinoku_bank import product_scraper as _product_scraper
        from scrapers.aomori_michinoku_bank import config as _config
    except Exception:
        handler_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(handler_dir)))
        for p in [project_root, os.path.join(project_root, "scrapers")]:
            if p not in sys.path:
                sys.path.insert(0, p)
        from scrapers.aomori_michinoku_bank import product_scraper as _product_scraper
        from scrapers.aomori_michinoku_bank import config as _config

    scrape_product = _product_scraper.scrape_product
    profiles = _config.profiles  # noqa: F401 (将来拡張で使用)

    class ProductScraper:
        def __init__(self, url: str, pdf_url_override: str = None):
            self.url = url
            self.pdf_url_override = pdf_url_override

        def scrape_loan_info(self) -> Dict[str, Any]:
            try:
                product, raw_data = scrape_product(
                    self.url,
                    fin_id=int(os.getenv("AOMORI_MICHINOKU_ID", "1")),
                    pdf_url_override=self.pdf_url_override,
                )
                # 特徴は配列に正規化（" / "区切り想定）
                feat_list = None
                if product.special_features:
                    parts = [p.strip() for p in str(product.special_features).split("/")]
                    feat_list = [p for p in parts if p]

                # 統一キーで返却（互換フィールドも最小限で併記）
                unified = {
                    "scraping_status": "success",
                    "product_name": product.product_name,
                    "loan_category": product.category or product.loan_type,
                    "min_interest_rate": product.min_interest_rate,
                    "max_interest_rate": product.max_interest_rate,
                    "interest_rate_type": product.interest_type,
                    "min_loan_amount": product.min_loan_amount,
                    "max_loan_amount": product.max_loan_amount,
                    "min_loan_period_months": product.min_loan_term,
                    "max_loan_period_months": product.max_loan_term,
                    "repayment_method": product.repayment_method,
                    "min_age": product.min_age,
                    "max_age": product.max_age,
                    "features": feat_list,
                    "source_reference": product.source_reference,
                    "raw_data": raw_data.model_dump() if raw_data else None,
                }
                # 互換キー（既存の他箇所参照向け。段階的に削除可）
                unified.update({
                    "category": unified["loan_category"],
                    "interest_type": unified["interest_rate_type"],
                    "min_loan_term": unified["min_loan_period_months"],
                    "max_loan_term": unified["max_loan_period_months"],
                    "special_features": product.special_features,
                })
                return unified
            except Exception as e:
                return {"scraping_status": "error", "error": str(e)}

    reg: Dict[str, Dict[str, Any]] = {}
    reg["mycar"] = {
        "name": "青森みちのくマイカーローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/mycarloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-75.pdf",
        ),
    }
    reg["education"] = {
        "name": "青森みちのく教育ローン反復利用型",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/kyouikuloan_hanpuku/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-77.pdf",
        ),
    }
    reg["education_deed"] = {
        "name": "青森みちのく教育ローン証書貸付型",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/certificate/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-78.pdf",
        ),
    }
    reg["education_card"] = {
        "name": "青森みちのく教育カードローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/kyouikuloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-79.pdf",
        ),
    }
    reg["freeloan"] = {
        "name": "青森みちのくフリーローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/freeloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-81.pdf",
        ),
    }
    reg["omatomeloan"] = {
        "name": "青森みちのくおまとめローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/omatomeloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-83.pdf",
        ),
    }
    return reg


def _save(product_data: Dict[str, Any], raw_data_dict: Dict[str, Any]) -> bool:
    # サービス層（DB保存）
    from database.loan_service import save_scraped_product

    return save_scraped_product(
        institution_code="aomori_michinoku",
        institution_name="青森みちのく銀行",
        product_data=product_data,
        raw_data_dict=raw_data_dict,
    )


def _run_one(product_key: str, reg: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    info = reg[product_key]
    name = info["name"]
    cls = info["cls"]

    logger.info(f"▶ {name} のスクレイピング開始")
    try:
        scraper = cls()
        result = scraper.scrape_loan_info()
        if result and result.get("scraping_status") == "success":
            logger.info(f"✅ {name} のスクレイピング成功")
            raw_data = result.get("raw_data", {})
            db_saved = _save(result, raw_data)
            return {
                "product": product_key,
                "product_name": name,
                "success": True,
                "result": result,
                "error": None,
                "db_saved": db_saved,
            }
        else:
            error_msg = (result or {}).get("error") or "スクレイパーが失敗/結果なし"
            logger.error(f"❌ {name} のスクレイピング失敗: {error_msg}")
            return {
                "product": product_key,
                "product_name": name,
                "success": False,
                "result": result,
                "error": error_msg,
            }
    except Exception as e:
        logger.exception(f"❌ {name} で例外発生")
        return {
            "product": product_key,
            "product_name": name,
            "success": False,
            "result": None,
            "error": f"Exception: {e}",
        }


def _run_many(targets: List[str]) -> Tuple[List[Dict[str, Any]], int, int]:
    reg = _load_registry()
    results: List[Dict[str, Any]] = []
    ok = 0
    ng = 0
    for key in targets:
        r = _run_one(key, reg)
        results.append(r)
        ok += 1 if r["success"] else 0
        ng += 0 if r["success"] else 1
        time.sleep(float(os.getenv("SCRAPE_SLEEP_SEC", "2.0")))
    return results, ok, ng


def _parse_targets(evt: Dict[str, Any]) -> List[str]:
    reg_keys = list(_load_registry().keys())
    p = evt.get("product", "all")
    if isinstance(p, list):
        return p or reg_keys
    if isinstance(p, str):
        if p == "all":
            return reg_keys
        return [p]
    return reg_keys


def run(event: Any) -> Dict[str, Any]:
    """ハンドラーから呼び出すエントリポイント（Lambda Proxy互換レスポンスを返す）"""
    evt = _to_event_dict(event)

    # SQSバッチ簡易対応
    if "Records" in evt and isinstance(evt["Records"], list):
        for rec in evt["Records"]:
            try:
                body = json.loads(rec.get("body") or "{}")
                run(body)
            except Exception:
                logger.exception("SQS record handling error")
        return {"batchItemFailures": []}

    targets = _parse_targets(evt)
    all_keys = set(_load_registry().keys())
    invalid = [k for k in targets if k not in all_keys]
    if invalid:
        body = {
            "success": False,
            "error": "InvalidProduct",
            "message": f"無効な商品指定: {invalid}",
            "available_products": sorted(all_keys),
            "institution": "aomori_michinoku",
            "timestamp": datetime.now().isoformat(),
        }
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps(body, ensure_ascii=False),
        }

    results, ok, ng = _run_many(targets)
    overall_success = ok > 0 and ng == 0
    status = 200 if overall_success else (207 if ok > 0 else 500)

    body = {
        "success": overall_success,
        "message": f"統合スクレイピング完了: 成功{ok}件、失敗{ng}件",
        "institution": "aomori_michinoku",
        "target_products": targets,
        "summary": {
            "total_products": len(targets),
            "success_count": ok,
            "error_count": ng,
        },
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }

    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }
