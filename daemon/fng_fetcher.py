from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import httpx

from logs.logger import get_logger

logger = get_logger("daemon")

FNG_URL = "https://api.alternative.me/fng/"


async def fetch_fng(limit: int = 31) -> Dict[str, Any]:
    """Retourne {"current": int, "classification": str, "history": {date_iso: value}}.

    Source : alternative.me Crypto Fear & Greed Index (gratuit, sans clé API).
    Les données sont ordonnées du plus récent au plus ancien.
    """
    logger.debug(f"[F&G] fetch limit={limit}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(FNG_URL, params={"limit": limit, "format": "json"})
        resp.raise_for_status()
        data = resp.json()["data"]

    history = {}
    for entry in data:
        ts = int(entry["timestamp"])
        d = str(datetime.fromtimestamp(ts).date())
        history[d] = int(entry["value"])

    newest = data[0]
    result = {
        "current": int(newest["value"]),
        "classification": newest["value_classification"],
        "history": history,
    }
    logger.debug(f"[F&G] {len(history)} points, current={result['current']} ({result['classification']})")
    return result
