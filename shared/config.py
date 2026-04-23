from __future__ import annotations
import json
import os
import signal
from dataclasses import dataclass, field, asdict
from typing import List

import shared.paths as paths
from shared.paths import ensure_dirs


@dataclass
class WidgetConfig:
    pair: str
    scale: str


@dataclass
class DashboardConfig:
    base_currency: str = "EUR"
    refresh_interval_minutes: int = 60
    grid_columns: int = 2
    terminal_cell_ratio: float = 0.477
    widgets: List[WidgetConfig] = field(
        default_factory=lambda: [
            WidgetConfig("EUR/USD", "1M"),
            WidgetConfig("EUR/GBP", "1M"),
            WidgetConfig("EUR/JPY", "1M"),
        ]
    )


def load_config() -> DashboardConfig:
    if not paths.CONFIG_FILE.exists():
        cfg = DashboardConfig()
        save_config(cfg)
        return cfg
    data = json.loads(paths.CONFIG_FILE.read_text())
    widgets = [WidgetConfig(**w) for w in data.pop("widgets", [])]
    return DashboardConfig(**data, widgets=widgets)


def save_config(cfg: DashboardConfig) -> None:
    ensure_dirs()
    data = asdict(cfg)
    paths.CONFIG_FILE.write_text(json.dumps(data, indent=2))


def notify_daemon() -> None:
    """Envoie SIGHUP au daemon pour déclencher un rechargement immédiat."""
    if not paths.PID_FILE.exists():
        return
    pid = int(paths.PID_FILE.read_text().strip())
    try:
        os.kill(pid, signal.SIGHUP)
    except ProcessLookupError:
        paths.PID_FILE.unlink(missing_ok=True)
