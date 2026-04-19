from __future__ import annotations

import base64
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Label

from logs.logger import get_logger
from shared.paths import png_path

logger = get_logger("tui")


class ChartDisplay(Widget):
    """Affiche un PNG via le protocole iTerm2 inline images."""

    DEFAULT_CSS = """
    ChartDisplay {
        height: 1fr;
    }
    """

    def __init__(self, image_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.image_path = image_path

    def render_line(self, y: int) -> Strip:
        if y == 0 and self.image_path.exists():
            data = self.image_path.read_bytes()
            encoded = base64.b64encode(data).decode()
            w = self.size.width
            h = self.size.height
            seq = (
                f"\x1b]1337;File=inline=1;"
                f"width={w}char;height={h}char;"
                f"preserveAspectRatio=1:{encoded}\x07"
            )
            return Strip([Segment(seq, Style())])

        if not self.image_path.exists() and y == self.size.height // 2:
            label = "⏳ Chargement..."
            pad = (self.size.width - len(label)) // 2
            return Strip([Segment(" " * pad + label, Style(color="yellow"))])

        return Strip([Segment(" " * self.size.width, Style())])

    def refresh_chart(self) -> None:
        self.refresh()


class CurrencyWidget(Widget):
    DEFAULT_CSS = """
    CurrencyWidget {
        border: solid $border;
        height: 22;
        padding: 0;
    }
    .header {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    .rate-line {
        height: 1;
        padding: 0 1;
    }
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
        rate = meta.get("current", "—")
        variation = meta.get("variation_pct", 0.0)
        sign = "+" if variation >= 0 else ""
        color = "green" if variation >= 0 else "red"
        label = self.query_one(f"#rate-{id(self)}", Label)
        label.update(f"{rate:.4f}  [{color}]{sign}{variation:.2f}%[/]")
