#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青森県信用組合スクレイパー実行スクリプト
"""

import sys
import logging
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'loanpedia_scraper'))

from scrapers.aomori_shinkumi.handler import AomoriShinkumiHandler

def main():
    """メイン実行関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("青森県信用組合ローン情報スクレイピング実行")
    print("=" * 60)

    try:
        handler = AomoriShinkumiHandler()
        handler.cli_handler(sys.argv[1:])

    except KeyboardInterrupt:
        print("\n処理が中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()