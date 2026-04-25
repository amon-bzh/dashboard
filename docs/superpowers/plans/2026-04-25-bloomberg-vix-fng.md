# Bloomberg Theme + VIX + F&G Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Appliquer le thème Bloomberg au dashboard Textual, supprimer `terminal_cell_ratio`, améliorer la navigation clavier, et ajouter les onglets VIX (yfinance) et F&G (alternative.me).

**Architecture:** Thème Textual défini dans `tui/theme.py` et enregistré au `on_mount`. Les données VIX/F&G suivent le même pipeline que les devises (fetcher → renderer → PNG+JSON → widget → `refresh_if_updated`). Chaque nouveau widget hérite du `ChartDisplay` existant et s'inscrit dans la boucle `_poll_cache` de l'app.

**Tech Stack:** Textual ≥0.80.0, yfinance ≥0.2.50, httpx (déjà présent), matplotlib (déjà présent), alternative.me API (gratuit, sans clé).

---

## Fichiers concernés

| Action | Fichier | Rôle |
|--------|---------|------|
| Créer | `tui/theme.py` | Thème Bloomberg (palette + variables CSS) |
| Créer | `daemon/vix_fetcher.py` | Fetch VIX via yfinance (`^VIX`) |
| Créer | `daemon/vix_renderer.py` | Render PNG VIX (Bloomberg palette) |
| Créer | `tui/widgets/vix_widget.py` | Widget VIX (ChartDisplay + stats) |
| Créer | `daemon/fng_fetcher.py` | Fetch F&G via alternative.me |
| Créer | `daemon/fng_renderer.py` | Render PNG F&G historique 30j |
| Créer | `tui/widgets/fng_widget.py` | Widget F&G (ChartDisplay + valeur/classification) |
| Créer | `tests/test_vix_fetcher.py` | Tests VIX fetcher (mocks) |
| Créer | `tests/test_vix_renderer.py` | Tests VIX renderer |
| Créer | `tests/test_fng_fetcher.py` | Tests F&G fetcher (mocks) |
| Créer | `tests/test_fng_renderer.py` | Tests F&G renderer |
| Modifier | `requirements.txt` | Ajouter `yfinance` |
| Modifier | `shared/config.py` | Supprimer `terminal_cell_ratio` + rétrocompat |
| Modifier | `shared/paths.py` | Ajouter `vix_png_path()` + `fng_png_path()` |
| Modifier | `main.py` | Supprimer CSI16t + simplifier `_compute_widget_height` |
| Modifier | `tui/app.py` | Thème Bloomberg, onglets VIX+F&G, supprimer `cell_ratio` |
| Modifier | `tui/widgets/currency_widget.py` | Touches `k`+`Tab`+`Shift+Tab`, simplifier `_write_image` |
| Modifier | `tui/screens/config_screen.py` | Supprimer champ `terminal_cell_ratio` |
| Modifier | `daemon/renderer.py` | Palette Bloomberg |
| Modifier | `tests/test_config.py` | Adapter aux nouvelles règles de `DashboardConfig` |
| Modifier | `tests/test_tui.py` | Ajouter tests VIX/F&G, `k`, Tab, adapter config test |

---

## Task 1 : Thème Bloomberg

**Files:**
- Create: `tui/theme.py`
- Modify: `tui/app.py`
- Modify: `daemon/renderer.py`
- Test: `tests/test_tui.py`

- [ ] **Step 1 : Écrire le test (app démarre avec thème bloomberg)**

```python
# tests/test_tui.py — ajouter ce test
@pytest.mark.asyncio
async def test_app_uses_bloomberg_theme():
    app = DashboardApp()
    async with app.run_test() as pilot:
        assert pilot.app.theme == "bloomberg"
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
cd /Users/Antoine/Developer/dashboard && source .venv/bin/activate
pytest tests/test_tui.py::test_app_uses_bloomberg_theme -v
```

