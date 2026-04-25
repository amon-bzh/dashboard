from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from logs.logger import get_logger
from shared.paths import vix_png_path
from tui.widgets.currency_widget import ChartDisplay

logger = get_logger("tui")

_PERIODS = ["1M", "3M", "6M", "1A"]


class VixWidget(Widget):
    can_focus = True

    DEFAULT_CSS = """
    VixWidget {
        border: solid $border;
        height: 1fr;
        padding: 0;
    }
    VixWidget:focus {
        border: solid $primary;
    }
    VixWidget:focus .vix-header {
        color: $primary;
        text-style: bold;
    }
    .vix-header {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    .vix-rate {
        height: 1;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("p",         "cycle_period",      "Période"),
        ("tab",       "cycle_period",      "Période suiv."),
        ("shift+tab", "cycle_period_back", "Période préc."),
    ]

    def __init__(self, scale: str = "1M", **kwargs) -> None:
        super().__init__(**kwargs)
        self.scale = scale
        self._png_path = vix_png_path(scale)
        self._last_mtime: float = 0.0

    def compose(self) -> ComposeResult:
        yield Label(f"VIX · {self.scale}", classes="vix-header")
        yield Label("— / —%", id=f"vix-rate-{id(self)}", classes="vix-rate")
        yield ChartDisplay(self._png_path, id=f"vix-chart-{id(self)}")

    def refresh_if_updated(self) -> None:
        if not self._png_path.exists():
            return
        mtime = self._png_path.stat().st_mtime
        if mtime > self._last_mtime:
            self._last_mtime = mtime
            self.query_one(ChartDisplay).refresh_chart()
            self._refresh_rate_label()

    def _refresh_rate_label(self) -> None:
        meta_path = self._png_path.with_suffix(".json")
        if not meta_path.exists():
            return
        try:
            meta = json.loads(meta_path.read_text())
            current = float(meta["current"])
            variation = meta.get("variation_pct", 0.0)
            regime = meta.get("regime", "")
            sign = "+" if variation >= 0 else ""
            color = "red" if variation >= 0 else "green"
            label = self.query_one(f"#vix-rate-{id(self)}", Label)
            label.update(f"{current:.2f}  [{color}]{sign}{variation:.2f}%[/]  {regime}")
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug(f"VixWidget label: {exc}")

    def action_cycle_period(self) -> None:
        try:
            idx = _PERIODS.index(self.scale)
        except ValueError:
            idx = -1
        self.scale = _PERIODS[(idx + 1) % len(_PERIODS)]
        self._png_path = vix_png_path(self.scale)
        self._last_mtime = 0.0
        self.query_one(".vix-header", Label).update(f"VIX · {self.scale}")
        self.refresh_if_updated()

    def action_cycle_period_back(self) -> None:
        try:
            idx = _PERIODS.index(self.scale)
        except ValueError:
            idx = 0
        self.scale = _PERIODS[(idx - 1) % len(_PERIODS)]
        self._png_path = vix_png_path(self.scale)
        self._last_mtime = 0.0
        self.query_one(".vix-header", Label).update(f"VIX · {self.scale}")
        self.refresh_if_updated()
