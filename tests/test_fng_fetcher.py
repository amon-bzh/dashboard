import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_fetch_fng_returns_structured_dict():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"value": "72", "value_classification": "Greed",   "timestamp": "1714953600"},
            {"value": "68", "value_classification": "Greed",   "timestamp": "1714867200"},
            {"value": "55", "value_classification": "Neutral", "timestamp": "1714780800"},
        ]
    }
    with patch("daemon.fng_fetcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        from daemon.fng_fetcher import fetch_fng
        result = await fetch_fng()

    assert result["current"] == 72
    assert result["classification"] == "Greed"
    assert isinstance(result["history"], dict)
    assert len(result["history"]) == 3


@pytest.mark.asyncio
async def test_fetch_fng_raises_on_http_error():
    with patch("daemon.fng_fetcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
        mock_cls.return_value = mock_client

        from daemon.fng_fetcher import fetch_fng
        with pytest.raises(Exception, match="connection refused"):
            await fetch_fng()
