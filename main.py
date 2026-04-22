import math
import os
import re
import select
import sys
import termios
import tty

from tui.app import DashboardApp

_CELL_QUERY_TIMEOUT = 0.5  # secondes


def _query_cell_size() -> tuple[int, int]:
    """Retourne (cell_w_px, cell_h_px) via XTWINOPS CSI 16 t.

    Fonctionne uniquement si le terminal répond à cette séquence (iTerm2, etc.).
    Valeur par défaut : (8, 16) — cellule terminale la plus courante.
    """
    if not sys.stdin.isatty():
        return 8, 16
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdout.write("\x1b[16t")
        sys.stdout.flush()
        response = ""
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], _CELL_QUERY_TIMEOUT)
            if not ready:
                break
            c = sys.stdin.read(1)
            response += c
            if c == "t":
                break
        m = re.match(r"\x1b\[6;(\d+);(\d+)t", response)
        if m:
            cell_h = int(m.group(1))
            cell_w = int(m.group(2))
            return cell_w, cell_h
    except Exception:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return 8, 16


def _compute_widget_height(cell_w: int, cell_h: int) -> int:
    """Calcule la hauteur optimale du CurrencyWidget pour que l'image iTerm2 remplisse la largeur."""
    from shared.config import load_config

    config = load_config()
    nb_cols = max(1, config.grid_columns)
    term_cols = os.get_terminal_size().columns
    frame_width = term_cols / nb_cols

    # ratio figsize=(8,3) dans renderer.py
    image_ratio = 8 / 3
    h_chart = math.ceil(frame_width * cell_w / (image_ratio * cell_h))
    # 2 bordures + 1 header + 1 rate-line
    return max(10, h_chart + 4)


if __name__ == "__main__":
    cell_w, cell_h = _query_cell_size()
    widget_height = _compute_widget_height(cell_w, cell_h)
    DashboardApp(widget_height=widget_height).run()
