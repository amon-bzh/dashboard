from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from logs.logger import get_logger
from shared.config import load_config, save_config, notify_daemon

logger = get_logger("tui")


class ConfigScreen(Widget):
    DEFAULT_CSS = """
    ConfigScreen {
        padding: 1 2;
    }
    ConfigScreen Label {
        margin-top: 1;
        color: $text-muted;
    }
    ConfigScreen Input {
        margin-bottom: 1;
        border: solid $border;
    }
    #btn-apply {
        margin-top: 2;
    }
    #future-alerts {
        margin-top: 2;
        color: $text-disabled;
    }
    """

    def compose(self) -> ComposeResult:
        config = load_config()
        yield Label("Devise de base")
        yield Input(value=config.base_currency, id="input-base-currency")
        yield Label("Intervalle de rafraîchissement (minutes)")
        yield Input(
            value=str(config.refresh_interval_minutes),
            id="input-refresh",
            type="integer",
        )
        yield Label("Nombre de colonnes")
        yield Input(
            value=str(config.grid_columns),
            id="input-columns",
            type="integer",
        )
        yield Button("Appliquer", id="btn-apply", variant="primary")
        yield Static("⏳ Seuils d'alerte — Prochainement", id="future-alerts")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-apply":
            return

        config = load_config()
        config.base_currency = self.query_one("#input-base-currency", Input).value.strip().upper()
        try:
            config.refresh_interval_minutes = int(
                self.query_one("#input-refresh", Input).value
            )
            config.grid_columns = int(
                self.query_one("#input-columns", Input).value
            )
        except ValueError:
            logger.warning("Valeurs de configuration invalides")
            return

        save_config(config)
        notify_daemon()
        logger.info("Configuration sauvegardée et daemon notifié")

        from textual.containers import Grid
        grid = self.app.query_one("#grid", Grid)
        grid.styles.grid_size_columns = config.grid_columns
        grid.styles.grid_columns = " ".join(["1fr"] * config.grid_columns)
