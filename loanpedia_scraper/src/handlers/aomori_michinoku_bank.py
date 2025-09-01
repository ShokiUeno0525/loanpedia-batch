# handlers_aomori_michinoku.py
# -*- coding: utf-8 -*-
"""
青森みちのく銀行 統合Lambdaハンドラー
- 固定PDF+HTML金利スクレイプの各商品スクレイパーを集約
- API Gateway / SQS / ローカル直叩き で共通に使えるディスパッチ
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, cast

# パス設定ユーティリティ
def _setup_paths():
    """Lambda環境とローカル実行環境の両方でモジュールパスを設定"""
    handler_dir = os.path.dirname(os.path.abspath(__file__))
    # loanpedia_scraper レベルまで遡る
    loanpedia_scraper_root = os.path.dirname(os.path.dirname(handler_dir))
    
    paths_to_add = [
        "/var/task",  # Lambda環境
        "/var/task/scrapers",
        "/var/task/database", 
        handler_dir,  # ローカル実行用
        os.path.join(loanpedia_scraper_root, "scrapers", "aomori_michinoku_bank"),
        os.path.join(loanpedia_scraper_root, "database"),
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)

# パスの初期設定
_setup_paths()

# 設定とロガーの初期化
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# 定数定義
INSTITUTION_KEY = "aomori_michinoku"
FINANCIAL_INSTITUTION_ID = int(os.getenv("AOMORI_MICHINOKU_ID", "1"))
SCRAPE_SLEEP_SEC = float(os.getenv("SCRAPE_SLEEP_SEC", "2.0"))
DB_RETRY_MAX = int(os.getenv("DB_RETRY_MAX", "5"))
DB_RETRY_BASE_DELAY = float(os.getenv("DB_RETRY_BASE_DELAY", "1.0"))


# ========== レスポンス・ユーティリティ（Lambda Proxy 互換） ==========
def _resp(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _ok(body: Dict[str, Any]) -> Dict[str, Any]:
    return _resp(200, body)


def _err(status: int, code: str, message: str, **extra) -> Dict[str, Any]:
    payload = {
        "success": False,
        "error": code,
        "message": message,
        "institution": INSTITUTION_KEY,
        "timestamp": datetime.now().isoformat(),
    }
    payload.update(extra)
    return _resp(status, payload)


def _to_event_dict(event: Any) -> Dict[str, Any]:
    if event is None:
        return {}
    if isinstance(event, str):
        try:
            return cast(Dict[str, Any], json.loads(event))
        except Exception:
            return {}
    if isinstance(event, dict):
        return cast(Dict[str, Any], event)
    return {}


# ========== スクレイパーレジストリ ==========
def _load_registry():
    """
    各商品スクレイパーのクラスを遅延インポートしてレジストリ化。
    新しいスクレイパーモジュールを使用。
    """
    try:
        # 統一的な絶対インポートを使用
        from loanpedia_scraper.scrapers.aomori_michinoku_bank import product_scraper
        from loanpedia_scraper.scrapers.aomori_michinoku_bank import config
        scrape_product = product_scraper.scrape_product
        profiles = config.profiles
    except ImportError as e:
        logger.error(f"Failed to import scraper modules: {e}")
        # 詳細なエラー情報を追加
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"Current Python path: {sys.path[:5]}...")  # パスの最初の5つを表示
        raise
    
    # 商品プロファイルベースのスクレイパー生成
    class ProductScraper:
        def __init__(self, url: str, pdf_url_override: str = None):
            self.url = url
            self.pdf_url_override = pdf_url_override
            
        def scrape_loan_info(self) -> Dict[str, Any]:
            try:
                product, raw_data = scrape_product(
                    self.url, 
                    fin_id=FINANCIAL_INSTITUTION_ID, 
                    pdf_url_override=self.pdf_url_override
                )
                return {
                    "scraping_status": "success",
                    "product_name": product.product_name,
                    "loan_type": product.loan_type,
                    "category": product.category,
                    "min_interest_rate": product.min_interest_rate,
                    "max_interest_rate": product.max_interest_rate,
                    "interest_type": product.interest_type,
                    "min_loan_amount": product.min_loan_amount,
                    "max_loan_amount": product.max_loan_amount,
                    "min_loan_term": product.min_loan_term,
                    "max_loan_term": product.max_loan_term,
                    "min_loan_term_months": product.min_loan_term,  # 月単位（互換性のため保持）
                    "max_loan_term_months": product.max_loan_term,  # 月単位（互換性のため保持）
                    "repayment_method": product.repayment_method,
                    "min_age": product.min_age,
                    "max_age": product.max_age,
                    "special_features": product.special_features,
                    "source_reference": product.source_reference,
                    "raw_data": raw_data.model_dump() if raw_data else None,
                }
            except Exception as e:
                return {
                    "scraping_status": "error", 
                    "error": str(e)
                }
    
    # key: APIで指定するproduct、name: 表示名、cls: スクレイパークラス
    registry = {}
    
    # マイカーローン
    registry["mycar"] = {
        "name": "青森みちのくマイカーローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/mycarloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-75.pdf"
        ),
    }
    
    # 教育ローン（反復利用型）
    registry["education"] = {
        "name": "青森みちのく教育ローン反復利用型",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/kyouikuloan_hanpuku/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-77.pdf"
        ),
    }
    
    
    # フリーローン
    registry["freeloan"] = {
        "name": "青森みちのくフリーローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/freeloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-81.pdf"
        ),
    }
    
    # おまとめローン
    registry["omatomeloan"] = {
        "name": "青森みちのくおまとめローン",
        "cls": lambda: ProductScraper(
            "https://www.am-bk.co.jp/kojin/loan/omatomeloan/",
            "https://www.am-bk.co.jp/kojin/loan/pdf/l-83.pdf"
        ),
    }
    
    return registry


def get_available_products() -> List[str]:
    return list(_load_registry().keys())


def get_product_info() -> Dict[str, str]:
    reg = _load_registry()
    return {k: v["name"] for k, v in reg.items()}


# ========== 実行ロジック ==========
def _save_to_database(product_data: Dict[str, Any], raw_data_dict: Dict[str, Any]) -> bool:
    """
    スクレイピング結果をデータベースに保存
    
    Args:
        product_data: 商品データ辞書
        raw_data_dict: 生データ辞書
        
    Returns:
        bool: 保存成功時True、失敗時False
    """
    save_to_db = os.getenv("SAVE_TO_DB", "true").lower()
    if save_to_db not in ("true", "1", "yes"):
        logger.info("SAVE_TO_DB is disabled, skipping database save")
        return True
    
    # デバッグモード: データベース保存を無効にして、スクレイピングの成功を確認
    if os.getenv("DEBUG_SKIP_DB", "false").lower() in ("true", "1", "yes"):
        logger.info("DEBUG_SKIP_DB is enabled, skipping database save for debugging")
        return True
    
    try:
        # データベースモジュールをインポート
        # ハンドラーの位置: loanpedia_scraper/src/handlers/
        # データベースの位置: loanpedia_scraper/database/
        database_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database")
        if database_path not in sys.path:
            sys.path.insert(0, database_path)
        
        try:
            from loan_database import LoanDatabase
        except ImportError as e:
            logger.error(f"Failed to import LoanDatabase: {e}")
            # 詳細なエラー情報を追加
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.error(f"Database path: {database_path}")
            logger.error(f"Python path: {sys.path}")
            raise
        
        # データベース設定（環境変数から取得）
        db_config = {
            'host': os.getenv('DB_HOST', 'mysql'),
            'user': os.getenv('DB_USER', 'app_user'),
            'password': os.getenv('DB_PASSWORD', 'app_password'),
            'database': os.getenv('DB_NAME', 'app_db'),
            'port': int(os.getenv('DB_PORT', '3306')),  # Docker内のポート
            'charset': 'utf8mb4'
        }
        
        # データベース接続をリトライ付きで実行（指数バックオフ）
        for attempt in range(DB_RETRY_MAX):
            try:
                # 接続前に少し待機（リソース競合回避）
                if attempt > 0:
                    delay = DB_RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 指数バックオフ
                    logger.info(f"Waiting {delay} seconds before retry {attempt + 1}")
                    time.sleep(delay)
                
                db = LoanDatabase(db_config)
                if db.connect():
                    logger.info(f"Database connection successful on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"Database connection attempt {attempt + 1} failed (returned False)")
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed with exception: {e}")
                if attempt == DB_RETRY_MAX - 1:
                    logger.error("All database connection attempts failed")
                    return False
        else:
            logger.error(f"Failed to connect to database after {DB_RETRY_MAX} retries")
            return False
        
        # LoanDatabaseの期待する形式に統合
        loan_data = {
            'institution_code': 'aomori_michinoku',
            'institution_name': '青森みちのく銀行',
            'source_url': raw_data_dict.get('source_url', product_data.get('source_reference', '')),
            'html_content': raw_data_dict.get('html_content', ''),
            'extracted_text': raw_data_dict.get('extracted_text', ''),
            'content_hash': raw_data_dict.get('content_hash', ''),
            'scraping_status': 'success',
            'scraped_at': datetime.now().isoformat(),
            'product_name': product_data.get('product_name'),
            'loan_type': product_data.get('loan_type'),
            'category': product_data.get('category'),
            'min_interest_rate': product_data.get('min_interest_rate'),
            'max_interest_rate': product_data.get('max_interest_rate'),
            'interest_type': product_data.get('interest_type'),
            'min_loan_amount': product_data.get('min_loan_amount'),
            'max_loan_amount': product_data.get('max_loan_amount'),
            'min_loan_term': product_data.get('min_loan_term'),
            'max_loan_term': product_data.get('max_loan_term'),
            'repayment_method': product_data.get('repayment_method'),
            'min_age': product_data.get('min_age'),
            'max_age': product_data.get('max_age'),
            'special_features': product_data.get('special_features'),
        }
        
        # データベースに保存
        success = db.save_loan_data(loan_data)
        db.disconnect()
        
        if success:
            logger.info(f"Successfully saved {product_data.get('product_name')} to database")
            return True
        else:
            logger.error(f"Failed to save {product_data.get('product_name')} to database")
            return False
        
    except Exception as e:
        logger.exception(f"Database save error: {e}")
        return False


def _run_one(product_key: str, reg: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    単一スクレイパーを実行して結果を標準化。
    戻り値:
      {
        "product": "mycar",
        "product_name": "マイカーローン",
        "success": True/False,
        "result": {...} or None,
        "error": "..." or None
      }
    """
    info = reg[product_key]
    name = info["name"]
    cls = info["cls"]

    logger.info(f"▶ {name} のスクレイピング開始")
    try:
        scraper = cls()
        result = scraper.scrape_loan_info()
        if result and result.get("scraping_status") == "success":
            logger.info(f"✅ {name} のスクレイピング成功")
            
            # データベースに保存
            raw_data = result.get("raw_data", {})
            db_saved = _save_to_database(result, raw_data)
            
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
        if key not in reg:
            results.append(
                {
                    "product": key,
                    "product_name": "(unknown)",
                    "success": False,
                    "result": None,
                    "error": f"Unknown product: {key}",
                }
            )
            ng += 1
            continue
        r = _run_one(key, reg)
        results.append(r)
        if r["success"]:
            ok += 1
        else:
            ng += 1
        # 過負荷防止とデータベース負荷軽減
        time.sleep(SCRAPE_SLEEP_SEC)
    return results, ok, ng


