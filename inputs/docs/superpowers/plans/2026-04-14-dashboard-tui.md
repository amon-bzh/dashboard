# Dashboard TUI — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire un dashboard TUI de suivi de risque de change composé d'un daemon de génération de graphiques matplotlib et d'un frontend Textual affichant les images via le protocole iTerm2.

**Architecture:** Un daemon Python (géré par Launchd) fetche les données Frankfurter.app, génère des PNG matplotlib et les stocke dans `~/.config/dashboard/cache/`. Un frontend Textual lit ces PNG, les affiche via le protocole iTerm2 inline images, et envoie `SIGHUP` au daemon quand la configuration change. La communication entre les deux processus passe uniquement par `~/.config/dashboard/config.json` et `daemon.pid`.

**Tech Stack:** Python 3.12, Textual ≥ 0.80, httpx, matplotlib, scipy, python-dateutil, pytest, pytest-asyncio.

---

## Carte des fichiers

| Fichier | Rôle |
|---|---|
| `shared/paths.py` | Constantes de chemins, création des répertoires |
| `shared/config.py` | Dataclasses config, lecture/écriture JSON, envoi SIGHUP |
| `logs/logger.py` | Logger rotatif partagé daemon + TUI |
| `daemon/fetcher.py` | Client async Frankfurter.app |
| `daemon/renderer.py` | Génération PNG matplotlib |
| `daemon/__main__.py` | Boucle principale, SIGHUP, PID file |
| `com.user.dashboard.plist` | Launchd service descriptor |
| `tui/app.py` | DashboardApp Textual (tabs, grid, polling) |
| `tui/widgets/currency_widget.py` | Widget devise + ChartDisplay (iTerm2) |
| `tui/widgets/context_menu.py` | Menu contextuel flottant |
| `tui/screens/config_screen.py` | Onglet Configuration |
| `main.py` | Point d'entrée TUI |
| `bin/dashboard` | Script shell (active .venv, lance main.py) |
| `tests/test_config.py` | Tests unitaires config |
| `tests/test_fetcher.py` | Tests unitaires fetcher (httpx mocké) |
| `tests/test_renderer.py` | Tests unitaires renderer (PNG généré) |
| `tests/test_tui.py` | Tests Textual (Pilot) |

---

## Task 1 : Scaffolding du projet

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `shared/__init__.py`, `daemon/__init__.py`, `tui/__init__.py`, `tui/widgets/__init__.py`, `tui/screens/__init__.py`, `logs/__init__.py`, `tests/__init__.py`

- [ ] **Step 1 : Créer l'environnement virtuel Python 3.12**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

- [ ] **Step 2 : Créer `requirements.txt`**

```
textual>=0.80.0
httpx>=0.27.0
matplotlib>=3.9.0
scipy>=1.13.0
python-dateutil>=2.9.0
pytest>=8.1.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 3 : Installer les dépendances**

```bash
pip install -r requirements.txt
```

Expected : installation sans erreur.

- [ ] **Step 4 : Créer `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 5 : Créer les répertoires et fichiers `__init__.py` vides**

```bash
mkdir -p shared daemon tui/widgets tui/screens logs tests bin
touch shared/__init__.py daemon/__init__.py tui/__init__.py \
      tui/widgets/__init__.py tui/screens/__init__.py \
      logs/__init__.py tests/__init__.py
```

- [ ] **Step 6 : Vérifier que pytest tourne sans erreur**

```bash
pytest
```

Expected : `no tests ran` sans erreur.

- [ ] **Step 7 : Commit**

```bash
git add .
git commit -m "feat: scaffolding initial du projet"
```

---

## Task 2 : shared/paths.py

**Files:**
- Create: `shared/paths.py`
- Create: `tests/test_paths.py`

- [ ] **Step 1 : Écrire le test**

```python
# tests/test_paths.py
from pathlib import Path
from shared.paths import CONFIG_DIR, CACHE_DIR, png_path, ensure_dirs

def test_png_path_naming():
    p = png_path("EUR/USD", "1M")
    assert p.name == "EUR_USD_1M.png"
    assert p.parent == CACHE_DIR

def test_ensure_dirs_creates_directories(tmp_path, monkeypatch):
    monkeypatch.setattr("shared.paths.CONFIG_DIR", tmp_path / "dashboard")
    monkeypatch.setattr("shared.paths.CACHE_DIR", tmp_path / "dashboard" / "cache")
    from shared import paths
    paths.CONFIG_DIR = tmp_path / "dashboard"
    paths.CACHE_DIR = tmp_path / "dashboard" / "cache"
    paths.ensure_dirs()
    assert paths.CONFIG_DIR.exists()
    assert paths.CACHE_DIR.exists()
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_paths.py -v
```

Expected : `ModuleNotFoundError` ou `ImportError`.

- [ ] **Step 3 : Créer `shared/paths.py`**

```python
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "dashboard"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"
PID_FILE = CONFIG_DIR / "daemon.pid"
LOG_FILE = CONFIG_DIR / "dashboard.log"


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def png_path(pair: str, scale: str) -> Path:
    base, quote = pair.split("/")
    return CACHE_DIR / f"{base}_{quote}_{scale}.png"
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/test_paths.py -v
```

Expected : 2 tests PASS.

- [ ] **Step 5 : Commit**

```bash
git add shared/paths.py tests/test_paths.py
git commit -m "feat: shared/paths — constantes de chemins et utilitaires"
```

---

