"""Configuration for Aoimori Shinkin scraper (skeleton)."""
from typing import Dict, Any

BASE = "https://example.com"
START = ""
PDF_CATALOG_URL = ""
HEADERS: Dict[str, str] = {"User-Agent": "LoanScraper/1.0"}

# Product-specific profiles placeholder
profiles: Dict[str, Dict[str, Any]] = {}

def pick_profile(url: str) -> Dict[str, Any]:
    return {}