def _parse_targets(evt: Dict[str, Any]) -> List[str]:
    """
    event の "product" 指定を解釈:
      - "all"（既定）: 全商品
      - "mycar" のような文字列
      - ["mycar","education"] のような配列
    """
    reg_keys = get_available_products()
    p = evt.get("product", "all")

    if isinstance(p, list):
        return p or reg_keys
    if isinstance(p, str):
        if p == "all":
            return reg_keys
        return [p]
    # 型不正時は全件
    return reg_keys


# ========== メイン・ディスパッチ ==========
def _dispatch(evt: Dict[str, Any]) -> Dict[str, Any]:
    """
    入力イベントの多形を吸収し、共通処理へディスパッチ。
    - API Gateway (Lambda Proxy): {"httpMethod": "...", "body": "..."} に対応
    - SQS: {"Records":[{"body":"...json..."}]} に対応（バッチ処理は簡略）
    - 直叩き/StepFunctions/EventBridge: そのままJSON
    """
    # SQS（バッチ）は各レコードの body を再帰処理（ここでは簡略化しfailuresなしで返す）
    if "Records" in evt and isinstance(evt["Records"], list):
        for rec in evt["Records"]:
            try:
                body = json.loads(rec.get("body") or "{}")
                _dispatch(body)
            except Exception:
                logger.exception("SQS record handling error")
        return {"batchItemFailures": []}

    # API Gateway（Lambda Proxy統合）
    if "httpMethod" in evt and "body" in evt:
        try:
            body = json.loads(evt.get("body") or "{}")
        except Exception:
            body = {}
        return _dispatch(body)

    # 直叩き/汎用
    targets = _parse_targets(evt)
    all_keys = set(get_available_products())
    invalid = [k for k in targets if k not in all_keys]
    if invalid:
        return _err(
            400,
            "InvalidProduct",
            f"無効な商品指定: {invalid}",
            available_products=sorted(all_keys),
        )

    results, ok, ng = _run_many(targets)
    overall_success = ok > 0 and ng == 0
    status = 200 if overall_success else (207 if ok > 0 else 500)

    summary = {
        "total_products": len(targets),
        "success_count": ok,
        "error_count": ng,
    }
    body = {
        "success": overall_success,
        "message": f"統合スクレイピング完了: 成功{ok}件、失敗{ng}件",
        "institution": INSTITUTION_KEY,
        "target_products": targets,
        "summary": summary,
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }
    return _resp(status, body)