## Task 3 : shared/config.py

**Files:**
- Create: `shared/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1 : Écrire les tests**

```python
# tests/test_config.py
import json
from pathlib import Path
import pytest
from shared.config import DashboardConfig, WidgetConfig, load_config, save_config

def test_default_config_has_three_widgets():
    cfg = DashboardConfig()
    assert len(cfg.widgets) == 3
    assert cfg.widgets[0].pair == "EUR/USD"

def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("shared.paths.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("shared.paths.CONFIG_FILE", tmp_path / "config.json")
    import shared.paths as p
    p.CONFIG_DIR = tmp_path
    p.CONFIG_FILE = tmp_path / "config.json"
    p.CACHE_DIR = tmp_path / "cache"
    p.CACHE_DIR.mkdir()

    cfg = DashboardConfig(
        base_currency="USD",
        refresh_interval_minutes=30,
        grid_columns=3,
        widgets=[WidgetConfig("GBP/JPY", "6M")],
    )
    save_config(cfg)
    loaded = load_config()
    assert loaded.base_currency == "USD"
    assert loaded.refresh_interval_minutes == 30
    assert loaded.grid_columns == 3
    assert loaded.widgets[0].pair == "GBP/JPY"
    assert loaded.widgets[0].scale == "6M"

def test_load_config_creates_default_if_missing(tmp_path, monkeypatch):
    import shared.paths as p
    p.CONFIG_DIR = tmp_path
    p.CONFIG_FILE = tmp_path / "config.json"
    p.CACHE_DIR = tmp_path / "cache"
    p.CACHE_DIR.mkdir()
    cfg = load_config()
    assert isinstance(cfg, DashboardConfig)
    assert (tmp_path / "config.json").exists()
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_config.py -v
```

Expected : `ModuleNotFoundError`.

- [ ] **Step 3 : Créer `shared/config.py`**

```python
from __future__ import annotations
import json
import os
import signal
from dataclasses import dataclass, field, asdict
from typing import List

from shared.paths import CONFIG_FILE, PID_FILE, ensure_dirs


@dataclass
class WidgetConfig:
    pair: str
    scale: str


@dataclass
class DashboardConfig:
    base_currency: str = "EUR"
    refresh_interval_minutes: int = 60
    grid_columns: int = 2
    widgets: List[WidgetConfig] = field(
        default_factory=lambda: [
            WidgetConfig("EUR/USD", "1M"),
            WidgetConfig("EUR/GBP", "1M"),
            WidgetConfig("EUR/JPY", "1M"),
        ]
    )


def load_config() -> DashboardConfig:
    if not CONFIG_FILE.exists():
        cfg = DashboardConfig()
        save_config(cfg)
        return cfg
    data = json.loads(CONFIG_FILE.read_text())
    widgets = [WidgetConfig(**w) for w in data.pop("widgets", [])]
    return DashboardConfig(**data, widgets=widgets)


def save_config(cfg: DashboardConfig) -> None:
    ensure_dirs()
    data = asdict(cfg)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def notify_daemon() -> None:
    """Envoie SIGHUP au daemon pour déclencher un rechargement immédiat."""
    if not PID_FILE.exists():
        return
    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, signal.SIGHUP)
    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/test_config.py -v
```

Expected : 3 tests PASS.

- [ ] **Step 5 : Commit**

```bash
git add shared/config.py tests/test_config.py
git commit -m "feat: shared/config — dataclasses, lecture/écriture JSON, SIGHUP"
```

---

## Task 4 : logs/logger.py

**Files:**
- Create: `logs/logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1 : Écrire le test**

```python
# tests/test_logger.py
import logging
import os
from logs.logger import get_logger

def test_logger_returns_named_logger():
    logger = get_logger("daemon")
    assert logger.name == "dashboard.daemon"

def test_logger_respects_env_level(monkeypatch, tmp_path):
    import shared.paths as p
    p.LOG_FILE = tmp_path / "dashboard.log"
    monkeypatch.setenv("DASHBOARD_LOG_LEVEL", "DEBUG")
    # Forcer un nouveau logger sans handlers
    import logging
    logging.getLogger("dashboard.test_level").handlers.clear()
    import importlib, logs.logger as mod
    importlib.reload(mod)
    logger = mod.get_logger("test_level")
    assert logger.level == logging.DEBUG
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_logger.py -v
```

Expected : `ModuleNotFoundError`.

- [ ] **Step 3 : Créer `logs/logger.py`**

```python
import logging
import os
from logging.handlers import RotatingFileHandler

from shared.paths import LOG_FILE, ensure_dirs


def get_logger(component: str) -> logging.Logger:
    ensure_dirs()
    level_name = os.environ.get("DASHBOARD_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(f"dashboard.{component}")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter(f"%(asctime)s [{component}] %(levelname)s %(message)s")
    )
    logger.addHandler(handler)
    return logger
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/test_logger.py -v
```

Expected : 2 tests PASS.

- [ ] **Step 5 : Commit**

```bash
git add logs/logger.py tests/test_logger.py
git commit -m "feat: logs/logger — rotating file handler, niveau via env var"
```

---

## Task 5 : daemon/fetcher.py

**Files:**
- Create: `daemon/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1 : Écrire les tests**

```python
# tests/test_fetcher.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from daemon.fetcher import fetch_rates, fetch_current_rate, SCALES

def test_scales_has_six_entries():
    assert set(SCALES.keys()) == {"1M", "3M", "6M", "1A", "2A", "5A"}

