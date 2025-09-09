#!/usr/bin/env python3
"""
Aoimori Shinkin のDB保存動作確認スクリプト

実ネットワークに依存せず、HTTP取得をモックしてHTMLを供給し、
スクレイパーの save_to_db=True で raw_loan_data への保存可否を検証する。

実行前準備（必要に応じて環境変数を設定）:
  - DB_HOST / DB_USER / DB_PASSWORD / DB_NAME / DB_PORT

実行:
  python scripts/db_save_check_aoimori_shinkin.py
"""
from __future__ import annotations

import os
import sys
import json
from typing import Any, Dict, List

# リポジトリ直下をパスに追加（scripts/ から実行してもパッケージを解決できるように）
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def main() -> None:
    # 過度なエラー短絡を避けつつ、状態を見やすく出力
    from loanpedia_scraper.scrapers.aoimori_shinkin import product_scraper as mod
    from loanpedia_scraper.database.loan_database import (
        LoanDatabase,
        get_database_config,
    )

    # テスト用の簡易HTML（商品名/金利/融資額/期間/年齢を含む）
    html = (
        "<html><head><title>マイカーローン | 青い森信用金庫</title></head>"
        "<body><h1>マイカーローン</h1>"
        "<div>金利：年2.5%～3.5%</div>"
        "<div>融資金額：10万円～1,000万円</div>"
        "<div>融資期間：6ヶ月～10年</div>"
        "<div>年齢：満20歳以上満65歳未満</div>"
        "</body></html>"
    )

    class DummyResp:
        def __init__(self, text: str, url: str):
            self.text = text
            self.content = text.encode("utf-8")
            self.url = url
            self.status_code = 200

    target_url = "https://example.com/aoimori-test"

    # http_client.get をモック
    orig_get = mod.http_client.get
    mod.http_client.get = lambda session, url, timeout=15: DummyResp(html, target_url)

    try:
        scraper = mod.AoimoriShinkinScraper(save_to_db=True)
        result: Dict[str, Any] = scraper.scrape_loan_info(url=target_url)

        print("=== Scraper Result ===")
        print(json.dumps({k: v for k, v in result.items() if k != "products"}, ensure_ascii=False, indent=2))
        if result.get("products"):
            print(f"products count: {len(result['products'])}")

        saved_ids: List[int] = result.get("db_saved_ids") or []
        if not saved_ids:
            print("[NG] db_saved_ids が空です（保存されていない可能性）")
        else:
            print(f"[OK] 保存ID: {saved_ids}")

        # 直近の保存行を確認
        cfg = get_database_config()
        with LoanDatabase(cfg) as db:
            if not db:
                print("[NG] DB接続に失敗しました")
                return
            cur = db.cursor  # type: ignore
            cur.execute(
                "SELECT id, institution_id, source_url, page_title, scraped_at FROM raw_loan_data WHERE id=%s",
                (saved_ids[0] if saved_ids else -1,),
            )
            row = cur.fetchone()
            if row:
                print("=== Inserted Row (raw_loan_data) ===")
                print(json.dumps(row, ensure_ascii=False, default=str, indent=2))
            else:
                print("[WARN] 指定IDの行が見つかりませんでした。保存がロールバックされた可能性があります。")

    finally:
        # モック解除
        mod.http_client.get = orig_get


if __name__ == "__main__":
    main()
