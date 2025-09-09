"""青い森信用金庫向けのHTTPクライアント

共通ヘッダーを維持するための requests.Session の薄いラッパー。
将来的なプロキシ/リトライ対応を見据えた構成。
"""
from __future__ import annotations

from typing import Optional, Dict
import requests


def build_session(extra_headers: Optional[Dict[str, str]] = None) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36 LoanpediaBot/1.0"
            )
        }
    )
    if extra_headers:
        s.headers.update(extra_headers)
    return s


def get(session: requests.Session, url: str, timeout: int = 15) -> requests.Response:
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp
