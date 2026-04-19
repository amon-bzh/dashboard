# tests/test_tui.py
import pytest
from tui.app import DashboardApp

@pytest.mark.asyncio
async def test_app_starts_without_error():
    app = DashboardApp()
    async with app.run_test() as pilot:
        assert pilot.app.is_running
        await pilot.pause()


@pytest.mark.asyncio
async def test_currency_widget_mounts(tmp_path, monkeypatch):
    import shared.paths as p
    p.CACHE_DIR = tmp_path
    p.CONFIG_FILE = tmp_path / "config.json"
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig(widgets=[]))
    from tui.widgets.currency_widget import CurrencyWidget
    from textual.containers import Grid
    app = DashboardApp()
    async with app.run_test() as pilot:
        widget = CurrencyWidget("EUR/USD", "1M")
        await pilot.app.query_one("#grid", Grid).mount(widget)
        await pilot.pause()
        assert pilot.app.query_one(CurrencyWidget)
