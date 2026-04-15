import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from daemon.fetcher import fetch_rates, fetch_current_rate, SCALES


def test_scales_has_six_entries():
    assert set(SCALES.keys()) == {"1M", "3M", "6M", "1A", "2A", "5A"}


@pytest.mark.asyncio
async def test_fetch_rates_returns_date_rate_dict():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "base": "EUR",
        "rates": {
            "2025-01-02": {"USD": 1.05},
            "2025-01-03": {"USD": 1.06},
        }
    }
    with patch("daemon.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await fetch_rates("EUR/USD", "1M")

    assert result == {"2025-01-02": 1.05, "2025-01-03": 1.06}


@pytest.mark.asyncio
async def test_fetch_current_rate_returns_float():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"rates": {"USD": 1.0842}}
    with patch("daemon.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await fetch_current_rate("EUR/USD")

    assert result == 1.0842
