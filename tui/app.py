from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Label, TabbedContent, TabPane

from shared.config import load_config
from logs.logger import get_logger

logger = get_logger("tui")


class DashboardApp(App):
    BINDINGS = [
        ("q", "quit", "Quitter"),
    ]

    def __init__(self, widget_height: int = 22, **kwargs) -> None:
        super().__init__(**kwargs)
        self._widget_height = widget_height
        logger.debug(f"DashboardApp widget_height={widget_height}")

    CSS = """
    Screen {
        layers: base overlay;
        color: #c9bfa8;
    }
    #bottom-bar {
        height: auto;
        padding: 0 1;
    }
    #btn-fetch {
        margin-left: 1;
    }
    #fetch-status {
        color: #00b4d8;
        height: 1;
        content-align: center middle;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                with Vertical():
                    from tui.widgets.gallery import WidgetGallery
                    yield WidgetGallery(self._widget_height, id="gallery")
                    with Horizontal(id="bottom-bar"):
                        yield Button("[+] Ajouter une paire", id="btn-add", variant="default")
                        yield Button("↻ Charger les données", id="btn-fetch", variant="default")
                        yield Label("", id="fetch-status")
            with TabPane("Configuration", id="tab-config"):
                from tui.screens.config_screen import ConfigScreen
                yield ConfigScreen()
        yield Footer()

    def on_mount(self) -> None:
        from tui.theme import BLOOMBERG
        self.register_theme(BLOOMBERG)
        self.theme = "bloomberg"
        self._load_widgets()
        self.set_interval(5, self._poll_cache)
        self.call_after_refresh(self._poll_cache)
        logger.info("TUI démarré")

    def _load_widgets(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        from tui.widgets.gallery import WidgetGallery
        config = load_config()
        gallery = self.query_one("#gallery", WidgetGallery)
        gallery.load_widgets([
            CurrencyWidget(w.pair, w.scale, widget_height=self._widget_height)
            for w in config.widgets
        ])
        logger.debug(f"{len(config.widgets)} widgets chargés")

    async def _poll_cache(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        for widget in self.query(CurrencyWidget):
            widget.refresh_if_updated()

    def on_button_pressed(self, event) -> None:
        btn_id = event.button.id
        if btn_id == "btn-add":
            self._handle_add_pair()
        elif btn_id == "btn-fetch":
            self._fetch_all_pairs()

    def _handle_add_pair(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget, _EditPairModal

        async def _handle(result) -> None:
            if not result:
                return
            new_pair, new_scale = result
            widget = CurrencyWidget(new_pair, new_scale, widget_height=self._widget_height)
            from tui.widgets.gallery import WidgetGallery
            await self.query_one("#gallery", WidgetGallery).add_currency_widget(widget)
            from shared.config import load_config, save_config, WidgetConfig
            config = load_config()
            config.widgets.append(WidgetConfig(new_pair, new_scale))
            save_config(config)
            from shared.config import notify_daemon
            notify_daemon()
            self._fetch_single_pair(new_pair, new_scale)

        self.push_screen(_EditPairModal("EUR/USD", "1M"), _handle)

    def _fetch_all_pairs(self) -> None:
        self.run_worker(self._do_fetch_all(), name="fetch-all", exclusive=True)

    def _fetch_single_pair(self, pair: str, scale: str) -> None:
        self.run_worker(self._do_fetch_one(pair, scale), name=f"fetch-{pair}", exclusive=False)

    async def _do_fetch_all(self) -> None:
        config = load_config()
        status = self.query_one("#fetch-status", Label)
        pairs = config.widgets
        status.update(f"⏳ Chargement de {len(pairs)} paire(s)...")
        for i, w in enumerate(pairs, 1):
            status.update(f"⏳ {w.pair} {w.scale} ({i}/{len(pairs)})...")
            await self._do_fetch(w.pair, w.scale)
        status.update("✓ Données à jour")
        self.set_timer(3, lambda: status.update(""))

    async def _do_fetch_one(self, pair: str, scale: str) -> None:
        status = self.query_one("#fetch-status", Label)
        status.update(f"⏳ Chargement {pair} {scale}...")
        await self._do_fetch(pair, scale)
        status.update(f"✓ {pair} {scale} chargé")
        self.set_timer(3, lambda: status.update(""))

    async def _do_fetch(self, pair: str, scale: str) -> None:
        from daemon.fetcher import fetch_rates
        from daemon.renderer import render_chart, render_error_chart
        from shared.paths import png_path
        path = png_path(pair, scale)
        try:
            rates = await fetch_rates(pair, scale)
            render_chart(rates, pair, scale, path)
            logger.info(f"Données chargées : {pair} {scale}")
        except Exception as exc:
            logger.error(f"Échec chargement {pair} {scale} : {exc}")
            render_error_chart(pair, str(exc), path)
