from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Grid, Vertical
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
        from textual.widgets import Button
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                with Vertical():
                    with ScrollableContainer():
                        yield Grid(id="grid")
                    yield Button("[+] Ajouter une paire", id="btn-add", variant="default")
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

    def on_button_pressed(self, event) -> None:
        from textual.widgets import Button
        if not isinstance(event.button, Button) or event.button.id != "btn-add":
            return
        from tui.widgets.currency_widget import CurrencyWidget, _EditPairModal
        from textual.containers import Grid

        async def _handle(result) -> None:
            if result:
                new_pair, new_scale = result
                widget = CurrencyWidget(new_pair, new_scale)
                await self.query_one("#grid", Grid).mount(widget)
                from shared.config import load_config, save_config, WidgetConfig
                config = load_config()
                config.widgets.append(WidgetConfig(new_pair, new_scale))
                save_config(config)
                from shared.config import notify_daemon
                notify_daemon()

        self.push_screen(_EditPairModal("EUR/USD", "1M"), _handle)
