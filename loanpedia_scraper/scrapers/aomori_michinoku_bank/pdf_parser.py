# loan_scraper/pdf_parser.py
# -*- coding: utf-8 -*-
from typing import Dict
import io
import pdfplumber
from .extractors import extract_age, to_month_range


def pdf_bytes_to_text(b: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(b)) as pdf:
        for p in pdf.pages:
            pages.append(p.extract_text() or "")
    return "\n".join(pages)


def extract_pdf_fields(pdf_text: str) -> Dict:
    if not pdf_text:
        return {}
    agemin, agemax = extract_age(pdf_text)
    tmin, tmax = to_month_range(pdf_text)
    return {
        "min_age": agemin,
        "max_age": agemax,
        "min_loan_term": tmin,
        "max_loan_term": tmax,
    }
