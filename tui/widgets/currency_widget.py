from __future__ import annotations

import base64
from pathlib import Path

from rich.segment import Segment, ControlType
from rich.style import Style
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Static

from logs.logger import get_logger
from shared.paths import png_path
from tui.widgets.context_menu import FOCUS_COLOR

logger = get_logger("tui")


class _EditPairModal(ModalScreen):
    DEFAULT_CSS = """
    _EditPairModal {
        align: center middle;
    }
    #modal-box {
        border: solid $border;
        background: $surface;
        padding: 1 2;
        width: 40;
        height: auto;
    }
    """

    def __init__(self, current_pair: str, current_scale: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pair = current_pair
        self._scale = current_scale

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical
        with Vertical(id="modal-box"):
            yield Label("Paire (ex: EUR/USD)")
            yield Input(value=self._pair, id="new-pair")
            yield Label("Échelle")
            yield Select(
                [(s, s) for s in ["1M", "3M", "6M", "1A", "2A", "5A"]],
                value=self._scale,
                id="new-scale",
            )
            yield Button("Valider", id="btn-ok", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            new_pair = self.query_one("#new-pair", Input).value.strip().upper()
            new_scale = self.query_one("#new-scale", Select).value
            parts = new_pair.split("/")
            if len(parts) != 2 or not parts[0] or not parts[1]:
                self.notify("Format invalide : utilisez BASE/QUOTE (ex: EUR/USD)", severity="error")
                return
            self.dismiss((new_pair, new_scale))


class ChartDisplay(Widget):
    """Affiche un PNG via le protocole iTerm2 inline images."""

    DEFAULT_CSS = """
    ChartDisplay {
        height: 1fr;
        align: center middle;
    }
    #chart-placeholder {
        color: $text-disabled;
        text-style: italic;
    }
    """

    def __init__(self, image_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.image_path = image_path
        self._placeholder: Static | None = None

    def compose(self) -> ComposeResult:
        self._placeholder = Static("⏳ Chargement...", id="chart-placeholder")
        yield self._placeholder

    def on_mount(self) -> None:
        self._render_image()

    def _render_image(self) -> None:
        if not self.image_path.exists():
            if self._placeholder:
                self._placeholder.update("⏳ Chargement...")
            return
        w = self.size.width
        h = self.size.height
        if w == 0 or h == 0:
            return
        data = self.image_path.read_bytes()
        encoded = base64.b64encode(data).decode()
        seq = (
            f"\x1b]1337;File=inline=1;"
            f"width={w}char;height={h}char;"
            f"preserveAspectRatio=1:{encoded}\x07"
        )
        # Écrire la séquence iTerm2 directement après avoir positionné le curseur
        region = self.content_region
        cursor_pos = f"\x1b[{region.y + 1};{region.x + 1}H"
        import sys
        sys.stdout.write(cursor_pos + seq)
        sys.stdout.flush()
        if self._placeholder:
            self._placeholder.update("")

    def refresh_chart(self) -> None:
        self._render_image()
        self.refresh()


class CurrencyWidget(Widget):
    can_focus = True

    DEFAULT_CSS = f"""
    CurrencyWidget {{
        border: solid $border;
        height: 22;
        padding: 0;
    }}
    CurrencyWidget:focus {{
        border: solid {FOCUS_COLOR};
    }}
    .header {{
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }}
    .rate-line {{
        height: 1;
        padding: 0 1;
    }}
    """

    def __init__(self, pair: str, scale: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pair = pair
        self.scale = scale
        self._png_path = png_path(pair, scale)
        self._last_mtime: float = 0.0

    def compose(self) -> ComposeResult:
        yield Label(f"{self.pair} · {self.scale}", classes="header")
        yield Label("— / —%", id=f"rate-{id(self)}", classes="rate-line")
        yield ChartDisplay(self._png_path, id=f"chart-{id(self)}")

    def refresh_if_updated(self) -> None:
        if not self._png_path.exists():
            return
        mtime = self._png_path.stat().st_mtime
        if mtime > self._last_mtime:
            self._last_mtime = mtime
            self.query_one(ChartDisplay).refresh_chart()
            self._refresh_rate_label()
            logger.debug(f"Chart rafraîchi : {self.pair} {self.scale}")

    def _refresh_rate_label(self) -> None:
        from shared.paths import CACHE_DIR
        base, quote = self.pair.split("/")
        meta_path = CACHE_DIR / f"{base}_{quote}_{self.scale}.json"
        if not meta_path.exists():
            return
        import json
        meta = json.loads(meta_path.read_text())
        label = self.query_one(f"#rate-{id(self)}", Label)
        try:
            rate = float(meta["current"])
            variation = meta.get("variation_pct", 0.0)
            sign = "+" if variation >= 0 else ""
            color = "green" if variation >= 0 else "red"
            label.update(f"{rate:.4f}  [{color}]{sign}{variation:.2f}%[/]")
        except (KeyError, ValueError, TypeError):
            label.update("— / —%")
            return

    BINDINGS = [
        ("m", "open_menu", "Menu"),
        ("p", "cycle_period", "Période"),
    ]

    def action_open_menu(self) -> None:
        from tui.widgets.context_menu import ContextMenu
        existing = self.query(ContextMenu)
        if existing:
            existing.first().remove()
            return
        self.mount(ContextMenu())

    _PERIODS = ["1M", "3M", "6M", "1A", "2A", "5A"]

    def action_cycle_period(self) -> None:
        try:
            idx = self._PERIODS.index(self.scale)
        except ValueError:
            idx = -1
        self.scale = self._PERIODS[(idx + 1) % len(self._PERIODS)]
        self._png_path = png_path(self.pair, self.scale)
        self._last_mtime = 0.0
        self.query_one(".header", Label).update(f"{self.pair} · {self.scale}")
        self._update_config()
        from shared.config import notify_daemon
        notify_daemon()

    def on_context_menu_delete_widget(self) -> None:
        self.remove()

    def on_context_menu_edit_pair(self) -> None:
        async def _handle_result(result) -> None:
            if result:
                new_pair, new_scale = result
                self.pair = new_pair
                self.scale = new_scale
                self._png_path = png_path(new_pair, new_scale)
                self._last_mtime = 0.0
                self.query_one(".header", Label).update(f"{new_pair} · {new_scale}")
                self._update_config()
                from shared.config import notify_daemon
                notify_daemon()

        self.app.push_screen(_EditPairModal(self.pair, self.scale), _handle_result)

    def _update_config(self) -> None:
        from shared.config import load_config, save_config, WidgetConfig
        from tui.widgets.currency_widget import CurrencyWidget
        config = load_config()
        config.widgets = [
            WidgetConfig(w.pair, w.scale)
            for w in self.app.query(CurrencyWidget)
        ]
        save_config(config)

    def on_context_menu_change_scale(self) -> None:
        self.on_context_menu_edit_pair()
