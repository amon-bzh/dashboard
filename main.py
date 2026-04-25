from __future__ import annotations

import math
import os

from tui.app import DashboardApp

_WIDGET_COLS = 2
_TOP_OVERHEAD = 2
_BOTTOM_OVERHEAD = 4


def _compute_widget_height(num_widgets: int = 4) -> int:
    term_rows = os.get_terminal_size().lines
    num_widget_rows = math.ceil(max(1, num_widgets) / _WIDGET_COLS)
    available_rows = term_rows - _TOP_OVERHEAD - _BOTTOM_OVERHEAD
    return max(8, available_rows // num_widget_rows)


if __name__ == "__main__":
    from logs.logger import get_logger
    from shared.config import load_config

    logger = get_logger("tui")
    config = load_config()
    widget_height = _compute_widget_height(num_widgets=len(config.widgets))
    logger.info(f"widget_height calculé : {widget_height}")
    DashboardApp(widget_height=widget_height).run()