Résultat attendu : `FAILED` (AssertionError car le thème n'est pas encore défini)

- [ ] **Step 3 : Créer `tui/theme.py`**

```python
# tui/theme.py
from textual.theme import Theme

BLOOMBERG = Theme(
    name="bloomberg",
    primary="#ffb020",
    secondary="#22d3ee",
    accent="#22d3ee",
    background="#05070a",
    surface="#0a0d12",
    panel="#05070a",
    warning="#f97316",
    error="#ef4444",
    success="#4ade80",
    dark=True,
    variables={
        "border": "#6b6355",
        "text-muted": "#6b6355",
        "text-disabled": "#3a3530",
    }
)
```

- [ ] **Step 4 : Mettre à jour `tui/app.py` — enregistrer le thème Bloomberg**

Remplacer :
```python
CSS = """
Screen {
    layers: base overlay;
    background: #1a1a2e;
}
```

Par :
```python
CSS = """
Screen {
    layers: base overlay;
    color: #c9bfa8;
}
```

Et dans `__init__` (après `super().__init__(**kwargs)`) :
```python
def __init__(self, widget_height: int = 22, cell_ratio: float = 0.477, **kwargs) -> None:
    super().__init__(**kwargs)
    self._widget_height = widget_height
    self.cell_ratio = cell_ratio
    logger.debug(f"DashboardApp widget_height={widget_height} cell_ratio={cell_ratio:.4f}")
```

Dans `on_mount`, avant `self._load_widgets()` :
```python
def on_mount(self) -> None:
    from tui.theme import BLOOMBERG
    self.register_theme(BLOOMBERG)
    self.theme = "bloomberg"
    self._load_widgets()
    self.set_interval(5, self._poll_cache)
    self.call_after_refresh(self._poll_cache)
    logger.info("TUI démarré")
```

- [ ] **Step 5 : Mettre à jour la palette dans `daemon/renderer.py`**

Remplacer les constantes au début :
```python
_BG = "#05070a"
_GREEN = "#4ade80"
_RED = "#ef4444"
_GRID = "#6b6355"
_TICK = "#c9bfa8"
```

Et dans `_write_image` de `currency_widget.py`, la couleur de fond pour effacer l'ancienne zone :
- Chercher `"\x1b[48;2;26;26;46m"` (RGB 26,26,46 = #1a1a2e)
- Remplacer par `"\x1b[48;2;5;7;10m"` (RGB 5,7,10 = #05070a)

- [ ] **Step 6 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Résultat attendu : `test_app_uses_bloomberg_theme PASSED` + tous les tests existants verts.

- [ ] **Step 7 : Commit**

```bash
git add tui/theme.py tui/app.py daemon/renderer.py tui/widgets/currency_widget.py tests/test_tui.py
git commit -m "feat: thème Bloomberg (palette #05070a/amber/cyan)"
```

---

## Task 2 : Nettoyage terminal_cell_ratio

**Files:**
- Modify: `shared/config.py`
- Modify: `tui/app.py`
- Modify: `tui/widgets/currency_widget.py`
- Modify: `tui/screens/config_screen.py`
- Modify: `main.py`
- Modify: `tests/test_config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1 : Écrire le test de rétrocompatibilité**

```python
# tests/test_config.py — ajouter ce test
import json
def test_load_config_drops_terminal_cell_ratio(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    old = {
        "base_currency": "EUR",
        "refresh_interval_minutes": 60,
        "terminal_cell_ratio": 0.477,
        "widgets": [],
    }
    (tmp_path / "config.json").write_text(json.dumps(old))
    from shared.config import load_config
    cfg = load_config()
    assert cfg.base_currency == "EUR"
    assert not hasattr(cfg, "terminal_cell_ratio")
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
pytest tests/test_config.py::test_load_config_drops_terminal_cell_ratio -v
```

Résultat attendu : `FAILED` (TypeError : argument inattendu `terminal_cell_ratio`)

- [ ] **Step 3 : Mettre à jour `shared/config.py`**

Remplacer la dataclass et `load_config` :

```python
@dataclass
class DashboardConfig:
    base_currency: str = "EUR"
    refresh_interval_minutes: int = 60
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
    data.pop("grid_columns", None)
    data.pop("terminal_cell_ratio", None)  # rétrocompatibilité : champ supprimé
    widgets = [WidgetConfig(**w) for w in data.pop("widgets", [])]
    return DashboardConfig(**data, widgets=widgets)
```

- [ ] **Step 4 : Mettre à jour `tui/app.py` — supprimer `cell_ratio`**

Remplacer le `__init__` :
```python
def __init__(self, widget_height: int = 22, **kwargs) -> None:
    super().__init__(**kwargs)
    self._widget_height = widget_height
    logger.debug(f"DashboardApp widget_height={widget_height}")
```

- [ ] **Step 5 : Mettre à jour `tui/widgets/currency_widget.py` — simplifier `_write_image`**

Dans la méthode `_write_image`, remplacer le bloc de calcul `display_h` :

```python
# Avant :
ratio = getattr(self.app, "cell_ratio", 0.477)
display_h_exact = w * ratio / (8 / 3)
display_h = max(1, min(h, math.ceil(display_h_exact)))
logger.debug(
    f"[cadre] {self.image_path.name} : "
    f"ChartDisplay={w}×{h}  ratio={ratio:.4f}  "
    f"display_h_exact={display_h_exact:.2f}  display_h={display_h}"
)

# Après :
display_h = h
```

Supprimer également `import math` en haut du fichier (plus utilisé).

Mettre à jour la couleur d'effacement (déjà fait Task 1) — vérifier que c'est `"\x1b[48;2;5;7;10m"`.

- [ ] **Step 6 : Mettre à jour `tui/screens/config_screen.py` — supprimer le champ cell-ratio**

Remplacer `compose()` entier :
```python
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
    yield Button("Appliquer", id="btn-apply", variant="primary")
    yield Button("🗑 Purger la base de données", id="btn-purge", variant="error")
    yield Static("", id="purge-status")
    yield Static("⏳ Seuils d'alerte — Prochainement", id="future-alerts")
```

Remplacer `_apply_config()` :
```python
def _apply_config(self) -> None:
    config = load_config()
    config.base_currency = self.query_one("#input-base-currency", Input).value.strip().upper()
    try:
        config.refresh_interval_minutes = int(
            self.query_one("#input-refresh", Input).value
        )
    except ValueError:
        logger.warning("Valeurs de configuration invalides")
        return
    save_config(config)
    notify_daemon()
    logger.info("Configuration sauvegardée et daemon notifié")
```

Supprimer `#cell-ratio-hint` du DEFAULT_CSS.

- [ ] **Step 7 : Mettre à jour `main.py` — supprimer CSI16t et simplifier**

Remplacer tout le fichier par :
```python
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
```

- [ ] **Step 8 : Adapter le test `test_config_screen_saves_config`**

Dans `tests/test_tui.py`, le test `test_config_screen_saves_config` accède à `#input-cell-ratio` — supprimer cette référence. Le test reste valide en ne testant que `refresh_interval_minutes`.

```python
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
        input_widget.value = "30"
        await pilot.pause()
        from tui.screens.config_screen import ConfigScreen
        from textual.widgets import Button
        config_screen = pilot.app.query_one(ConfigScreen)
        btn = pilot.app.query_one("#btn-apply", Button)
        config_screen.on_button_pressed(Button.Pressed(btn))
        await pilot.pause()

    from shared.config import load_config
    cfg = load_config()
    assert str(cfg.refresh_interval_minutes) == "30"
```

- [ ] **Step 9 : Lancer tous les tests**

```bash
pytest -v
```

Résultat attendu : 23 tests verts (1 nouveau test ajouté).

- [ ] **Step 10 : Commit**

```bash
git add shared/config.py tui/app.py tui/widgets/currency_widget.py tui/screens/config_screen.py main.py tests/test_config.py tests/test_tui.py
git commit -m "refactor: supprimer terminal_cell_ratio, simplifier main.py"
```

---

## Task 3 : Navigation — touche k, Tab, Shift+Tab

**Files:**
- Modify: `tui/widgets/currency_widget.py`
- Modify: `tui/app.py`
- Test: `tests/test_tui.py`

- [ ] **Step 1 : Écrire les tests de navigation**

```python
# tests/test_tui.py — ajouter ces tests

@pytest.mark.asyncio
async def test_key_k_deletes_currency_widget(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from shared.config import DashboardConfig, WidgetConfig, save_config
    save_config(DashboardConfig(widgets=[
        WidgetConfig("EUR/USD", "1M"),
        WidgetConfig("EUR/GBP", "1M"),
    ]))
    from tui.widgets.currency_widget import CurrencyWidget
    from tui.widgets.gallery import WidgetGallery
    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        widgets = list(pilot.app.query(CurrencyWidget))
        assert len(widgets) == 2
        widgets[0].focus()
        await pilot.press("k")
        await pilot.pause()
        assert len(list(pilot.app.query(CurrencyWidget))) == 1


@pytest.mark.asyncio
async def test_tab_cycles_period_forward(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from shared.config import DashboardConfig, WidgetConfig, save_config
    save_config(DashboardConfig(widgets=[WidgetConfig("EUR/USD", "1M")]))
    from tui.widgets.currency_widget import CurrencyWidget
    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        w = pilot.app.query_one(CurrencyWidget)
        assert w.scale == "1M"
        w.focus()
        await pilot.press("tab")
        await pilot.pause()
        assert w.scale == "3M"
```

- [ ] **Step 2 : Vérifier que les tests échouent**

```bash
pytest tests/test_tui.py::test_key_k_deletes_currency_widget tests/test_tui.py::test_tab_cycles_period_forward -v
```

Résultat attendu : les 2 tests `FAILED`.

- [ ] **Step 3 : Mettre à jour `CurrencyWidget` dans `currency_widget.py`**

Remplacer le bloc BINDINGS :
```python
BINDINGS = [
    ("m", "open_menu", "Menu"),
    ("p", "cycle_period", "Période"),
    ("tab", "cycle_period", "Période suiv."),
    ("shift+tab", "cycle_period_back", "Période préc."),
    ("k", "delete_widget", "Supprimer"),
]
```

Ajouter les méthodes `action_cycle_period_back` et `action_delete_widget` après `action_cycle_period` :
```python
def action_cycle_period_back(self) -> None:
    try:
        idx = self._PERIODS.index(self.scale)
    except ValueError:
        idx = 0
    self.scale = self._PERIODS[(idx - 1) % len(self._PERIODS)]
    self._png_path = png_path(self.pair, self.scale)
    self._last_mtime = 0.0
    self.query_one(".header", Label).update(f"{self.pair} · {self.scale}")
    self._update_config()
    from shared.config import notify_daemon
    notify_daemon()

def action_delete_widget(self) -> None:
    self.post_message(CurrencyWidget.RequestDelete(self))
```

- [ ] **Step 4 : Retirer Tab/Shift+Tab des BINDINGS de `DashboardApp` dans `tui/app.py`**

```python
BINDINGS = [
    ("q", "quit", "Quitter"),
]
```

- [ ] **Step 5 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Résultat attendu : tous les tests verts.

- [ ] **Step 6 : Commit**

```bash
git add tui/widgets/currency_widget.py tui/app.py tests/test_tui.py
git commit -m "feat: touches k (supprimer), Tab/Shift+Tab (période) sur CurrencyWidget"
```

---

## Task 4 : VIX — fetcher + renderer + paths

**Files:**
- Modify: `requirements.txt`
- Create: `daemon/vix_fetcher.py`
- Create: `daemon/vix_renderer.py`
- Modify: `shared/paths.py`
- Create: `tests/test_vix_fetcher.py`
- Create: `tests/test_vix_renderer.py`

- [ ] **Step 1 : Ajouter yfinance à `requirements.txt`**

```
textual>=0.80.0
httpx>=0.27.0
matplotlib>=3.9.0
scipy>=1.13.0
python-dateutil>=2.9.0
yfinance>=0.2.50
```

Installer :
```bash
source .venv/bin/activate && pip install yfinance>=0.2.50
```

- [ ] **Step 2 : Ajouter `vix_png_path` à `shared/paths.py`**

Ajouter après `png_path` :
```python
def vix_png_path(scale: str) -> Path:
    return CACHE_DIR / f"VIX_{scale}.png"
```

- [ ] **Step 3 : Écrire les tests du fetcher VIX**

```python
# tests/test_vix_fetcher.py
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import date


@pytest.mark.asyncio
async def test_fetch_vix_returns_date_close_dict():
    df = pd.DataFrame(
        {"Close": [20.5, 21.0, 19.8]},
        index=pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06"])
    )
    df.index = pd.DatetimeIndex(df.index, tz="UTC")

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df

    with patch("daemon.vix_fetcher.yf.Ticker", return_value=mock_ticker):
        from daemon.vix_fetcher import fetch_vix
        result = await fetch_vix("1M")

    assert "2025-01-02" in result
    assert result["2025-01-02"] == pytest.approx(20.5)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_fetch_vix_raises_on_empty_dataframe():
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("daemon.vix_fetcher.yf.Ticker", return_value=mock_ticker):
        from daemon.vix_fetcher import fetch_vix
        with pytest.raises(ValueError, match="Aucune donnée VIX"):
            await fetch_vix("1M")


def test_vix_scales_keys():
    from daemon.vix_fetcher import SCALES
    assert set(SCALES.keys()) == {"1M", "3M", "6M", "1A"}
```

- [ ] **Step 4 : Vérifier que les tests échouent**

```bash
pytest tests/test_vix_fetcher.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'daemon.vix_fetcher'`

- [ ] **Step 5 : Créer `daemon/vix_fetcher.py`**

```python
# daemon/vix_fetcher.py
from __future__ import annotations

import asyncio
from typing import Dict

import yfinance as yf

SCALES: Dict[str, dict] = {
    "1M": {"period": "1mo", "interval": "1d"},
    "3M": {"period": "3mo", "interval": "1d"},
    "6M": {"period": "6mo", "interval": "1d"},
    "1A": {"period": "1y",  "interval": "1d"},
}


async def fetch_vix(scale: str) -> Dict[str, float]:
    """Retourne {date_iso: close} pour le VIX via Yahoo Finance."""
    if scale not in SCALES:
        raise ValueError(f"Échelle non supportée : {scale}. Valides : {list(SCALES)}")
    return await asyncio.to_thread(_fetch_vix_sync, scale)


def _fetch_vix_sync(scale: str) -> Dict[str, float]:
    params = SCALES[scale]
    df = yf.Ticker("^VIX").history(**params)
    if df.empty:
        raise ValueError(f"Aucune donnée VIX pour l'échelle {scale}")
    return {str(idx.date()): float(row["Close"]) for idx, row in df.iterrows()}
```

- [ ] **Step 6 : Écrire les tests du renderer VIX**

```python
# tests/test_vix_renderer.py
from pathlib import Path
import pytest
from daemon.vix_renderer import render_vix_chart, render_vix_error_chart

SAMPLE_VIX = {
    "2025-01-02": 18.5,
    "2025-01-03": 19.2,
    "2025-01-06": 17.8,
    "2025-01-07": 21.3,
    "2025-01-08": 20.1,
}

def _is_valid_png(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(8) == b"\x89PNG\r\n\x1a\n"

def test_render_vix_chart_creates_png(tmp_path):
    output = tmp_path / "vix.png"
    render_vix_chart(SAMPLE_VIX, "1M", output)
    assert output.exists()
    assert _is_valid_png(output)

def test_render_vix_chart_creates_json_meta(tmp_path):
    output = tmp_path / "vix.png"
    render_vix_chart(SAMPLE_VIX, "1M", output)
    import json
    meta = json.loads(output.with_suffix(".json").read_text())
    assert "current" in meta
    assert "variation_pct" in meta
    assert meta["current"] == pytest.approx(20.1, abs=0.01)

def test_render_vix_error_chart_creates_png(tmp_path):
    output = tmp_path / "vix_err.png"
    render_vix_error_chart("timeout", output)
    assert output.exists()
    assert _is_valid_png(output)
```

- [ ] **Step 7 : Vérifier que les tests échouent**

```bash
pytest tests/test_vix_renderer.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'daemon.vix_renderer'`

- [ ] **Step 8 : Créer `daemon/vix_renderer.py`**

```python
# daemon/vix_renderer.py
from __future__ import annotations

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Dict

_BG   = "#05070a"
_RED  = "#ef4444"
_GREEN = "#4ade80"
_GRID = "#6b6355"
_TICK = "#c9bfa8"
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
```

- [ ] **Step 9 : Lancer tous les tests VIX**

```bash
pytest tests/test_vix_fetcher.py tests/test_vix_renderer.py -v
```

Résultat attendu : 5 tests verts.

- [ ] **Step 10 : Commit**

```bash
git add requirements.txt shared/paths.py daemon/vix_fetcher.py daemon/vix_renderer.py tests/test_vix_fetcher.py tests/test_vix_renderer.py
git commit -m "feat: VIX fetcher (yfinance) + renderer Bloomberg"
```

---

## Task 5 : VIX — widget TUI + onglet

**Files:**
- Create: `tui/widgets/vix_widget.py`
- Modify: `tui/app.py`
- Test: `tests/test_tui.py`

- [ ] **Step 1 : Écrire le test du widget VIX**

```python
# tests/test_tui.py — ajouter

@pytest.mark.asyncio
async def test_vix_tab_mounts_vix_widget(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig(widgets=[]))
    from tui.widgets.vix_widget import VixWidget
    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.click("#tab-vix")
        await pilot.pause()
        assert pilot.app.query_one(VixWidget)
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
pytest tests/test_tui.py::test_vix_tab_mounts_vix_widget -v
```

Résultat attendu : `FAILED` (NoMatches ou ImportError)

- [ ] **Step 3 : Créer `tui/widgets/vix_widget.py`**

```python
# tui/widgets/vix_widget.py
from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from logs.logger import get_logger
from shared.paths import vix_png_path
from tui.widgets.currency_widget import ChartDisplay

logger = get_logger("tui")

_PERIODS = ["1M", "3M", "6M", "1A"]


class VixWidget(Widget):
    can_focus = True

    DEFAULT_CSS = """
    VixWidget {
        border: solid $border;
        height: 1fr;
        padding: 0;
    }
    VixWidget:focus {
        border: solid $primary;
    }
    VixWidget:focus .vix-header {
        color: $primary;
        text-style: bold;
    }
    .vix-header {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    .vix-rate {
        height: 1;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("p",         "cycle_period",      "Période"),
        ("tab",       "cycle_period",      "Période suiv."),
        ("shift+tab", "cycle_period_back", "Période préc."),
    ]

    def __init__(self, scale: str = "1M", **kwargs) -> None:
        super().__init__(**kwargs)
        self.scale = scale
        self._png_path = vix_png_path(scale)
        self._last_mtime: float = 0.0

    def compose(self) -> ComposeResult:
        yield Label(f"VIX · {self.scale}", classes="vix-header")
        yield Label("— / —%", id=f"vix-rate-{id(self)}", classes="vix-rate")
        yield ChartDisplay(self._png_path, id=f"vix-chart-{id(self)}")

    def refresh_if_updated(self) -> None:
        if not self._png_path.exists():
            return
        mtime = self._png_path.stat().st_mtime
        if mtime > self._last_mtime:
            self._last_mtime = mtime
            self.query_one(ChartDisplay).refresh_chart()
            self._refresh_rate_label()

    def _refresh_rate_label(self) -> None:
        meta_path = self._png_path.with_suffix(".json")
        if not meta_path.exists():
            return
        try:
            meta = json.loads(meta_path.read_text())
            current = float(meta["current"])
            variation = meta.get("variation_pct", 0.0)
            regime = meta.get("regime", "")
            sign = "+" if variation >= 0 else ""
            color = "red" if variation >= 0 else "green"
            label = self.query_one(f"#vix-rate-{id(self)}", Label)
            label.update(f"{current:.2f}  [{color}]{sign}{variation:.2f}%[/]  {regime}")
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug(f"VixWidget label: {exc}")

    def action_cycle_period(self) -> None:
        try:
            idx = _PERIODS.index(self.scale)
        except ValueError:
            idx = -1
        self.scale = _PERIODS[(idx + 1) % len(_PERIODS)]
        self._png_path = vix_png_path(self.scale)
        self._last_mtime = 0.0
        self.query_one(".vix-header", Label).update(f"VIX · {self.scale}")
        self.refresh_if_updated()

    def action_cycle_period_back(self) -> None:
        try:
            idx = _PERIODS.index(self.scale)
        except ValueError:
            idx = 0
        self.scale = _PERIODS[(idx - 1) % len(_PERIODS)]
        self._png_path = vix_png_path(self.scale)
        self._last_mtime = 0.0
        self.query_one(".vix-header", Label).update(f"VIX · {self.scale}")
        self.refresh_if_updated()
```

- [ ] **Step 4 : Ajouter l'onglet VIX dans `tui/app.py`**

Dans `compose()`, après le TabPane "Configuration" et avant le `yield Footer()` :
```python
with TabPane("VIX", id="tab-vix"):
    from tui.widgets.vix_widget import VixWidget
    yield VixWidget(scale="1M", id="vix-widget")
```

Dans `_poll_cache()`, ajouter le polling VIX :
```python
async def _poll_cache(self) -> None:
    from tui.widgets.currency_widget import CurrencyWidget
    from tui.widgets.vix_widget import VixWidget
    for widget in self.query(CurrencyWidget):
        widget.refresh_if_updated()
    for widget in self.query(VixWidget):
        widget.refresh_if_updated()
```

Dans `_do_fetch_all()`, ajouter le fetch VIX (toutes les échelles) :
```python
async def _do_fetch_all(self) -> None:
    config = load_config()
    status = self.query_one("#fetch-status", Label)
    pairs = config.widgets
    status.update(f"⏳ Chargement de {len(pairs)} paire(s) + VIX + F&G...")
    for i, w in enumerate(pairs, 1):
        status.update(f"⏳ {w.pair} {w.scale} ({i}/{len(pairs)})...")
        await self._do_fetch(w.pair, w.scale)
    status.update("⏳ VIX...")
    await self._do_fetch_vix()
    status.update("✓ Données à jour")
    self.set_timer(3, lambda: status.update(""))
```

Ajouter la méthode `_do_fetch_vix()` :
```python
async def _do_fetch_vix(self) -> None:
    from daemon.vix_fetcher import fetch_vix, SCALES as VIX_SCALES
    from daemon.vix_renderer import render_vix_chart, render_vix_error_chart
    from shared.paths import vix_png_path
    for scale in VIX_SCALES:
        path = vix_png_path(scale)
        try:
            rates = await fetch_vix(scale)
            render_vix_chart(rates, scale, path)
            logger.info(f"VIX {scale} chargé")
        except Exception as exc:
            logger.error(f"Échec VIX {scale}: {exc}")
            render_vix_error_chart(str(exc), path)
```

- [ ] **Step 5 : Lancer les tests**

```bash
pytest tests/test_tui.py -v
```

Résultat attendu : tous les tests verts.

- [ ] **Step 6 : Commit**

```bash
git add tui/widgets/vix_widget.py tui/app.py tests/test_tui.py
git commit -m "feat: onglet VIX (widget + polling + fetch)"
```

---

## Task 6 : F&G — fetcher + renderer + paths

**Files:**
- Modify: `shared/paths.py`
- Create: `daemon/fng_fetcher.py`
- Create: `daemon/fng_renderer.py`
- Create: `tests/test_fng_fetcher.py`
- Create: `tests/test_fng_renderer.py`

- [ ] **Step 1 : Ajouter `fng_png_path` à `shared/paths.py`**

Ajouter après `vix_png_path` :
```python
def fng_png_path() -> Path:
    return CACHE_DIR / "FNG.png"
```

- [ ] **Step 2 : Écrire les tests du fetcher F&G**

```python
# tests/test_fng_fetcher.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_fetch_fng_returns_structured_dict():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"value": "72", "value_classification": "Greed",   "timestamp": "1714953600"},
            {"value": "68", "value_classification": "Greed",   "timestamp": "1714867200"},
            {"value": "55", "value_classification": "Neutral", "timestamp": "1714780800"},
        ]
    }
    with patch("daemon.fng_fetcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        from daemon.fng_fetcher import fetch_fng
        result = await fetch_fng()

    assert result["current"] == 72
    assert result["classification"] == "Greed"
    assert isinstance(result["history"], dict)
    assert len(result["history"]) == 3


@pytest.mark.asyncio
async def test_fetch_fng_raises_on_http_error():
    with patch("daemon.fng_fetcher.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
        mock_cls.return_value = mock_client

        from daemon.fng_fetcher import fetch_fng
        with pytest.raises(Exception, match="connection refused"):
            await fetch_fng()
```

- [ ] **Step 3 : Vérifier que les tests échouent**

```bash
pytest tests/test_fng_fetcher.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'daemon.fng_fetcher'`

- [ ] **Step 4 : Créer `daemon/fng_fetcher.py`**

```python
# daemon/fng_fetcher.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import httpx

FNG_URL = "https://api.alternative.me/fng/"


async def fetch_fng(limit: int = 31) -> Dict[str, Any]:
    """Retourne {"current": int, "classification": str, "history": {date_iso: value}}.

    Source : alternative.me Crypto Fear & Greed Index (gratuit, sans clé API).
    Les données sont ordonnées du plus récent au plus ancien.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(FNG_URL, params={"limit": limit, "format": "json"})
        resp.raise_for_status()
        data = resp.json()["data"]

    history = {}
    for entry in data:
        ts = int(entry["timestamp"])
        d = str(datetime.fromtimestamp(ts).date())
        history[d] = int(entry["value"])

    newest = data[0]
    return {
        "current": int(newest["value"]),
        "classification": newest["value_classification"],
        "history": history,
    }
```

- [ ] **Step 5 : Écrire les tests du renderer F&G**

```python
# tests/test_fng_renderer.py
from pathlib import Path
import pytest
from daemon.fng_renderer import render_fng_chart, render_fng_error_chart

SAMPLE_FNG = {
    "current": 72,
    "classification": "Greed",
    "history": {
        f"2025-01-{str(i).zfill(2)}": 50 + i
        for i in range(2, 32)
    },
}

def _is_valid_png(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(8) == b"\x89PNG\r\n\x1a\n"

def test_render_fng_chart_creates_png(tmp_path):
    output = tmp_path / "fng.png"
    render_fng_chart(SAMPLE_FNG, output)
    assert output.exists()
    assert _is_valid_png(output)

def test_render_fng_chart_creates_json_meta(tmp_path):
    output = tmp_path / "fng.png"
    render_fng_chart(SAMPLE_FNG, output)
    import json
    meta = json.loads(output.with_suffix(".json").read_text())
    assert meta["current"] == 72
    assert meta["classification"] == "Greed"
    assert "variation_7d" in meta

def test_render_fng_error_chart_creates_png(tmp_path):
    output = tmp_path / "fng_err.png"
    render_fng_error_chart("timeout", output)
    assert output.exists()
    assert _is_valid_png(output)
```

- [ ] **Step 6 : Vérifier que les tests échouent**

```bash
pytest tests/test_fng_renderer.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'daemon.fng_renderer'`

- [ ] **Step 7 : Créer `daemon/fng_renderer.py`**

```python
# daemon/fng_renderer.py
from __future__ import annotations

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

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
```

- [ ] **Step 8 : Lancer tous les tests F&G**

```bash
pytest tests/test_fng_fetcher.py tests/test_fng_renderer.py -v
```

Résultat attendu : 5 tests verts.

- [ ] **Step 9 : Commit**

```bash
git add shared/paths.py daemon/fng_fetcher.py daemon/fng_renderer.py tests/test_fng_fetcher.py tests/test_fng_renderer.py
git commit -m "feat: F&G fetcher (alternative.me) + renderer Bloomberg"
```

---

## Task 7 : F&G — widget TUI + onglet

**Files:**
- Create: `tui/widgets/fng_widget.py`
- Modify: `tui/app.py`
- Test: `tests/test_tui.py`

- [ ] **Step 1 : Écrire le test du widget F&G**

```python
# tests/test_tui.py — ajouter

@pytest.mark.asyncio
async def test_fng_tab_mounts_fng_widget(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig(widgets=[]))
    from tui.widgets.fng_widget import FngWidget
    app = DashboardApp()
    async with app.run_test() as pilot:
        await pilot.click("#tab-fng")
        await pilot.pause()
        assert pilot.app.query_one(FngWidget)
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
pytest tests/test_tui.py::test_fng_tab_mounts_fng_widget -v
```

Résultat attendu : `FAILED` (ImportError ou NoMatches)

- [ ] **Step 3 : Créer `tui/widgets/fng_widget.py`**

```python
# tui/widgets/fng_widget.py
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
```

- [ ] **Step 4 : Ajouter l'onglet F&G dans `tui/app.py`**

Dans `compose()`, après le TabPane "VIX" :
```python
with TabPane("F&G", id="tab-fng"):
    from tui.widgets.fng_widget import FngWidget
    yield FngWidget(id="fng-widget")
```

Dans `_poll_cache()`, ajouter le polling F&G :
```python
async def _poll_cache(self) -> None:
    from tui.widgets.currency_widget import CurrencyWidget
    from tui.widgets.vix_widget import VixWidget
    from tui.widgets.fng_widget import FngWidget
    for widget in self.query(CurrencyWidget):
        widget.refresh_if_updated()
    for widget in self.query(VixWidget):
        widget.refresh_if_updated()
    for widget in self.query(FngWidget):
        widget.refresh_if_updated()
```

Dans `_do_fetch_all()`, ajouter le fetch F&G :
```python
async def _do_fetch_all(self) -> None:
    config = load_config()
    status = self.query_one("#fetch-status", Label)
    pairs = config.widgets
    status.update(f"⏳ {len(pairs)} paire(s) + VIX + F&G...")
    for i, w in enumerate(pairs, 1):
        status.update(f"⏳ {w.pair} {w.scale} ({i}/{len(pairs)})...")
        await self._do_fetch(w.pair, w.scale)
    status.update("⏳ VIX...")
    await self._do_fetch_vix()
    status.update("⏳ F&G...")
    await self._do_fetch_fng()
    status.update("✓ Données à jour")
    self.set_timer(3, lambda: status.update(""))
```

Ajouter la méthode `_do_fetch_fng()` :
```python
async def _do_fetch_fng(self) -> None:
    from daemon.fng_fetcher import fetch_fng
    from daemon.fng_renderer import render_fng_chart, render_fng_error_chart
    from shared.paths import fng_png_path
    path = fng_png_path()
    try:
        data = await fetch_fng()
        render_fng_chart(data, path)
        logger.info("F&G chargé")
    except Exception as exc:
        logger.error(f"Échec F&G: {exc}")
        render_fng_error_chart(str(exc), path)
```

- [ ] **Step 5 : Lancer tous les tests**

```bash
pytest -v
```

Résultat attendu : 29 tests verts (22 existants + 7 nouveaux).

- [ ] **Step 6 : Commit final**

```bash
git add tui/widgets/fng_widget.py tui/app.py tests/test_tui.py
git commit -m "feat: onglet F&G (alternative.me · widget + polling + fetch)"
```

---

## Vérification finale

```bash
pytest -v
# Attendu : 29 tests verts

source .venv/bin/activate && python -m main
# Vérifier visuellement : thème noir Bloomberg, touches k/Tab/p fonctionnelles,
# onglets VIX et F&G présents (affichent "⏳ Chargement..." jusqu'au premier fetch)
```

---

## Self-review

**Couverture des specs :**
- ✅ Thème Bloomberg — Task 1
- ✅ Suppression terminal_cell_ratio — Task 2
- ✅ Touche `k` pour supprimer une paire — Task 3
- ✅ Tab/Shift+Tab pour cycler les périodes — Task 3
- ✅ VIX (yfinance, gratuit) — Tasks 4+5
- ✅ F&G (alternative.me, gratuit) — Tasks 6+7
- ✅ Config screen conservée, simplifiée — Task 2
- ✅ Onglet Config conservé dans TabbedContent — Task 2 (pas touché, reste en place)
- ✅ VixWidget : Tab/Shift+Tab pour périodes — Task 5
- ✅ `_do_fetch_all` inclut VIX (toutes échelles) + F&G — Tasks 5+7
- ✅ `_poll_cache` inclut VixWidget + FngWidget — Tasks 5+7

**Vérification cohérence types :**
- `vix_png_path(scale: str) -> Path` : cohérent entre paths.py, vix_fetcher, vix_renderer, vix_widget
- `fng_png_path() -> Path` : cohérent entre paths.py, fng_fetcher, fng_renderer, fng_widget
- `fetch_vix(scale) -> Dict[str, float]` : cohérent fetcher ↔ renderer ↔ test
- `fetch_fng() -> Dict[str, Any]` avec clés `current`, `classification`, `history` : cohérent
- `VixWidget` importe `ChartDisplay` depuis `currency_widget` : correct
- `FngWidget` importe `ChartDisplay` depuis `currency_widget` : correct
