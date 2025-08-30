"""
青森みちのく銀行 統合Lambdaハンドラー（極薄）
サービス層へ委譲し、イベント入出力のみ担当。
"""

import logging
from typing import Any

from src.services.aomori_michinoku_service import run

logger = logging.getLogger(__name__)


def lambda_handler(event: Any, context: Any):
    logger.info("青森みちのく銀行 統合スクレイピング開始")
    logger.info(f"Event(raw): {event!r}")
    return run(event)