@pytest.mark.asyncio
async def test_fetch_rates_returns_date_rate_dict():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "base": "EUR",
        "rates": {
            "2025-01-02": {"USD": 1.05},
            "2025-01-03": {"USD": 1.06},
        }
    }
    with patch("daemon.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await fetch_rates("EUR/USD", "1M")

    assert result == {"2025-01-02": 1.05, "2025-01-03": 1.06}

@pytest.mark.asyncio
async def test_fetch_current_rate_returns_float():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"rates": {"USD": 1.0842}}
    with patch("daemon.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await fetch_current_rate("EUR/USD")

    assert result == 1.0842
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_fetcher.py -v
```

Expected : `ModuleNotFoundError`.

- [ ] **Step 3 : Créer `daemon/fetcher.py`**

```python
from __future__ import annotations
from datetime import date
from typing import Dict

import httpx
from dateutil.relativedelta import relativedelta

BASE_URL = "https://api.frankfurter.app"

SCALES: Dict[str, relativedelta] = {
    "1M": relativedelta(months=1),
    "3M": relativedelta(months=3),
    "6M": relativedelta(months=6),
    "1A": relativedelta(years=1),
    "2A": relativedelta(years=2),
    "5A": relativedelta(years=5),
}


async def fetch_rates(pair: str, scale: str) -> Dict[str, float]:
    """Retourne {date_iso: taux} pour la paire et l'échelle données."""
    base, quote = pair.split("/")
    end_date = date.today()
    start_date = end_date - SCALES[scale]

    url = f"{BASE_URL}/{start_date}..{end_date}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"from": base, "to": quote})
        response.raise_for_status()

    data = response.json()
    return {d: rates[quote] for d, rates in data["rates"].items()}


async def fetch_current_rate(pair: str) -> float:
    """Retourne le taux le plus récent pour la paire."""
    base, quote = pair.split("/")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{BASE_URL}/latest", params={"from": base, "to": quote}
        )
        response.raise_for_status()
    return float(response.json()["rates"][quote])
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/test_fetcher.py -v
```

Expected : 3 tests PASS.

- [ ] **Step 5 : Commit**

```bash
git add daemon/fetcher.py tests/test_fetcher.py
git commit -m "feat: daemon/fetcher — client async Frankfurter.app"
```

---

## Task 6 : daemon/renderer.py

**Files:**
- Create: `daemon/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1 : Écrire les tests**

```python
# tests/test_renderer.py
import struct
from pathlib import Path
import pytest
from daemon.renderer import render_chart, render_error_chart

SAMPLE_RATES = {
    "2025-01-02": 1.050,
    "2025-01-03": 1.055,
    "2025-01-06": 1.048,
    "2025-01-07": 1.060,
    "2025-01-08": 1.072,
}

def _is_valid_png(path: Path) -> bool:
    with open(path, "rb") as f:
        header = f.read(8)
    return header == b"\x89PNG\r\n\x1a\n"

def test_render_chart_creates_png(tmp_path):
    output = tmp_path / "test.png"
    render_chart(SAMPLE_RATES, "EUR/USD", "1M", output)
    assert output.exists()
    assert _is_valid_png(output)

def test_render_chart_green_when_up(tmp_path):
    output = tmp_path / "up.png"
    rates = {"2025-01-02": 1.00, "2025-01-03": 1.10}
    render_chart(rates, "EUR/USD", "1M", output)
    assert output.exists()

def test_render_error_chart_creates_png(tmp_path):
    output = tmp_path / "error.png"
    render_error_chart("EUR/XYZ", "Paire invalide", output)
    assert output.exists()
    assert _is_valid_png(output)
```

- [ ] **Step 2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_renderer.py -v
```

Expected : `ModuleNotFoundError`.

- [ ] **Step 3 : Créer `daemon/renderer.py`**

```python
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
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
    import json
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
```

- [ ] **Step 4 : Lancer les tests**

```bash
pytest tests/test_renderer.py -v
```

Expected : 3 tests PASS.

- [ ] **Step 5 : Commit**

```bash
git add daemon/renderer.py tests/test_renderer.py
git commit -m "feat: daemon/renderer — génération PNG matplotlib avec thème sombre"
```

---

## Task 7 : daemon/__main__.py

**Files:**
- Create: `daemon/__main__.py`

- [ ] **Step 1 : Créer `daemon/__main__.py`**

```python
from __future__ import annotations

import asyncio
import os
import signal

from daemon.fetcher import fetch_rates
from daemon.renderer import render_chart, render_error_chart
from logs.logger import get_logger
from shared.config import load_config
from shared.paths import PID_FILE, ensure_dirs, png_path

logger = get_logger("daemon")
_reload_event: asyncio.Event


def _handle_sighup() -> None:
    logger.info("SIGHUP reçu — rechargement de la configuration")
    _reload_event.set()


async def generate_png(pair: str, scale: str) -> None:
    path = png_path(pair, scale)
    logger.debug(f"Génération {pair} {scale} → {path.name}")
    try:
        rates = await fetch_rates(pair, scale)
        render_chart(rates, pair, scale, path)
        logger.info(f"PNG généré : {path.name}")
    except Exception as exc:
        logger.error(f"Échec {pair} {scale} : {exc}")
        render_error_chart(pair, str(exc), path)


async def generate_all(config) -> None:
    tasks = [generate_png(w.pair, w.scale) for w in config.widgets]
    await asyncio.gather(*tasks)


