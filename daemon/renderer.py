from __future__ import annotations

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Dict

_BG = "#1a1a2e"
_GREEN = "#00c896"
_RED = "#ff6b6b"
_GRID = "#2a2a4a"
_TICK = "#888888"


def render_chart(
    rates: Dict[str, float], pair: str, scale: str, output_path: Path
) -> None:
    sorted_dates = sorted(rates.keys())
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
    values = [rates[d] for d in sorted_dates]

    if not values:
        raise ValueError(f"Aucune donnée disponible pour {pair} {scale}")

    color = _GREEN if values[-1] >= values[0] else _RED

    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    ax.plot(dates, values, color=color, linewidth=1.5)
    ax.fill_between(dates, values, min(values), alpha=0.15, color=color)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.tick_params(colors=_TICK, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(axis="y", color=_GRID, linewidth=0.5)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, format="png", dpi=100, facecolor=_BG)
    plt.close(fig)

    # Écrire les métadonnées (taux actuel + variation %) pour le TUI
    variation_pct = round((values[-1] - values[0]) / values[0] * 100, 2)
    meta_path = output_path.with_suffix(".json")
    meta_path.write_text(json.dumps({
        "current": round(values[-1], 4),
        "variation_pct": variation_pct,
    }))


def render_error_chart(pair: str, message: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.text(
        0.5, 0.5, f"⚠  {message}",
        ha="center", va="center",
        transform=ax.transAxes,
        color=_RED, fontsize=12,
    )
    ax.axis("off")
    plt.savefig(output_path, format="png", dpi=100, facecolor=_BG)
    plt.close(fig)
