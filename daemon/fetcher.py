from __future__ import annotations
from datetime import date
from typing import Dict

import httpx
from dateutil.relativedelta import relativedelta

BASE_URL = "https://api.frankfurter.app"

SCALES: Dict[str, relativedelta] = {
    "1M": relativedelta(months=1),
    "3M": relativedelta(months=3),
    "6M": relativedelta(months=6),
    "1A": relativedelta(years=1),
    "2A": relativedelta(years=2),
    "5A": relativedelta(years=5),
}


async def fetch_rates(pair: str, scale: str) -> Dict[str, float]:
    """Retourne {date_iso: taux} pour la paire et l'échelle données."""
    base, quote = pair.split("/")
    end_date = date.today()
    start_date = end_date - SCALES[scale]

    url = f"{BASE_URL}/{start_date}..{end_date}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"from": base, "to": quote})
        response.raise_for_status()
        data = response.json()
    return {d: rates[quote] for d, rates in data["rates"].items()}


async def fetch_current_rate(pair: str) -> float:
    """Retourne le taux le plus récent pour la paire."""
    base, quote = pair.split("/")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{BASE_URL}/latest", params={"from": base, "to": quote}
        )
        response.raise_for_status()
        return float(response.json()["rates"][quote])
