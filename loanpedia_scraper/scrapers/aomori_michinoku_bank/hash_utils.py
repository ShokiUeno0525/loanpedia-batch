# loan_scraper/hash_utils.py
# -*- coding: utf-8 -*-
import hashlib


def sha_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()
