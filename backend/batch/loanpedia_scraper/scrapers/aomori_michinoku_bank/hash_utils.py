# loan_scraper/hash_utils.py
# -*- coding: utf-8 -*-
import hashlib


def sha_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aomori_michinoku_bank/hash_utils.py
# コンテンツハッシュ/重複判定ユーティリティ
# なぜ: 同一内容の再保存や再処理を避けるため
# 関連: product_scraper.py, ../../database/loan_database.py, ../../schemas.py
