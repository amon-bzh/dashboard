import math
import os

from tui.app import DashboardApp


def _compute_widget_height() -> int:
    from shared.config import load_config

    config = load_config()
    nb_cols = max(1, config.grid_columns)
    term_cols = os.get_terminal_size().columns
    frame_width = term_cols / nb_cols
    # ratio figsize=(8,3) dans renderer.py
    image_ratio = 8 / 3
    h_chart = math.ceil(frame_width * config.terminal_cell_ratio / image_ratio)
    # 2 bordures + 1 header + 1 rate-line
    return max(10, h_chart + 4)


if __name__ == "__main__":
    DashboardApp(widget_height=_compute_widget_height()).run()
