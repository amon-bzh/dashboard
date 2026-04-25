from __future__ import annotations

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from logs.logger import get_logger

logger = get_logger("daemon")

_BG     = "#05070a"
_GRID   = "#6b6355"
_TICK   = "#c9bfa8"
_RED    = "#ef4444"
_ORANGE = "#f97316"
_AMBER  = "#ffb020"
_LIME   = "#a3e635"
_GREEN  = "#4ade80"


def _fng_color(value: int) -> str:
    if value < 25:
        return _RED
    if value < 45:
        return _ORANGE
    if value < 55:
        return _AMBER
    if value < 75:
        return _LIME
    return _GREEN


def render_fng_chart(fng_data: Dict[str, Any], output_path: Path) -> None:
    history = fng_data["history"]
    all_dates = sorted(history.keys())
    last_30 = all_dates[-30:]
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in last_30]
    values = [history[d] for d in last_30]

    if not values:
        raise ValueError("Aucune donnée F&G disponible")

    current = fng_data["current"]
    line_color = _fng_color(current)

    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    ax.plot(dates, values, color=line_color, linewidth=1.5)
    ax.fill_between(dates, values, 0, alpha=0.15, color=line_color)
    ax.set_ylim(0, 100)
    for threshold, color in [(25, _RED), (45, _ORANGE), (55, _AMBER), (75, _LIME)]:
        ax.axhline(y=threshold, color=color, linewidth=0.4, linestyle="--", alpha=0.4)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(colors=_TICK, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(axis="y", color=_GRID, linewidth=0.5)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, format="png", dpi=100, facecolor=_BG)
    plt.close(fig)

    # Variation par rapport à j-7
    prev_7d = history.get(all_dates[-8], current) if len(all_dates) >= 8 else current
    variation_7d = current - prev_7d
    logger.debug(f"[F&G] render → {output_path.name}  current={current}  variation_7d={variation_7d:+d}")
    output_path.with_suffix(".json").write_text(json.dumps({
        "current": current,
        "classification": fng_data["classification"],
        "variation_7d": int(variation_7d),
    }))


def render_fng_error_chart(message: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.text(0.5, 0.5, f"⚠  {message}", ha="center", va="center",
            transform=ax.transAxes, color=_RED, fontsize=12)
    ax.axis("off")
    plt.savefig(output_path, format="png", dpi=100, facecolor=_BG)
    plt.close(fig)
