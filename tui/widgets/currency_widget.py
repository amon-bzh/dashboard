from __future__ import annotations

import base64
import sys
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.geometry import Region
from textual.message import Message
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
    """Affiche un PNG via le protocole iTerm2 inline images.

    Stratégie : render_lines() est le point d'accroche correct — il est appelé
    par le compositor Textual chaque fois qu'il va envoyer les strips au terminal,
    y compris quand il utilise le cache de StylesCache (ce que render_line() ne
    voit pas). On y planifie via call_after_refresh l'écriture de la séquence
    iTerm2 sur sys.__stdout__ (fd terminal réel), APRÈS que Textual a flushed ses
    cellules vides.
    """

    DEFAULT_CSS = """
    ChartDisplay {
        height: 1fr;
    }
    """

    def __init__(self, image_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.image_path = image_path
        self._write_pending = False
        self._prev_image_pos: tuple[int, int, int, int] | None = None  # x, y, w, h

    def render_lines(self, crop: Region) -> list[Strip]:
        strips = super().render_lines(crop)
        w, h = self.size.width, self.size.height
        if self.image_path.exists() and w > 0 and h > 0 and not self._write_pending:
            self._write_pending = True
            self.app.call_after_refresh(self._write_image)
        return strips

    def render_line(self, y: int) -> Strip:
        w = self.size.width
        h = self.size.height
        if not self.image_path.exists() and h > 0 and y == h // 2:
            msg = "⏳ Chargement..."
            pad = max(0, (w - len(msg)) // 2)
            return Strip([Segment(" " * pad + msg)])
        return Strip.blank(w)

    def _write_image(self) -> None:
        self._write_pending = False
        if not self.image_path.exists():
            self.refresh()
            return
        w = self.size.width
        h = self.size.height
        region = self.content_region
        logger.debug(
            f"_write_image {self.image_path.name} "
            f"size=({w},{h}) region=({region.x},{region.y})"
        )
        if w == 0 or h == 0:
            return
        display_h = h
        # Effacer l'ancienne zone si le widget a bougé (scroll)
        new_pos = (region.x, region.y, w, display_h)
        if self._prev_image_pos is not None and self._prev_image_pos != new_pos:
            px, py, pw, ph = self._prev_image_pos
            # Effacer avec la couleur de fond de l'app (#05070a = 5,7,10)
            sys.__stdout__.write("\x1b[48;2;5;7;10m")
            for row in range(ph):
                sys.__stdout__.write(f"\x1b[{py + 1 + row};{px + 1}H" + " " * pw)
            sys.__stdout__.write("\x1b[0m")
        self._prev_image_pos = new_pos

        data = self.image_path.read_bytes()

        import struct
        try:
            png_w = struct.unpack(">I", data[16:20])[0]
            png_h = struct.unpack(">I", data[20:24])[0]
            logger.debug(f"[image] {self.image_path.name} : PNG {png_w}×{png_h} px  ratio={png_w/png_h:.4f}")
        except Exception:
            pass

        encoded = base64.b64encode(data).decode()
        seq = (
            f"\x1b]1337;File=inline=1;"
            f"width={w}char;height={display_h}char;"
            f"preserveAspectRatio=1:{encoded}\x07"
        )
        cursor_pos = f"\x1b[{region.y + 1};{region.x + 1}H"
        sys.__stdout__.write(cursor_pos + seq)
        sys.__stdout__.flush()
        logger.debug(f"[image] séquence écrite : width={w}char height={display_h}char ({len(encoded)} b64)")

    def refresh_chart(self) -> None:
        logger.debug(f"ChartDisplay.refresh_chart {self.image_path.name}")
        self.refresh()  # → render_lines → call_after_refresh → _write_image


class CurrencyWidget(Widget):
    can_focus = True

    DEFAULT_CSS = f"""
    CurrencyWidget {{
        border: solid $border;
        height: auto;
        padding: 0;
    }}
    CurrencyWidget:focus {{
        border: solid {FOCUS_COLOR};
    }}
    CurrencyWidget:focus .header {{
        color: {FOCUS_COLOR};
        text-style: bold;
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

    def __init__(self, pair: str, scale: str, widget_height: int = 22, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pair = pair
        self.scale = scale
        self._png_path = png_path(pair, scale)
        self._last_mtime: float = 0.0
        self.styles.height = widget_height
        logger.debug(f"CurrencyWidget {pair}/{scale} height={widget_height}")

    def compose(self) -> ComposeResult:
        yield Label(f"{self.pair} · {self.scale}", classes="header")
        yield Label("— / —%", id=f"rate-{id(self)}", classes="rate-line")
        yield ChartDisplay(self._png_path, id=f"chart-{id(self)}")

    def refresh_if_updated(self) -> None:
        if not self._png_path.exists():
            logger.debug(f"refresh_if_updated: PNG absent {self._png_path}")
            return
        mtime = self._png_path.stat().st_mtime
        logger.debug(f"refresh_if_updated: {self.pair} {self.scale} mtime={mtime:.3f} last={self._last_mtime:.3f}")
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
        ("tab", "cycle_period", "Période suiv."),
        ("shift+tab", "cycle_period_back", "Période préc."),
        ("k", "delete_widget", "Supprimer"),
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

    def action_cycle_period_back(self) -> None:
        try:
            idx = self._PERIODS.index(self.scale)
        except ValueError:
            idx = 0  # échelle inconnue : on part de la première → wrap arrière vers la dernière
        self.scale = self._PERIODS[(idx - 1) % len(self._PERIODS)]
        self._png_path = png_path(self.pair, self.scale)
        self._last_mtime = 0.0
        self.query_one(".header", Label).update(f"{self.pair} · {self.scale}")
        self._update_config()
        from shared.config import notify_daemon
        notify_daemon()

    def action_delete_widget(self) -> None:
        self.post_message(CurrencyWidget.RequestDelete(self))

    class RequestDelete(Message):
        """Demande à la galerie parente de supprimer ce widget et de nettoyer la rangée."""
        def __init__(self, widget: "CurrencyWidget") -> None:
            super().__init__()
            self.widget = widget

    def on_context_menu_delete_widget(self) -> None:
        self.post_message(CurrencyWidget.RequestDelete(self))

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
        from tui.widgets.gallery import WidgetGallery
        config = load_config()
        gallery = self.app.query_one(WidgetGallery)
        config.widgets = [
            WidgetConfig(w.pair, w.scale)
            for w in gallery.all_currency_widgets()
        ]
        save_config(config)

    def on_context_menu_change_scale(self) -> None:
        self.on_context_menu_edit_pair()
