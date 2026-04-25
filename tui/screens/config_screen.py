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
        height: auto;
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
    #btn-purge {
        margin-top: 1;
        border: solid red;
    }
    #purge-status {
        margin-top: 1;
        color: #00b4d8;
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
        yield Button("Appliquer", id="btn-apply", variant="primary")
        yield Button("🗑 Purger la base de données", id="btn-purge", variant="error")
        yield Static("", id="purge-status")
        yield Static("⏳ Seuils d'alerte — Prochainement", id="future-alerts")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply":
            self._apply_config()
        elif event.button.id == "btn-purge":
            self._purge_cache()

    def _apply_config(self) -> None:
        config = load_config()
        config.base_currency = self.query_one("#input-base-currency", Input).value.strip().upper()
        try:
            config.refresh_interval_minutes = int(
                self.query_one("#input-refresh", Input).value
            )
        except ValueError:
            logger.warning("Valeurs de configuration invalides")
            return

        save_config(config)
        notify_daemon()
        logger.info("Configuration sauvegardée et daemon notifié")

    def _purge_cache(self) -> None:
        from shared.paths import CACHE_DIR
        status = self.query_one("#purge-status", Static)
        deleted = 0
        for f in CACHE_DIR.glob("*"):
            if f.is_file():
                f.unlink()
                deleted += 1
        logger.info(f"Cache purgé : {deleted} fichier(s) supprimé(s)")
        status.update(f"✓ {deleted} fichier(s) supprimé(s) — base purgée")
        self.set_timer(4, lambda: status.update(""))
