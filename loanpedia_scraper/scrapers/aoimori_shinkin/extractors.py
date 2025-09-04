"""Common extractors and text utilities for Aoimori Shinkin."""
from __future__ import annotations

import re
import unicodedata
from typing import Optional


def z2h(s: Optional[str]) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip()


def clean_rate_cell(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    t = z2h(s).replace("％", "%")
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%?", t)
    return float(m.group(1)) if m else None
