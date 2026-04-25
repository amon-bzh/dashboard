from __future__ import annotations

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Dict

_BG    = "#05070a"
_RED   = "#ef4444"
_GREEN = "#4ade80"
_GRID  = "#6b6355"
_TICK  = "#c9bfa8"
_AMBER = "#ffb020"


def render_vix_chart(rates: Dict[str, float], scale: str, output_path: Path) -> None:
    sorted_dates = sorted(rates.keys())
    dates = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
    values = [rates[d] for d in sorted_dates]
    if not values:
        raise ValueError(f"Aucune donnée VIX pour {scale}")

    # VIX en hausse = plus de peur → rouge ; en baisse = calme → vert
    color = _RED if values[-1] >= values[0] else _GREEN

    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    ax.plot(dates, values, color=color, linewidth=1.5)
    ax.fill_between(dates, values, min(values), alpha=0.15, color=color)
    ax.axhline(y=20, color=_GRID,  linewidth=0.5, linestyle="--")
    ax.axhline(y=30, color=_AMBER, linewidth=0.5, linestyle="--")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.tick_params(colors=_TICK, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.grid(axis="y", color=_GRID, linewidth=0.5)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, format="png", dpi=100, facecolor=_BG)
    plt.close(fig)

    variation_pct = round((values[-1] - values[0]) / values[0] * 100, 2)
    regime = "high" if values[-1] >= 30 else "elevated" if values[-1] >= 20 else "low"
    output_path.with_suffix(".json").write_text(json.dumps({
        "current": round(values[-1], 2),
        "variation_pct": variation_pct,
        "regime": regime,
    }))


def render_vix_error_chart(message: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.text(0.5, 0.5, f"⚠  {message}", ha="center", va="center",
            transform=ax.transAxes, color=_RED, fontsize=12)
    ax.axis("off")
    plt.savefig(output_path, format="png", dpi=100, facecolor=_BG)
    plt.close(fig)
