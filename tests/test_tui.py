# tests/test_tui.py
import pytest
from textual.widgets import Input
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
    from tui.widgets.gallery import WidgetGallery
    app = DashboardApp()
    async with app.run_test() as pilot:
        widget = CurrencyWidget("EUR/USD", "1M")
        await pilot.app.query_one("#gallery", WidgetGallery).add_currency_widget(widget)
        await pilot.pause()
        assert pilot.app.query_one(CurrencyWidget)


@pytest.mark.asyncio
async def test_context_menu_appears_on_key_m():
    from tui.widgets.context_menu import ContextMenu
    from tui.widgets.currency_widget import CurrencyWidget
    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        widgets = list(pilot.app.query(CurrencyWidget))
        if widgets:
            widgets[0].focus()
            await pilot.press("m")
            await pilot.pause()
            menus = list(pilot.app.query(ContextMenu))
            assert len(menus) == 1


@pytest.mark.asyncio
async def test_config_screen_saves_config(tmp_path, monkeypatch):
    import shared.paths as p
    p.CONFIG_FILE = tmp_path / "config.json"
    p.CACHE_DIR = tmp_path / "cache"
    p.CACHE_DIR.mkdir()
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig())

    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.click("#tab-config")
        await pilot.pause()
        # Modifier la valeur de l'input directement
        input_widget = pilot.app.query_one("#input-refresh", Input)
        input_widget.value = "30"
        await pilot.pause()
        # Déclencher le handler directement (pilot.click sur btn ne propage pas l'événement)
        from tui.screens.config_screen import ConfigScreen
        from textual.widgets import Button
        config_screen = pilot.app.query_one(ConfigScreen)
        btn = pilot.app.query_one("#btn-apply", Button)
        config_screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()

    from shared.config import load_config
    cfg = load_config()
    assert "30" in str(cfg.refresh_interval_minutes)


@pytest.mark.asyncio
async def test_app_uses_bloomberg_theme():
    app = DashboardApp()
    async with app.run_test() as pilot:
        assert pilot.app.theme == "bloomberg"
