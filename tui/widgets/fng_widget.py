from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from logs.logger import get_logger
from shared.paths import fng_png_path
from tui.widgets.currency_widget import ChartDisplay

logger = get_logger("tui")

_CLASSIFICATION_COLORS = {
    "Extreme Fear": "red",
    "Fear":         "red",
    "Neutral":      "yellow",
    "Greed":        "green",
    "Extreme Greed":"green",
}


class FngWidget(Widget):
    can_focus = True

    DEFAULT_CSS = """
    FngWidget {
        border: solid $border;
        height: 1fr;
        padding: 0;
    }
    FngWidget:focus {
        border: solid $primary;
    }
    FngWidget:focus .fng-header {
        color: $primary;
        text-style: bold;
    }
    .fng-header {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    .fng-value {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._png_path = fng_png_path()
        self._last_mtime: float = 0.0

    def compose(self) -> ComposeResult:
        yield Label("F&G · alternative.me · 30j", classes="fng-header")
        yield Label("— · —", id=f"fng-value-{id(self)}", classes="fng-value")
        yield ChartDisplay(self._png_path, id=f"fng-chart-{id(self)}")

    def refresh_if_updated(self) -> None:
        if not self._png_path.exists():
            return
        mtime = self._png_path.stat().st_mtime
        if mtime > self._last_mtime:
            self._last_mtime = mtime
            self.query_one(ChartDisplay).refresh_chart()
            self._refresh_value_label()

    def _refresh_value_label(self) -> None:
        meta_path = self._png_path.with_suffix(".json")
        if not meta_path.exists():
            return
        try:
            meta = json.loads(meta_path.read_text())
            current = int(meta["current"])
            classification = meta.get("classification", "")
            variation = meta.get("variation_7d", 0)
            color = _CLASSIFICATION_COLORS.get(classification, "yellow")
            sign = "+" if variation >= 0 else ""
            label = self.query_one(f"#fng-value-{id(self)}", Label)
            label.update(
                f"[{color}]{current} · {classification}[/]"
                f"  7j: {sign}{variation}"
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug(f"FngWidget label: {exc}")
