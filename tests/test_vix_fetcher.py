import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


@pytest.mark.asyncio
async def test_fetch_vix_returns_date_close_dict():
    df = pd.DataFrame(
        {"Close": [20.5, 21.0, 19.8]},
        index=pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06"])
    )
    df.index = pd.DatetimeIndex(df.index, tz="UTC")

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df

    with patch("daemon.vix_fetcher.yf.Ticker", return_value=mock_ticker):
        from daemon.vix_fetcher import fetch_vix
        result = await fetch_vix("1M")

    assert "2025-01-02" in result
    assert result["2025-01-02"] == pytest.approx(20.5)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_fetch_vix_raises_on_empty_dataframe():
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("daemon.vix_fetcher.yf.Ticker", return_value=mock_ticker):
        from daemon.vix_fetcher import fetch_vix
        with pytest.raises(ValueError, match="Aucune donnée VIX"):
            await fetch_vix("1M")


def test_vix_scales_keys():
    from daemon.vix_fetcher import SCALES
    assert set(SCALES.keys()) == {"1M", "3M", "6M", "1A"}
