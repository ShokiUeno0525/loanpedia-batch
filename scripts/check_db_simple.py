#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなDB保存状況確認スクリプト
"""

import os
import sys
from datetime import datetime, timedelta

# リポジトリ直下をパスに追加
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def main():
    print("=" * 70)
    print("DB保存状況確認")
    print("=" * 70)
    print()

    try:
        from loanpedia_scraper.database.loan_database import LoanDatabase, get_database_config

        cfg = get_database_config()
        print(f"✅ データベース設定取得成功")
        print(f"   Host: {cfg.get('host', 'N/A')}")
        print(f"   Database: {cfg.get('database', 'N/A')}")
        print()

        with LoanDatabase(cfg) as db:
            if not db or not db.cursor:
                print("❌ データベース接続失敗")
                return

            cur = db.cursor
            print("✅ データベース接続成功")
            print()

            # 各金融機関のデータ確認
            institutions = [
                ("1250", "青い森信用金庫"),
                ("0117", "青森みちのく銀行"),
                ("1251", "東奥信用金庫"),
                ("2260", "青森県信用組合"),
            ]

            for code, name in institutions:
                print(f"{'=' * 70}")
                print(f"📊 {name} (機関コード: {code})")
                print('=' * 70)

                # 全期間のデータ件数
                cur.execute(
                    """
                    SELECT COUNT(*) as total_count,
                           MAX(scraped_at) as latest_scrape,
                           MIN(scraped_at) as earliest_scrape
                    FROM raw_loan_data
                    WHERE institution_id = %s
                    """,
                    (code,)
                )
                result = cur.fetchone()

                if result:
                    total_count = result['total_count'] if isinstance(result, dict) else result[0]
                    latest = result['latest_scrape'] if isinstance(result, dict) else (result[1] if len(result) > 1 else None)
                    earliest = result['earliest_scrape'] if isinstance(result, dict) else (result[2] if len(result) > 2 else None)

                    print(f"  全期間のデータ件数: {total_count}件")
                    if latest:
                        print(f"  最新スクレイピング日時: {latest}")
                    if earliest:
                        print(f"  最古スクレイピング日時: {earliest}")
                else:
                    print("  データなし")

                # 最新3件のサンプル
                cur.execute(
                    """
                    SELECT id, source_url, page_title, scraped_at
                    FROM raw_loan_data
                    WHERE institution_id = %s
                    ORDER BY scraped_at DESC
                    LIMIT 3
                    """,
                    (code,)
                )
                samples = cur.fetchall()

                if samples:
                    print(f"\n  最新データサンプル（最大3件）:")
                    for i, sample in enumerate(samples, 1):
                        if isinstance(sample, dict):
                            print(f"\n    [{i}] ID: {sample['id']}")
                            print(f"        URL: {sample['source_url']}")
                            print(f"        タイトル: {sample.get('page_title', 'N/A')}")
                            print(f"        日時: {sample['scraped_at']}")
                        else:
                            print(f"\n    [{i}] ID: {sample[0]}")
                            print(f"        URL: {sample[1]}")
                            print(f"        タイトル: {sample[2] if len(sample) > 2 else 'N/A'}")
                            print(f"        日時: {sample[3] if len(sample) > 3 else 'N/A'}")
                else:
                    print("\n  最新データサンプル: なし")

                print()

            print("=" * 70)
            print("確認完了")
            print("=" * 70)

    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        print("\n環境変数を確認してください:")
        print("  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n処理が中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        sys.exit(1)