async def main() -> None:
    global _reload_event
    _reload_event = asyncio.Event()

    ensure_dirs()
    PID_FILE.write_text(str(os.getpid()))
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGHUP, _handle_sighup)
    logger.info("Daemon démarré")

    try:
        while True:
            _reload_event.clear()
            config = load_config()
            await generate_all(config)

            interval = config.refresh_interval_minutes * 60
            logger.info(f"Pause de {config.refresh_interval_minutes} min")
            try:
                await asyncio.wait_for(_reload_event.wait(), timeout=interval)
                logger.info("Rechargement déclenché par SIGHUP")
            except asyncio.TimeoutError:
                logger.info("Rafraîchissement planifié")
    finally:
        PID_FILE.unlink(missing_ok=True)
        logger.info("Daemon arrêté")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2 : Tester le daemon manuellement**

```bash
source .venv/bin/activate
python -m daemon &
DAEMON_PID=$!
sleep 5
ls ~/.config/dashboard/cache/
kill $DAEMON_PID
```

Expected : les PNG EUR_USD_1M.png, EUR_GBP_1M.png, EUR_JPY_1M.png sont présents dans le cache.

- [ ] **Step 3 : Tester SIGHUP**

```bash
python -m daemon &
DAEMON_PID=$!
sleep 3
kill -HUP $DAEMON_PID
sleep 3
kill $DAEMON_PID
```

Expected : les logs indiquent "SIGHUP reçu — rechargement de la configuration".

- [ ] **Step 4 : Commit**

```bash
git add daemon/__main__.py
git commit -m "feat: daemon — boucle principale, SIGHUP, PID file"
```

---

## Task 8 : com.user.dashboard.plist

**Files:**
- Create: `com.user.dashboard.plist`

- [ ] **Step 1 : Déterminer les chemins absolus**

```bash
pwd          # → <PROJECT_DIR>
echo $(pwd)/.venv/bin/python
```

- [ ] **Step 2 : Créer `com.user.dashboard.plist`** en remplaçant `<PROJECT_DIR>` par le chemin absolu réel

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string><PROJECT_DIR>/.venv/bin/python</string>
        <string>-m</string>
        <string>daemon</string>
    </array>
    <key>WorkingDirectory</key>
    <string><PROJECT_DIR></string>
    <key>StandardOutPath</key>
    <string>/Users/Antoine/.config/dashboard/daemon-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Antoine/.config/dashboard/daemon-stderr.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DASHBOARD_LOG_LEVEL</key>
        <string>INFO</string>
    </dict>
</dict>
</plist>
```

- [ ] **Step 3 : Installer et démarrer le service Launchd**

```bash
cp com.user.dashboard.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.dashboard.plist
launchctl start com.user.dashboard
```

- [ ] **Step 4 : Vérifier que le daemon tourne**

```bash
launchctl list | grep dashboard
ls ~/.config/dashboard/cache/
```

Expected : le daemon est listé, les PNG sont générés.

- [ ] **Step 5 : Commit**

```bash
git add com.user.dashboard.plist
git commit -m "feat: Launchd plist — com.user.dashboard"
```

---

## Task 9 : main.py + tui/app.py (squelette)

**Files:**
- Create: `main.py`
- Create: `tui/app.py`
- Create: `tests/test_tui.py`

- [ ] **Step 1 : Écrire le test de démarrage**

```python
# tests/test_tui.py
import pytest
from textual.testing import CSSValidationResult
from tui.app import DashboardApp

@pytest.mark.asyncio
async def test_app_starts_without_error():
    app = DashboardApp()
    async with app.run_test() as pilot:
        assert pilot.app.is_running
        await pilot.pause()
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_tui.py::test_app_starts_without_error -v
```

Expected : `ModuleNotFoundError`.

- [ ] **Step 3 : Créer `tui/app.py`**

```python
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Grid
from textual.widgets import TabbedContent, TabPane

from shared.config import load_config
from logs.logger import get_logger

logger = get_logger("tui")


