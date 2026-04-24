from __future__ import annotations

import math
import os
import re
import select
import sys
import termios
import tty

from tui.app import DashboardApp

_CELL_QUERY_TIMEOUT = 0.5


def _query_cell_ratio(logger) -> float | None:
    """Mesure le ratio cell_w/cell_h via CSI 16t sur /dev/tty.

    Utilise /dev/tty directement pour éviter les problèmes de redirection
    stdin/stdout. Doit être appelé AVANT le lancement de Textual.
    """
    try:
        tty_fh = open("/dev/tty", "r+b", buffering=0)
    except OSError as exc:
        logger.debug(f"[CSI16t] impossible d'ouvrir /dev/tty : {exc}")
        return None
    try:
        old = termios.tcgetattr(tty_fh)
        tty.setraw(tty_fh)
        tty_fh.write(b"\x1b[16t")
        tty_fh.flush()
        response = b""
        while True:
            ready, _, _ = select.select([tty_fh], [], [], _CELL_QUERY_TIMEOUT)
            if not ready:
                logger.debug(f"[CSI16t] timeout après {_CELL_QUERY_TIMEOUT}s, réponse brute: {repr(response)}")
                break
            c = tty_fh.read(1)
            response += c
            if c == b"t":
                break
        logger.debug(f"[CSI16t] réponse complète: {repr(response)}")
        m = re.match(rb"\x1b\[6;(\d+);(\d+)t", response)
        if m:
            cell_h = int(m.group(1))
            cell_w = int(m.group(2))
            logger.debug(f"[CSI16t] cell_h={cell_h}px  cell_w={cell_w}px  ratio={cell_w/cell_h:.4f}")
            if cell_h > 0:
                return cell_w / cell_h
        else:
            logger.debug(f"[CSI16t] regex non matché sur: {repr(response)}")
    except Exception as exc:
        logger.debug(f"[CSI16t] exception: {exc}")
    finally:
        try:
            termios.tcsetattr(tty_fh, termios.TCSADRAIN, old)
        except Exception:
            pass
        tty_fh.close()
    return None


def _compute_widget_height(cell_ratio: float, logger) -> int:
    nb_cols = 2  # WidgetGallery utilise 2 colonnes fixes
    term_size = os.get_terminal_size()
    term_cols = term_size.columns

    logger.debug(f"[calcul] largeur terminal : {term_cols} cols")
    logger.debug(f"[calcul] grille : {nb_cols} colonnes")

    # Largeur réelle du ChartDisplay (gutter entre colonnes + 2 bordures du widget)
    gutter_cols = nb_cols - 1
    col_width = (term_cols - gutter_cols) / nb_cols
    inner_width = col_width - 2
    logger.debug(f"[calcul] largeur colonne grille : {col_width:.1f} chars")
    logger.debug(f"[calcul] largeur interne ChartDisplay : {inner_width:.1f} chars")
    logger.debug(f"[calcul] cell_ratio utilisé : {cell_ratio:.4f}")

    # Hauteur optimale pour les graphiques (depuis le ratio PNG 8:3)
    image_ratio = 8 / 3
    h_chart_from_ratio = inner_width * cell_ratio / image_ratio
    logger.debug(f"[calcul] h_chart depuis ratio : {h_chart_from_ratio:.3f}")

    h_chart = max(4, math.ceil(h_chart_from_ratio))
    widget_height = h_chart + 5  # +1 marge pour absorber le décalage de rendu iTerm2
    logger.debug(f"[calcul] h_chart final : {h_chart}  →  widget_height = {widget_height}")
    return widget_height


if __name__ == "__main__":
    from logs.logger import get_logger
    from shared.config import load_config

    logger = get_logger("tui")
    config = load_config()
    measured = _query_cell_ratio(logger)
    if measured is not None:
        cell_ratio = measured
        logger.info(f"Ratio cellule mesuré via CSI 16t : {cell_ratio:.4f}")
    else:
        cell_ratio = config.terminal_cell_ratio
        logger.info(f"CSI 16t indisponible, fallback config : {cell_ratio:.4f}")

    widget_height = _compute_widget_height(cell_ratio, logger)

    DashboardApp(
        widget_height=widget_height,
        cell_ratio=cell_ratio,
    ).run()
