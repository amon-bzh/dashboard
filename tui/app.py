from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Grid
from textual.widgets import TabbedContent, TabPane

from shared.config import load_config
from logs.logger import get_logger

logger = get_logger("tui")


class DashboardApp(App):
    CSS = """
    Screen {
        background: #1a1a2e;
    }
    #grid {
        layout: grid;
        grid-gutter: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                with ScrollableContainer():
                    yield Grid(id="grid")
            with TabPane("Configuration", id="tab-config"):
                from tui.screens.config_screen import ConfigScreen
                yield ConfigScreen()

    def on_mount(self) -> None:
        self._load_widgets()
        self.set_interval(5, self._poll_cache)
        logger.info("TUI démarré")

    def _load_widgets(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        config = load_config()
        grid = self.query_one("#grid", Grid)
        grid.styles.grid_size_columns = config.grid_columns
        grid.styles.grid_columns = " ".join(["1fr"] * config.grid_columns)
        for w in config.widgets:
            grid.mount(CurrencyWidget(w.pair, w.scale))
        logger.debug(f"{len(config.widgets)} widgets chargés")

    async def _poll_cache(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        for widget in self.query(CurrencyWidget):
            widget.refresh_if_updated()