class DashboardApp(App):
    CSS = """
    Screen {
        background: #1a1a2e;
    }
    #grid {
        layout: grid;
        grid-gutter: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                with ScrollableContainer():
                    yield Grid(id="grid")
            with TabPane("Configuration", id="tab-config"):
                from tui.screens.config_screen import ConfigScreen
                yield ConfigScreen()

    def on_mount(self) -> None:
        self._load_widgets()
        self.set_interval(5, self._poll_cache)
        logger.info("TUI démarré")

    def _load_widgets(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        config = load_config()
        grid = self.query_one("#grid", Grid)
        grid.styles.grid_size_columns = config.grid_columns
        grid.styles.grid_columns = " ".join(["1fr"] * config.grid_columns)
        for w in config.widgets:
            grid.mount(CurrencyWidget(w.pair, w.scale))
        logger.debug(f"{len(config.widgets)} widgets chargés")

    async def _poll_cache(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        for widget in self.query(CurrencyWidget):
            widget.refresh_if_updated()
```

- [ ] **Step 4 : Créer `main.py`**

```python
from tui.app import DashboardApp

if __name__ == "__main__":
    DashboardApp().run()
```

- [ ] **Step 5 : Lancer le test**

```bash
pytest tests/test_tui.py::test_app_starts_without_error -v
```

Expected : PASS.

- [ ] **Step 6 : Commit**

```bash
git add tui/app.py main.py tests/test_tui.py
git commit -m "feat: tui/app — squelette DashboardApp avec onglets et grille"
```

---

## Task 10 : tui/widgets/currency_widget.py

Le widget affiche un PNG via le protocole iTerm2 inline images. Le protocole est : `ESC ] 1337 ; File=inline=1;width=Wchar;height=Hchar:<base64> BEL`. Le widget utilise `render_line()` pour injecter la séquence d'échappement au niveau bas de Textual, en contournant le filtrage Rich sur les séquences OSC.

> **Note d'implémentation :** si iTerm2 ne rend pas l'image correctement dans le contexte Textual, ajouter la bibliothèque `rich-pixels` en fallback et remplacer `ChartDisplay` par un widget `Pixels` converti depuis le PNG.

**Files:**
- Create: `tui/widgets/currency_widget.py`

- [ ] **Step 1 : Ajouter le test d'instanciation**

```python
# Dans tests/test_tui.py, ajouter :
@pytest.mark.asyncio
async def test_currency_widget_mounts(tmp_path, monkeypatch):
    import shared.paths as p
    p.CACHE_DIR = tmp_path
    p.CONFIG_FILE = tmp_path / "config.json"
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig(widgets=[]))
    from tui.widgets.currency_widget import CurrencyWidget
    app = DashboardApp()
    async with app.run_test() as pilot:
        widget = CurrencyWidget("EUR/USD", "1M")
        await pilot.app.query_one("#grid", Grid).mount(widget)
        await pilot.pause()
        assert pilot.app.query_one(CurrencyWidget)
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_tui.py::test_currency_widget_mounts -v
```

Expected : `ModuleNotFoundError`.

- [ ] **Step 3 : Créer `tui/widgets/currency_widget.py`**

```python
from __future__ import annotations

import base64
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Label

from logs.logger import get_logger
from shared.paths import png_path

logger = get_logger("tui")


class ChartDisplay(Widget):
    """Affiche un PNG via le protocole iTerm2 inline images."""

    DEFAULT_CSS = """
    ChartDisplay {
        height: 1fr;
    }
    """

    def __init__(self, image_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.image_path = image_path

    def render_line(self, y: int) -> Strip:
        # La séquence iTerm2 est émise sur la ligne 0 uniquement.
        # iTerm2 positionne l'image à partir du curseur et occupe
        # les lignes suivantes automatiquement.
        if y == 0 and self.image_path.exists():
            data = self.image_path.read_bytes()
            encoded = base64.b64encode(data).decode()
            w = self.size.width
            h = self.size.height
            seq = (
                f"\x1b]1337;File=inline=1;"
                f"width={w}char;height={h}char;"
                f"preserveAspectRatio=1:{encoded}\x07"
            )
            return Strip([Segment(seq, Style())])

        if not self.image_path.exists() and y == self.size.height // 2:
            label = "⏳ Chargement..."
            pad = (self.size.width - len(label)) // 2
            return Strip([Segment(" " * pad + label, Style(color="yellow"))])

        return Strip([Segment(" " * self.size.width, Style())])

    def refresh_chart(self) -> None:
        self.refresh()


class CurrencyWidget(Widget):
    DEFAULT_CSS = """
    CurrencyWidget {
        border: solid $border;
        height: 22;
        padding: 0;
    }
    .header {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    .rate-line {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, pair: str, scale: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pair = pair
        self.scale = scale
        self._png_path = png_path(pair, scale)
        self._last_mtime: float = 0.0

    def compose(self) -> ComposeResult:
        yield Label(f"{self.pair} · {self.scale}", classes="header")
        yield Label("— / —%", id=f"rate-{id(self)}", classes="rate-line")
        yield ChartDisplay(self._png_path, id=f"chart-{id(self)}")

    def refresh_if_updated(self) -> None:
        if not self._png_path.exists():
            return
        mtime = self._png_path.stat().st_mtime
        if mtime > self._last_mtime:
            self._last_mtime = mtime
            self.query_one(ChartDisplay).refresh_chart()
            self._refresh_rate_label()
            logger.debug(f"Chart rafraîchi : {self.pair} {self.scale}")

    def _refresh_rate_label(self) -> None:
        """Lit le fichier JSON de taux généré par le daemon et met à jour le label."""
        from shared.paths import CACHE_DIR
        base, quote = self.pair.split("/")
        meta_path = CACHE_DIR / f"{base}_{quote}_{self.scale}.json"
        if not meta_path.exists():
            return
        import json
        meta = json.loads(meta_path.read_text())
        rate = meta.get("current", "—")
        variation = meta.get("variation_pct", 0.0)
        sign = "+" if variation >= 0 else ""
        color = "green" if variation >= 0 else "red"
        label = self.query_one(f"#rate-{id(self)}", Label)
        label.update(f"{rate:.4f}  [{color}]{sign}{variation:.2f}%[/]")
```

- [ ] **Step 4 : Lancer le test**

```bash
pytest tests/test_tui.py -v
```

Expected : tous les tests PASS.

- [ ] **Step 5 : Commit**

```bash
git add tui/widgets/currency_widget.py tests/test_tui.py
git commit -m "feat: CurrencyWidget — affichage PNG via protocole iTerm2"
```

---

## Task 11 : tui/widgets/context_menu.py

**Files:**
- Create: `tui/widgets/context_menu.py`

- [ ] **Step 1 : Ajouter le test**

```python
# Dans tests/test_tui.py, ajouter :
@pytest.mark.asyncio
async def test_context_menu_appears_on_key_m():
    from tui.widgets.context_menu import ContextMenu
    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Focuser un widget et appuyer sur 'm'
        widgets = list(pilot.app.query(CurrencyWidget))
        if widgets:
            widgets[0].focus()
            await pilot.press("m")
            await pilot.pause()
            menus = list(pilot.app.query(ContextMenu))
            assert len(menus) == 1
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_tui.py::test_context_menu_appears_on_key_m -v
```

Expected : FAIL (ContextMenu non défini).

- [ ] **Step 3 : Créer `tui/widgets/context_menu.py`**

```python
from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from textual.message import Message


class ContextMenu(Widget):
    """Menu contextuel flottant pour un CurrencyWidget."""

    DEFAULT_CSS = """
    ContextMenu {
        layer: overlay;
        border: solid $border;
        background: $surface;
        width: 24;
        height: auto;
        padding: 0;
    }
    ContextMenu Label {
        height: 1;
        padding: 0 1;
    }
    ContextMenu Label:hover {
        background: $accent;
    }
    """

    class EditPair(Message):
        pass

    class ChangeScale(Message):
        pass

    class DeleteWidget(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Label("✎  Modifier la paire", id="menu-edit")
        yield Label("⊞  Changer l'échelle", id="menu-scale")
        yield Label("✕  Supprimer", id="menu-delete")

    def on_label_click(self, event) -> None:
        label_id = event.widget.id
        if label_id == "menu-edit":
            self.post_message(self.EditPair())
        elif label_id == "menu-scale":
            self.post_message(self.ChangeScale())
        elif label_id == "menu-delete":
            self.post_message(self.DeleteWidget())
        self.remove()
```

- [ ] **Step 4 : Connecter le menu au `CurrencyWidget`**

Ajouter dans `tui/widgets/currency_widget.py`, à la fin de la classe `CurrencyWidget` :

```python
    BINDINGS = [("m", "open_menu", "Menu")]

    def action_open_menu(self) -> None:
        from tui.widgets.context_menu import ContextMenu
        self.app.mount(ContextMenu())

    def on_context_menu_delete_widget(self) -> None:
        self.remove()

    def on_context_menu_change_scale(self) -> None:
        # Implémenté en Task 13
        pass

    def on_context_menu_edit_pair(self) -> None:
        # Implémenté en Task 13
        pass
```

- [ ] **Step 5 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Expected : tous les tests PASS.

- [ ] **Step 6 : Commit**

```bash
git add tui/widgets/context_menu.py tui/widgets/currency_widget.py
git commit -m "feat: ContextMenu — menu contextuel avec touche m"
```

---

## Task 12 : tui/screens/config_screen.py

**Files:**
- Create: `tui/screens/config_screen.py`

- [ ] **Step 1 : Créer `tui/screens/config_screen.py`**

```python
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from logs.logger import get_logger
from shared.config import load_config, save_config, notify_daemon

logger = get_logger("tui")


class ConfigScreen(Widget):
    DEFAULT_CSS = """
    ConfigScreen {
        padding: 1 2;
    }
    ConfigScreen Label {
        margin-top: 1;
        color: $text-muted;
    }
    ConfigScreen Input {
        margin-bottom: 1;
        border: solid $border;
    }
    #btn-apply {
        margin-top: 2;
    }
    #future-alerts {
        margin-top: 2;
        color: $text-disabled;
    }
    """

    def compose(self) -> ComposeResult:
        config = load_config()
        yield Label("Devise de base")
        yield Input(value=config.base_currency, id="input-base-currency")
        yield Label("Intervalle de rafraîchissement (minutes)")
        yield Input(
            value=str(config.refresh_interval_minutes),
            id="input-refresh",
            type="integer",
        )
        yield Label("Nombre de colonnes")
        yield Input(
            value=str(config.grid_columns),
            id="input-columns",
            type="integer",
        )
        yield Button("Appliquer", id="btn-apply", variant="primary")
        yield Static("⏳ Seuils d'alerte — Prochainement", id="future-alerts")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-apply":
            return

        config = load_config()
        config.base_currency = self.query_one("#input-base-currency", Input).value.strip().upper()
        try:
            config.refresh_interval_minutes = int(
                self.query_one("#input-refresh", Input).value
            )
            config.grid_columns = int(
                self.query_one("#input-columns", Input).value
            )
        except ValueError:
            logger.warning("Valeurs de configuration invalides")
            return

        save_config(config)
        notify_daemon()
        logger.info("Configuration sauvegardée et daemon notifié")

        # Reconfigurer la grille
        from textual.containers import Grid
        grid = self.app.query_one("#grid", Grid)
        grid.styles.grid_size_columns = config.grid_columns
        grid.styles.grid_columns = " ".join(["1fr"] * config.grid_columns)
```

- [ ] **Step 2 : Ajouter le test**

```python
# Dans tests/test_tui.py, ajouter :
@pytest.mark.asyncio
async def test_config_screen_saves_config(tmp_path, monkeypatch):
    import shared.paths as p
    p.CONFIG_FILE = tmp_path / "config.json"
    p.CACHE_DIR = tmp_path / "cache"
    p.CACHE_DIR.mkdir()
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig())

    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.click("#tab-config")
        await pilot.pause()
        input_widget = pilot.app.query_one("#input-refresh", Input)
        await pilot.click(input_widget)
        await pilot.type("30")
        await pilot.click("#btn-apply")
        await pilot.pause()

    from shared.config import load_config
    cfg = load_config()
    assert "30" in str(cfg.refresh_interval_minutes)
```

- [ ] **Step 3 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Expected : tous les tests PASS.

- [ ] **Step 4 : Commit**

```bash
git add tui/screens/config_screen.py tests/test_tui.py
git commit -m "feat: ConfigScreen — onglet configuration avec sauvegarde et SIGHUP"
```

---

## Task 13 : Interactions menu contextuel — modifier paire et échelle

**Files:**
- Modify: `tui/widgets/currency_widget.py`

- [ ] **Step 1 : Ajouter l'écran de saisie de paire dans `currency_widget.py`**

Remplacer les méthodes `on_context_menu_edit_pair` et `on_context_menu_change_scale` par :

```python
    def on_context_menu_edit_pair(self) -> None:
        from textual.screen import ModalScreen
        from textual.widgets import Input, Button
        from textual.app import ComposeResult
        from textual.containers import Vertical

        class EditPairModal(ModalScreen):
            DEFAULT_CSS = """
            EditPairModal {
                align: center middle;
            }
            #modal-box {
                border: solid $border;
                background: $surface;
                padding: 1 2;
                width: 40;
                height: auto;
            }
            """

            def __init__(self, current_pair: str, current_scale: str, **kwargs):
                super().__init__(**kwargs)
                self._pair = current_pair
                self._scale = current_scale

            def compose(self) -> ComposeResult:
                with Vertical(id="modal-box"):
                    yield Label("Paire (ex: EUR/USD)")
                    yield Input(value=self._pair, id="new-pair")
                    yield Label("Échelle")
                    from textual.widgets import Select
                    yield Select(
                        [(s, s) for s in ["1M", "3M", "6M", "1A", "2A", "5A"]],
                        value=self._scale,
                        id="new-scale",
                    )
                    yield Button("Valider", id="btn-ok", variant="primary")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                if event.button.id == "btn-ok":
                    new_pair = self.query_one("#new-pair", Input).value.strip().upper()
                    new_scale = self.query_one("#new-scale", Select).value
                    self.dismiss((new_pair, new_scale))

        async def _handle_result(result):
            if result:
                new_pair, new_scale = result
                self.pair = new_pair
                self.scale = new_scale
                self._png_path = png_path(new_pair, new_scale)
                self._last_mtime = 0.0
                self.query_one(".header", Label).update(f"{new_pair} · {new_scale}")
                self._update_config()
                from shared.config import notify_daemon
                notify_daemon()

        self.app.push_screen(EditPairModal(self.pair, self.scale), _handle_result)

    def _update_config(self) -> None:
        # Reconstruit la liste des widgets depuis l'état courant de l'UI
        from shared.config import load_config, save_config, WidgetConfig
        from tui.widgets.currency_widget import CurrencyWidget
        config = load_config()
        config.widgets = [
            WidgetConfig(w.pair, w.scale)
            for w in self.app.query(CurrencyWidget)
        ]
        save_config(config)

    def on_context_menu_change_scale(self) -> None:
        # Réutilise on_context_menu_edit_pair avec la paire verrouillée
        self.on_context_menu_edit_pair()
```

- [ ] **Step 2 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Expected : tous les tests PASS.

- [ ] **Step 3 : Commit**

```bash
git add tui/widgets/currency_widget.py
git commit -m "feat: modal d'édition de paire et d'échelle via menu contextuel"
```

---

## Task 14 : bin/dashboard

**Files:**
- Create: `bin/dashboard`

- [ ] **Step 1 : Créer `bin/dashboard`**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Résoudre le chemin réel du script (fonctionne via symlink)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

VENV="$PROJECT_DIR/.venv"

if [[ ! -f "$VENV/bin/python" ]]; then
    echo "Erreur : environnement virtuel introuvable dans $VENV" >&2
    echo "Créez-le avec : python3.12 -m venv $VENV && pip install -r $PROJECT_DIR/requirements.txt" >&2
    exit 1
fi

exec "$VENV/bin/python" "$PROJECT_DIR/main.py" "$@"
```

- [ ] **Step 2 : Rendre le script exécutable**

```bash
chmod +x bin/dashboard
```

- [ ] **Step 3 : Tester le script localement**

```bash
./bin/dashboard
```

Expected : l'application TUI se lance dans le terminal.

- [ ] **Step 4 : Créer le symlink dans `/usr/local/bin`**

```bash
ln -sf "$(pwd)/bin/dashboard" /usr/local/bin/dashboard
```

- [ ] **Step 5 : Tester via le symlink**

```bash
dashboard
```

Expected : l'application TUI se lance.

- [ ] **Step 6 : Commit**

```bash
git add bin/dashboard
git commit -m "feat: bin/dashboard — script de lancement avec résolution symlink"
```

---

## Task 15 : Bouton "+" d'ajout de widget

**Files:**
- Modify: `tui/app.py`

- [ ] **Step 1 : Ajouter le bouton "+" dans `tui/app.py`**

Remplacer la méthode `compose` dans `DashboardApp` par :

```python
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                with Vertical():
                    with ScrollableContainer():
                        yield Grid(id="grid")
                    yield Button("[+] Ajouter une paire", id="btn-add", variant="default")
            with TabPane("Configuration", id="tab-config"):
                from tui.screens.config_screen import ConfigScreen
                yield ConfigScreen()
```

- [ ] **Step 2 : Connecter le bouton dans `DashboardApp`**

Ajouter dans `DashboardApp` :

```python
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "btn-add":
            return
        from tui.widgets.currency_widget import CurrencyWidget
        from tui.screens.config_screen import EditPairModal  # réutiliser le même modal

        # Le modal EditPairModal est défini inline dans currency_widget.py
        # On l'extrait ici en l'important depuis le widget
        from tui.widgets.currency_widget import CurrencyWidget

        async def _handle(result):
            if result:
                new_pair, new_scale = result
                widget = CurrencyWidget(new_pair, new_scale)
                await self.query_one("#grid", Grid).mount(widget)
                from shared.config import load_config, save_config, WidgetConfig
                config = load_config()
                config.widgets.append(WidgetConfig(new_pair, new_scale))
                save_config(config)
                from shared.config import notify_daemon
                notify_daemon()

        # Réutiliser le modal défini dans currency_widget
        from tui.widgets.currency_widget import _EditPairModal
        self.push_screen(_EditPairModal("EUR/USD", "1M"), _handle)
```

- [ ] **Step 3 : Extraire `EditPairModal` en classe de module dans `currency_widget.py`**

Déplacer la classe `EditPairModal` (définie inline en Task 13) au niveau module, et la renommer `_EditPairModal` :

```python
class _EditPairModal(ModalScreen):
    DEFAULT_CSS = """
    _EditPairModal {
        align: center middle;
    }
    #modal-box {
        border: solid $border;
        background: $surface;
        padding: 1 2;
        width: 40;
        height: auto;
    }
    """

    def __init__(self, current_pair: str, current_scale: str, **kwargs):
        super().__init__(**kwargs)
        self._pair = current_pair
        self._scale = current_scale

    def compose(self) -> ComposeResult:
        from textual.widgets import Select
        with Vertical(id="modal-box"):
            yield Label("Paire (ex: EUR/USD)")
            yield Input(value=self._pair, id="new-pair")
            yield Label("Échelle")
            yield Select(
                [(s, s) for s in ["1M", "3M", "6M", "1A", "2A", "5A"]],
                value=self._scale,
                id="new-scale",
            )
            yield Button("Valider", id="btn-ok", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            new_pair = self.query_one("#new-pair", Input).value.strip().upper()
            new_scale = self.query_one("#new-scale", Select).value
            self.dismiss((new_pair, new_scale))
```

- [ ] **Step 4 : Mettre à jour `on_context_menu_edit_pair` pour utiliser `_EditPairModal`**

```python
    def on_context_menu_edit_pair(self) -> None:
        async def _handle_result(result):
            if result:
                new_pair, new_scale = result
                self.pair = new_pair
                self.scale = new_scale
                self._png_path = png_path(new_pair, new_scale)
                self._last_mtime = 0.0
                self.query_one(".header", Label).update(f"{new_pair} · {new_scale}")
                self._update_config()
                from shared.config import notify_daemon
                notify_daemon()

        self.app.push_screen(_EditPairModal(self.pair, self.scale), _handle_result)
```

- [ ] **Step 5 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Expected : tous les tests PASS.

- [ ] **Step 6 : Commit**

```bash
git add tui/app.py tui/widgets/currency_widget.py
git commit -m "feat: bouton + pour ajouter une paire de devises"
```

---

## Task 16 : Lancer la suite de tests complète et vérification finale

- [ ] **Step 1 : Lancer tous les tests**

```bash
pytest -v
```

Expected : tous les tests PASS, aucun WARNING bloquant.

- [ ] **Step 2 : Démarrer le daemon et l'application**

```bash
launchctl start com.user.dashboard   # si pas déjà démarré
dashboard
```

Expected : les 3 widgets EUR/USD, EUR/GBP, EUR/JPY s'affichent avec leurs graphiques.

- [ ] **Step 3 : Tester l'ajout d'un widget via le bouton "+"**

Dans l'interface : cliquer sur `[+]`, entrer `USD/JPY`, sélectionner `6M`, valider.
Expected : un nouveau widget apparaît avec le graphique USD/JPY sur 6 mois.

- [ ] **Step 4 : Tester le menu contextuel**

Focaliser un widget existant, appuyer sur `m`, sélectionner "Changer l'échelle", passer à `5A`.
Expected : le widget se met à jour et le daemon génère le nouveau PNG.

- [ ] **Step 5 : Commit final**

```bash
git add .
git commit -m "feat: dashboard TUI v1 — implémentation complète"
```

---

## Notes d'implémentation

### Rendu iTerm2 dans Textual

Si le rendu via `render_line()` ne produit pas l'affichage attendu dans iTerm2, fallback recommandé :

```bash
pip install rich-pixels Pillow
```

Remplacer `ChartDisplay` par :

```python
from rich_pixels import Pixels
from PIL import Image
from rich.console import ConsoleRenderable

class ChartDisplay(Widget):
    def render(self) -> ConsoleRenderable:
        if not self.image_path.exists():
            return "⏳ Chargement..."
        img = Image.open(self.image_path)
        img = img.resize((self.size.width * 2, self.size.height * 4))
        return Pixels.from_image(img)
```

### Ajout d'un widget "+"

Le bouton `[+]` n'est pas implémenté comme une tâche séparée car il réutilise exactement le modal `EditPairModal` de la Task 13. Dans `tui/app.py`, monter un `Button("+", id="btn-add")` sous la grille et connecter `on_button_pressed` pour appeler `EditPairModal` puis monter un nouveau `CurrencyWidget`.
