#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全スクレイパーのDB保存状況確認スクリプト

各金融機関のraw_loan_dataテーブルへの保存状況を確認する
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# リポジトリ直下をパスに追加
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def check_database_connection() -> bool:
    """データベース接続をチェック"""
    try:
        from loanpedia_scraper.database.db_factory import get_database_adapter

        db = get_database_adapter()
        print(f"✅ データベース接続成功: {type(db).__name__}")
        return True
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return False


def get_recent_data_count(institution_code: str, days: int = 7) -> Optional[Dict[str, Any]]:
    """指定金融機関の最近のデータ件数を取得"""
    try:
        from loanpedia_scraper.database.db_factory import get_database_adapter

        db_adapter = get_database_adapter()
        with LoanDatabase(cfg) as db:
            if not db or not db.cursor:
                return None

            cur = db.cursor

            # 最近N日間のデータ件数
            cutoff_date = datetime.now() - timedelta(days=days)
            cur.execute(
                """
                SELECT COUNT(*) as count,
                       MAX(scraped_at) as latest_scrape,
                       MIN(scraped_at) as earliest_scrape
                FROM raw_loan_data
                WHERE institution_id = %s
                  AND scraped_at >= %s
                """,
                (institution_code, cutoff_date)
            )
            recent = cur.fetchone()

            # 全期間のデータ件数
            cur.execute(
                """
                SELECT COUNT(*) as total_count,
                       MAX(scraped_at) as latest_scrape
                FROM raw_loan_data
                WHERE institution_id = %s
                """,
                (institution_code,)
            )
            total = cur.fetchone()

            return {
                'recent_count': recent['count'] if recent else 0,
                'recent_latest': recent['latest_scrape'] if recent else None,
                'recent_earliest': recent['earliest_scrape'] if recent else None,
                'total_count': total['total_count'] if total else 0,
                'total_latest': total['latest_scrape'] if total else None,
            }

    except Exception as e:
        print(f"  エラー: {e}")
        return None


def get_sample_data(institution_code: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
    """指定金融機関の最新データサンプルを取得"""
    try:
        from loanpedia_scraper.database.loan_database import LoanDatabase, get_database_config

        # db_adapterを直接使用（LoanDatabaseまたはRDSDataAPIAdapter）
        if not hasattr(db_adapter, 'cursor'):
            # Data APIの場合は直接クエリ実行
            return None

        if hasattr(db_adapter, '__enter__'):
            # コンテキストマネージャーを使用
            with db_adapter as db:
                if not db or not db.cursor:
                    return None
                cur = db.cursor
        else:
            # コンテキストマネージャーがない場合
            cur = db_adapter.cursor
            cur.execute(
                """
                SELECT id, source_url, page_title, scraped_at
                FROM raw_loan_data
                WHERE institution_id = %s
                ORDER BY scraped_at DESC
                LIMIT %s
                """,
                (institution_code, limit)
            )
            rows = cur.fetchall()
            return rows if rows else []

    except Exception as e:
        print(f"  エラー: {e}")
        return None


def main():
    """メイン処理"""
    print("=" * 70)
    print("全スクレイパーのDB保存状況確認")
    print("=" * 70)
    print()

    # DB接続確認
    if not check_database_connection():
        print("\nデータベースに接続できませんでした。")
        print("環境変数を確認してください：")
        print("  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        print("  または USE_DATA_API=true の場合：")
        print("  - RDS_CLUSTER_ARN, RDS_SECRET_ARN, DB_NAME")
        return

    print()

    # 各金融機関のデータ確認
    institutions = [
        ("1250", "青い森信用金庫"),
        ("0117", "青森みちのく銀行"),
        ("1251", "東奥信用金庫"),
        ("2260", "青森県信用組合"),
    ]

    for code, name in institutions:
        print(f"\n{'=' * 70}")
        print(f"📊 {name} (機関コード: {code})")
        print('=' * 70)

        # 最近7日間のデータ
        stats = get_recent_data_count(code, days=7)
        if stats:
            print(f"  最近7日間のデータ件数: {stats['recent_count']}件")
            if stats['recent_latest']:
                print(f"  最新スクレイピング日時: {stats['recent_latest']}")
            if stats['recent_earliest']:
                print(f"  最古スクレイピング日時: {stats['recent_earliest']}")
            print(f"  全期間のデータ件数: {stats['total_count']}件")
            if stats['total_latest']:
                print(f"  全期間の最新日時: {stats['total_latest']}")
        else:
            print("  ⚠️ データ取得に失敗しました")

        # サンプルデータ表示
        print(f"\n  最新データサンプル（最大3件）:")
        samples = get_sample_data(code, limit=3)
        if samples:
            for i, sample in enumerate(samples, 1):
                print(f"\n    [{i}] ID: {sample['id']}")
                print(f"        URL: {sample['source_url']}")
                print(f"        タイトル: {sample['page_title']}")
                print(f"        スクレイピング日時: {sample['scraped_at']}")
        else:
            print("    データなし")

    print(f"\n{'=' * 70}")
    print("確認完了")
    print('=' * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n処理が中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
