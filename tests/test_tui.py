# tests/test_tui.py
import pytest
from tui.app import DashboardApp

@pytest.mark.asyncio
async def test_app_starts_without_error():
    app = DashboardApp()
    async with app.run_test() as pilot:
        assert pilot.app.is_running
        await pilot.pause()