# ========== Lambdaエントリポイント ==========
def lambda_handler(event, context):
    logger.info("青森みちのく銀行 統合スクレイピング開始")
    logger.info(f"Event(raw): {event!r}")
    try:
        return _dispatch(_to_event_dict(event))
    except ImportError as e:
        logger.exception("ImportError")
        return _err(500, "ImportError", str(e))
    except Exception as e:
        logger.exception("Unhandled exception")
        return _err(500, "UnexpectedError", str(e))


# ========== ローカル実行（python handlers_aomori_michinoku.py --product ...） ==========
def main():
    import argparse

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="青森みちのく銀行 統合スクレイピング（ローカル）"
    )
    parser.add_argument(
        "--product",
        default="all",
        help="対象商品。'all' / 'mycar' / 'education' / 'freeloan' / 'omatomeloan' またはカンマ区切り",
    )
    args = parser.parse_args()

    # 配列にも対応（mycar,education のような指定）
    if "," in args.product:
        products = [p.strip() for p in args.product.split(",") if p.strip()]
        evt = {"product": products}
    else:
        evt = {"product": args.product}

    resp = lambda_handler(evt, None)

    print("=" * 60)
    print("ステータス:", resp["statusCode"])
    body = json.loads(resp["body"])  # Lambda Proxyではbodyは文字列
    print("成功:", body["success"])
    print("メッセージ:", body["message"])
    print("サマリー:", body["summary"])
    for item in body["results"]:
        print(f"\n商品: {item['product']}")
        if item["success"]:
            data = item["result"] or {}
            print("  ✅ 成功")
            print(f"  DB保存: {'✅' if item.get('db_saved') else '❌'}")
            print("  商品名:", data.get("product_name"))
            print(
                "  金利:",
                data.get("min_interest_rate"),
                "-",
                data.get("max_interest_rate"),
            )
            print(
                "  融資額:",
                data.get("min_loan_amount"),
                "-",
                data.get("max_loan_amount"),
            )
            print(
                "  期間(月):",
                data.get("min_loan_term_months"),
                "-",
                data.get("max_loan_term_months"),
            )
            print("  年齢:", data.get("min_age"), "-", data.get("max_age"))
        else:
            print("  ❌ 失敗:", item["error"])


if __name__ == "__main__":
    main()
