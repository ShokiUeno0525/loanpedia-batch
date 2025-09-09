#!/usr/bin/env python3
"""
青い森信用金庫スクレイパー 実行スクリプト

用途:
- 実URLを指定してスクレイピング（HTML）
- PDF抽出の有効化/URL指定（環境変数で制御）
- DB保存の有効化（save_to_db）

例:
  # 実URLを1件指定して保存
  python scripts/run_aoimori_shinkin.py --save-to-db --urls https://example.com/product

  # 複数URL + PDF抽出 + OCR有効化
  python scripts/run_aoimori_shinkin.py --save-to-db \
    --urls https://example.com/a https://example.com/b \
    --enable-pdf --pdf-urls https://example.com/rates.pdf \
    --enable-ocr --tess-lang jpn

  # 事前に AOIMORI_SHINKIN_PRODUCT_URLS へ JSON を入れて一括実行
  set "AOIMORI_SHINKIN_PRODUCT_URLS=[{\"url\":\"https://example.com/a\"},{\"url\":\"https://example.com/b\"}]"
  python scripts/run_aoimori_shinkin.py --save-to-db --use-env-products --enable-pdf
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from typing import Any, Dict, List, Optional

# リポジトリ直下をパスに追加
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def configure_pdf(args: argparse.Namespace) -> None:
    if args.enable_pdf:
        os.environ["AOIMORI_SHINKIN_ENABLE_PDF"] = "true"
    if args.pdf_urls:
        os.environ["AOIMORI_SHINKIN_PDF_URLS"] = json.dumps(args.pdf_urls, ensure_ascii=False)
    if args.enable_ocr:
        # OCRは重量級のため明示フラグ
        os.environ["AOIMORI_SHINKIN_ENABLE_OCR"] = "true"
    if args.tess_cmd:
        os.environ["TESSERACT_CMD"] = args.tess_cmd
    if args.tess_lang:
        os.environ["TESS_LANG"] = args.tess_lang


def load_urls_from_env() -> List[str]:
    data = os.getenv("AOIMORI_SHINKIN_PRODUCT_URLS")
    if not data:
        return []
    try:
        parsed = json.loads(data)
        if isinstance(parsed, list):
            return [str(x.get("url")) for x in parsed if isinstance(x, dict) and x.get("url")]
    except Exception:
        return []
    return []


def run() -> int:
    from loanpedia_scraper.scrapers.aoimori_shinkin.product_scraper import AoimoriShinkinScraper

    parser = argparse.ArgumentParser(description="青い森信用金庫スクレイパー 実行")
    parser.add_argument("--save-to-db", action="store_true", help="DB保存を有効化")
    parser.add_argument("--urls", nargs="*", default=[], help="スクレイピング対象URL（スペース区切りで複数可）")
    parser.add_argument("--use-env-products", action="store_true", help="AOIMORI_SHINKIN_PRODUCT_URLS からURL一覧を取得")
    parser.add_argument("--enable-pdf", action="store_true", help="PDF抽出を有効化")
    parser.add_argument("--pdf-urls", nargs="*", default=[], help="PDF URL（複数可、環境変数に反映）")
    parser.add_argument("--enable-ocr", action="store_true", help="OCRフォールバックを有効化（必要時のみ）")
    parser.add_argument("--tess-cmd", type=str, default=None, help="tesseract 実行パス（任意）")
    parser.add_argument("--tess-lang", type=str, default=None, help="OCR言語（例:jpn）")

    args = parser.parse_args()

    # PDF関連の環境設定
    configure_pdf(args)

    targets: List[str] = list(args.urls)
    if args.use_env_products:
        targets.extend(load_urls_from_env())

    # URLがなければ START/製品リストの自動探索に任せる
    scraper = AoimoriShinkinScraper(save_to_db=args.save_to_db)

    all_results: List[Dict[str, Any]] = []
    if targets:
        for u in targets:
            print(f"\n>>> Scraping: {u}")
            res = scraper.scrape_loan_info(url=u)
            all_results.append(res)
    else:
        print("\n>>> Scraping with configured product list or START (URL未指定)")
        res = scraper.scrape_loan_info()
        all_results.append(res)

    # 出力整理
    print("\n=== Summary ===")
    for i, r in enumerate(all_results, 1):
        products = r.get("products") or []
        db_ids = r.get("db_saved_ids") or []
        status = r.get("scraping_status") or r.get("status")
        print(f"[{i}] status={status} products={len(products)} db_saved_ids={db_ids}")
        if products:
            # 最初の1件だけ簡易表示
            p0 = products[0]
            name = p0.get("product_name")
            rmin = p0.get("min_interest_rate")
            rmax = p0.get("max_interest_rate")
            print(f"    product[0]: name={name} rate={rmin}~{rmax}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

