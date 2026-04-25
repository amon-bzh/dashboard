from __future__ import annotations

import asyncio
from typing import Dict

import yfinance as yf

SCALES: Dict[str, dict] = {
    "1M": {"period": "1mo", "interval": "1d"},
    "3M": {"period": "3mo", "interval": "1d"},
    "6M": {"period": "6mo", "interval": "1d"},
    "1A": {"period": "1y",  "interval": "1d"},
}


async def fetch_vix(scale: str) -> Dict[str, float]:
    """Retourne {date_iso: close} pour le VIX via Yahoo Finance."""
    if scale not in SCALES:
        raise ValueError(f"Échelle non supportée : {scale}. Valides : {list(SCALES)}")
    return await asyncio.to_thread(_fetch_vix_sync, scale)


def _fetch_vix_sync(scale: str) -> Dict[str, float]:
    params = SCALES[scale]
    df = yf.Ticker("^VIX").history(**params)
    if df.empty:
        raise ValueError(f"Aucune donnée VIX pour l'échelle {scale}")
    return {str(idx.date()): float(row["Close"]) for idx, row in df.iterrows()}
