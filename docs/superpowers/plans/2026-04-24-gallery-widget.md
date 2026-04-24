# WidgetGallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le `Grid` Textual par une classe `WidgetGallery(VerticalScroll)` à 2 colonnes fixes, gérée par CSS, avec scroll vertical natif.

**Architecture:** `WidgetGallery` sous-classe `VerticalScroll` et contient des `GalleryRow(Horizontal)`, chaque rangée portant 2 `CurrencyWidget`. La hauteur des rangées est fixée programmatiquement à partir de `widget_height` calculé dans `main.py`. Le chargement initial passe par `load_widgets()` (sync, batch), l'ajout dynamique par `add_currency_widget()` (async). La suppression d'un widget déclenche `CurrencyWidget.RequestDelete` qui permet à la galerie de nettoyer les rangées vides.

**Tech Stack:** Python 3.12, Textual (`VerticalScroll`, `Horizontal`), pytest-asyncio

---

## Structure des fichiers

| Action | Fichier | Rôle |
|--------|---------|------|
| Créer | `tui/widgets/gallery.py` | Classes `GalleryRow` et `WidgetGallery` |
| Créer | `tests/test_gallery.py` | Tests unitaires de la galerie |
| Modifier | `tui/widgets/currency_widget.py` | Ajouter `RequestDelete`, modifier `on_context_menu_delete_widget` |
| Modifier | `tui/app.py` | Remplacer Grid par WidgetGallery |
| Modifier | `shared/config.py` | Retirer `grid_columns` |
| Modifier | `tests/test_tui.py` | Mettre à jour les références `#grid`/`Grid` |
| Modifier | `tests/test_config.py` | Retirer les assertions sur `grid_columns` |

---

### Task 1 : Créer `GalleryRow` avec hauteur fixe

**Files:**
- Create: `tui/widgets/gallery.py`
- Create: `tests/test_gallery.py`

- [ ] **Step 1 : Écrire le test**

Créer `tests/test_gallery.py` :

```python
import pytest
from textual.app import App, ComposeResult


@pytest.mark.asyncio
async def test_gallery_row_height_applied(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from tui.widgets.gallery import GalleryRow

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield GalleryRow(widget_height=12)

    async with TestApp().run_test() as pilot:
        row = pilot.app.query_one(GalleryRow)
        assert row.styles.height.value == 12
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
source .venv/bin/activate && pytest tests/test_gallery.py::test_gallery_row_height_applied -v
```

Résultat attendu : `FAILED` avec `ModuleNotFoundError` ou `ImportError`.

- [ ] **Step 3 : Créer `tui/widgets/gallery.py` avec `GalleryRow`**

```python
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll


class GalleryRow(Horizontal):
    DEFAULT_CSS = """
    GalleryRow {
        width: 1fr;
    }
    """

    def __init__(self, widget_height: int, widgets: list | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._widget_height = widget_height
        self._initial_widgets: list = widgets or []

    def compose(self) -> ComposeResult:
        yield from self._initial_widgets

    def on_mount(self) -> None:
        self.styles.height = self._widget_height


class WidgetGallery(VerticalScroll):
    DEFAULT_CSS = """
    WidgetGallery {
        width: 1fr;
        height: 1fr;
    }
    GalleryRow > CurrencyWidget {
        width: 1fr;
    }
    """

    def __init__(self, widget_height: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._widget_height = widget_height
```

- [ ] **Step 4 : Lancer le test pour vérifier qu'il passe**

```bash
pytest tests/test_gallery.py::test_gallery_row_height_applied -v
```

Résultat attendu : `PASSED`.

- [ ] **Step 5 : Commit**

```bash
git add tui/widgets/gallery.py tests/test_gallery.py
git commit -m "feat: ajouter GalleryRow avec hauteur fixe"
```

---

### Task 2 : `WidgetGallery.load_widgets` — chargement en lot

**Files:**
- Modify: `tui/widgets/gallery.py`
- Modify: `tests/test_gallery.py`

- [ ] **Step 1 : Écrire le test**

Ajouter à `tests/test_gallery.py` :

```python
@pytest.mark.asyncio
async def test_load_widgets_creates_rows(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from tui.widgets.gallery import GalleryRow, WidgetGallery
    from tui.widgets.currency_widget import CurrencyWidget

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield WidgetGallery(widget_height=12)

    async with TestApp().run_test() as pilot:
        gallery = pilot.app.query_one(WidgetGallery)
        gallery.load_widgets([
            CurrencyWidget("EUR/USD", "1M", widget_height=12),
            CurrencyWidget("GBP/USD", "1M", widget_height=12),
            CurrencyWidget("USD/JPY", "1M", widget_height=12),
        ])
        await pilot.pause()
        rows = list(gallery.query(GalleryRow))
        assert len(rows) == 2
        assert len(list(rows[0].query(CurrencyWidget))) == 2
        assert len(list(rows[1].query(CurrencyWidget))) == 1
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_gallery.py::test_load_widgets_creates_rows -v
```

Résultat attendu : `FAILED` avec `AttributeError: 'WidgetGallery' object has no attribute 'load_widgets'`.

- [ ] **Step 3 : Ajouter `load_widgets` et `all_currency_widgets` dans `WidgetGallery`**

Dans `tui/widgets/gallery.py`, ajouter les deux méthodes dans la classe `WidgetGallery` :

```python
    def load_widgets(self, widgets: list) -> None:
        """Charge un lot de CurrencyWidget en créant des rangées de 2."""
        rows = []
        for i in range(0, len(widgets), 2):
            rows.append(GalleryRow(widget_height=self._widget_height, widgets=widgets[i:i + 2]))
        if rows:
            self.mount(*rows)

    def all_currency_widgets(self) -> list:
        """Retourne tous les CurrencyWidget dans l'ordre DOM (ordre d'affichage)."""
        from tui.widgets.currency_widget import CurrencyWidget
        return list(self.query(CurrencyWidget))
```

- [ ] **Step 4 : Lancer le test pour vérifier qu'il passe**

```bash
pytest tests/test_gallery.py::test_load_widgets_creates_rows -v
```

Résultat attendu : `PASSED`.

- [ ] **Step 5 : Commit**

```bash
git add tui/widgets/gallery.py tests/test_gallery.py
git commit -m "feat: WidgetGallery.load_widgets — chargement en lot"
```

---

### Task 3 : `WidgetGallery.add_currency_widget` — ajout dynamique

**Files:**
- Modify: `tui/widgets/gallery.py`
- Modify: `tests/test_gallery.py`

- [ ] **Step 1 : Écrire le test**

Ajouter à `tests/test_gallery.py` :

```python
@pytest.mark.asyncio
async def test_add_currency_widget_fills_row_then_creates_new(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from tui.widgets.gallery import GalleryRow, WidgetGallery
    from tui.widgets.currency_widget import CurrencyWidget

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield WidgetGallery(widget_height=12)

    async with TestApp().run_test() as pilot:
        gallery = pilot.app.query_one(WidgetGallery)
        await gallery.add_currency_widget(CurrencyWidget("EUR/USD", "1M", widget_height=12))
        await gallery.add_currency_widget(CurrencyWidget("GBP/USD", "1M", widget_height=12))
        await gallery.add_currency_widget(CurrencyWidget("USD/JPY", "1M", widget_height=12))
        await pilot.pause()
        rows = list(gallery.query(GalleryRow))
        assert len(rows) == 2
        assert len(list(rows[0].query(CurrencyWidget))) == 2
        assert len(list(rows[1].query(CurrencyWidget))) == 1
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_gallery.py::test_add_currency_widget_fills_row_then_creates_new -v
```

Résultat attendu : `FAILED` avec `AttributeError`.

- [ ] **Step 3 : Ajouter `add_currency_widget` dans `WidgetGallery`**

Dans `tui/widgets/gallery.py`, ajouter dans la classe `WidgetGallery` :

```python
    async def add_currency_widget(self, widget) -> None:
        """Ajoute un widget dans la dernière rangée si dispo, sinon crée une nouvelle rangée."""
        rows = list(self.query(GalleryRow))
        if rows:
            last_row = rows[-1]
            from tui.widgets.currency_widget import CurrencyWidget
            if len(list(last_row.query(CurrencyWidget))) < 2:
                await last_row.mount(widget)
                return
        row = GalleryRow(widget_height=self._widget_height, widgets=[widget])
        await self.mount(row)
```

- [ ] **Step 4 : Lancer le test pour vérifier qu'il passe**

```bash
pytest tests/test_gallery.py::test_add_currency_widget_fills_row_then_creates_new -v
```

Résultat attendu : `PASSED`.

- [ ] **Step 5 : Lancer toute la suite pour vérifier aucune régression**

```bash
pytest tests/test_gallery.py -v
```

Résultat attendu : 3 tests `PASSED`.

- [ ] **Step 6 : Commit**

```bash
git add tui/widgets/gallery.py tests/test_gallery.py
git commit -m "feat: WidgetGallery.add_currency_widget — ajout dynamique async"
```

---

### Task 4 : `CurrencyWidget.RequestDelete` + nettoyage des rangées vides

**Files:**
- Modify: `tui/widgets/currency_widget.py`
- Modify: `tui/widgets/gallery.py`
- Modify: `tests/test_gallery.py`

- [ ] **Step 1 : Écrire le test**

Ajouter à `tests/test_gallery.py` :

```python
@pytest.mark.asyncio
async def test_empty_row_removed_after_widget_deletion(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from tui.widgets.gallery import GalleryRow, WidgetGallery
    from tui.widgets.currency_widget import CurrencyWidget

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield WidgetGallery(widget_height=12)

    async with TestApp().run_test() as pilot:
        gallery = pilot.app.query_one(WidgetGallery)
        w1 = CurrencyWidget("EUR/USD", "1M", widget_height=12)
        w2 = CurrencyWidget("GBP/USD", "1M", widget_height=12)
        w3 = CurrencyWidget("USD/JPY", "1M", widget_height=12)
        gallery.load_widgets([w1, w2, w3])
        await pilot.pause()
        # w3 est seul dans la rangée 2 — sa suppression doit effacer la rangée
        w3.post_message(CurrencyWidget.RequestDelete(w3))
        await pilot.pause()
        rows = list(gallery.query(GalleryRow))
        assert len(rows) == 1
        assert len(list(gallery.query(CurrencyWidget))) == 2
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/test_gallery.py::test_empty_row_removed_after_widget_deletion -v
```

Résultat attendu : `FAILED` avec `AttributeError: type object 'CurrencyWidget' has no attribute 'RequestDelete'`.

- [ ] **Step 3 : Ajouter `RequestDelete` dans `CurrencyWidget` et modifier `on_context_menu_delete_widget`**

Dans `tui/widgets/currency_widget.py`, ajouter dans la classe `CurrencyWidget` (après les imports de `Message`) :

En haut du fichier, ajouter l'import manquant si absent :
```python
from textual.message import Message
```

Dans la classe `CurrencyWidget`, ajouter la classe message et modifier le handler :

```python
    class RequestDelete(Message):
        """Demande à la galerie parente de supprimer ce widget et de nettoyer la rangée."""
        def __init__(self, widget: "CurrencyWidget") -> None:
            super().__init__()
            self.widget = widget

    def on_context_menu_delete_widget(self) -> None:
        self.post_message(CurrencyWidget.RequestDelete(self))
```

- [ ] **Step 4 : Ajouter le handler dans `WidgetGallery`**

Dans `tui/widgets/gallery.py`, ajouter dans la classe `WidgetGallery` :

```python
    def on_currency_widget_request_delete(self, event) -> None:
        """Supprime le widget et retire la rangée parente si elle devient vide."""
        widget = event.widget
        row = widget.parent
        from tui.widgets.currency_widget import CurrencyWidget
        is_last_in_row = isinstance(row, GalleryRow) and len(list(row.query(CurrencyWidget))) == 1
        widget.remove()
        if is_last_in_row:
            row.remove()
```

- [ ] **Step 5 : Lancer tous les tests de gallery pour vérifier**

```bash
pytest tests/test_gallery.py -v
```

Résultat attendu : 4 tests `PASSED`.

- [ ] **Step 6 : Commit**

```bash
git add tui/widgets/currency_widget.py tui/widgets/gallery.py tests/test_gallery.py
git commit -m "feat: CurrencyWidget.RequestDelete + nettoyage rangées vides dans WidgetGallery"
```

---

### Task 5 : Mettre à jour `app.py`

**Files:**
- Modify: `tui/app.py`
- Modify: `tests/test_tui.py`

- [ ] **Step 1 : Mettre à jour `test_tui.py`**

Dans `tests/test_tui.py`, remplacer `test_currency_widget_mounts` :

Remplacer :
```python
@pytest.mark.asyncio
async def test_currency_widget_mounts(tmp_path, monkeypatch):
    import shared.paths as p
    p.CACHE_DIR = tmp_path
    p.CONFIG_FILE = tmp_path / "config.json"
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig(widgets=[]))
    from tui.widgets.currency_widget import CurrencyWidget
    from textual.containers import Grid
    app = DashboardApp()
    async with app.run_test() as pilot:
        widget = CurrencyWidget("EUR/USD", "1M")
        await pilot.app.query_one("#grid", Grid).mount(widget)
        await pilot.pause()
        assert pilot.app.query_one(CurrencyWidget)
```

Par :
```python
@pytest.mark.asyncio
async def test_currency_widget_mounts(tmp_path, monkeypatch):
    import shared.paths as p
    p.CACHE_DIR = tmp_path
    p.CONFIG_FILE = tmp_path / "config.json"
    from shared.config import DashboardConfig, save_config
    save_config(DashboardConfig(widgets=[]))
    from tui.widgets.currency_widget import CurrencyWidget
    from tui.widgets.gallery import WidgetGallery
    app = DashboardApp()
    async with app.run_test() as pilot:
        widget = CurrencyWidget("EUR/USD", "1M")
        await pilot.app.query_one("#gallery", WidgetGallery).add_currency_widget(widget)
        await pilot.pause()
        assert pilot.app.query_one(CurrencyWidget)
```

- [ ] **Step 2 : Mettre à jour `app.py`**

Remplacer le contenu de `tui/app.py` par :

```python
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Footer, Label, TabbedContent, TabPane

from shared.config import load_config
from logs.logger import get_logger

logger = get_logger("tui")


class DashboardApp(App):
    BINDINGS = [
        ("tab", "focus_next", "Cadre suivant"),
        ("shift+tab", "focus_previous", "Cadre précédent"),
        ("q", "quit", "Quitter"),
    ]

    def __init__(self, widget_height: int = 22, cell_ratio: float = 0.477, **kwargs) -> None:
        super().__init__(**kwargs)
        self._widget_height = widget_height
        self.cell_ratio = cell_ratio
        logger.debug(f"DashboardApp widget_height={widget_height} cell_ratio={cell_ratio:.4f}")

    CSS = """
    Screen {
        layers: base overlay;
        background: #1a1a2e;
    }
    #bottom-bar {
        height: auto;
        padding: 0 1;
    }
    #btn-fetch {
        margin-left: 1;
    }
    #fetch-status {
        color: #00b4d8;
        height: 1;
        content-align: center middle;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Dashboard", id="tab-dashboard"):
                with Vertical():
                    from tui.widgets.gallery import WidgetGallery
                    yield WidgetGallery(self._widget_height, id="gallery")
                    with Horizontal(id="bottom-bar"):
                        yield Button("[+] Ajouter une paire", id="btn-add", variant="default")
                        yield Button("↻ Charger les données", id="btn-fetch", variant="default")
                        yield Label("", id="fetch-status")
            with TabPane("Configuration", id="tab-config"):
                from tui.screens.config_screen import ConfigScreen
                yield ConfigScreen()
        yield Footer()

    def on_mount(self) -> None:
        self._load_widgets()
        self.set_interval(5, self._poll_cache)
        logger.info("TUI démarré")

    def _load_widgets(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        from tui.widgets.gallery import WidgetGallery
        config = load_config()
        gallery = self.query_one("#gallery", WidgetGallery)
        gallery.load_widgets([
            CurrencyWidget(w.pair, w.scale, widget_height=self._widget_height)
            for w in config.widgets
        ])
        logger.debug(f"{len(config.widgets)} widgets chargés")


    async def _poll_cache(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget
        for widget in self.query(CurrencyWidget):
            widget.refresh_if_updated()

    def on_button_pressed(self, event) -> None:
        btn_id = event.button.id
        if btn_id == "btn-add":
            self._handle_add_pair()
        elif btn_id == "btn-fetch":
            self._fetch_all_pairs()

    def _handle_add_pair(self) -> None:
        from tui.widgets.currency_widget import CurrencyWidget, _EditPairModal

        async def _handle(result) -> None:
            if not result:
                return
            new_pair, new_scale = result
            widget = CurrencyWidget(new_pair, new_scale, widget_height=self._widget_height)
            from tui.widgets.gallery import WidgetGallery
            await self.query_one("#gallery", WidgetGallery).add_currency_widget(widget)
            from shared.config import load_config, save_config, WidgetConfig
            config = load_config()
            config.widgets.append(WidgetConfig(new_pair, new_scale))
            save_config(config)
            from shared.config import notify_daemon
            notify_daemon()
            self._fetch_single_pair(new_pair, new_scale)

        self.push_screen(_EditPairModal("EUR/USD", "1M"), _handle)

    def _fetch_all_pairs(self) -> None:
        self.run_worker(self._do_fetch_all(), name="fetch-all", exclusive=True)

    def _fetch_single_pair(self, pair: str, scale: str) -> None:
        self.run_worker(self._do_fetch_one(pair, scale), name=f"fetch-{pair}", exclusive=False)

    async def _do_fetch_all(self) -> None:
        config = load_config()
        status = self.query_one("#fetch-status", Label)
        pairs = config.widgets
        status.update(f"⏳ Chargement de {len(pairs)} paire(s)...")
        for i, w in enumerate(pairs, 1):
            status.update(f"⏳ {w.pair} {w.scale} ({i}/{len(pairs)})...")
            await self._do_fetch(w.pair, w.scale)
        status.update("✓ Données à jour")
        self.set_timer(3, lambda: status.update(""))

    async def _do_fetch_one(self, pair: str, scale: str) -> None:
        status = self.query_one("#fetch-status", Label)
        status.update(f"⏳ Chargement {pair} {scale}...")
        await self._do_fetch(pair, scale)
        status.update(f"✓ {pair} {scale} chargé")
        self.set_timer(3, lambda: status.update(""))

    async def _do_fetch(self, pair: str, scale: str) -> None:
        from daemon.fetcher import fetch_rates
        from daemon.renderer import render_chart, render_error_chart
        from shared.paths import png_path
        path = png_path(pair, scale)
        try:
            rates = await fetch_rates(pair, scale)
            render_chart(rates, pair, scale, path)
            logger.info(f"Données chargées : {pair} {scale}")
        except Exception as exc:
            logger.error(f"Échec chargement {pair} {scale} : {exc}")
            render_error_chart(pair, str(exc), path)
```

- [ ] **Step 3 : Mettre à jour `_update_config` dans `currency_widget.py`**

Dans `tui/widgets/currency_widget.py`, remplacer la méthode `_update_config` :

```python
    def _update_config(self) -> None:
        from shared.config import load_config, save_config, WidgetConfig
        from tui.widgets.gallery import WidgetGallery
        config = load_config()
        gallery = self.app.query_one(WidgetGallery)
        config.widgets = [
            WidgetConfig(w.pair, w.scale)
            for w in gallery.all_currency_widgets()
        ]
        save_config(config)
```

- [ ] **Step 4 : Lancer toute la suite de tests**

```bash
pytest -v
```

Résultat attendu : 18+ tests `PASSED` (les 18 existants + les 4 nouveaux de `test_gallery.py`).

- [ ] **Step 5 : Commit**

```bash
git add tui/app.py tui/widgets/currency_widget.py tests/test_tui.py
git commit -m "feat: remplacer Grid Textual par WidgetGallery dans app.py"
```

---

### Task 6 : Retirer `grid_columns` de `shared/config.py`

**Files:**
- Modify: `shared/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1 : Retirer `grid_columns` de `DashboardConfig`**

Dans `shared/config.py`, remplacer :

```python
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
```

Par :

```python
@dataclass
class DashboardConfig:
    base_currency: str = "EUR"
    refresh_interval_minutes: int = 60
    terminal_cell_ratio: float = 0.477
    widgets: List[WidgetConfig] = field(
        default_factory=lambda: [
            WidgetConfig("EUR/USD", "1M"),
            WidgetConfig("EUR/GBP", "1M"),
            WidgetConfig("EUR/JPY", "1M"),
        ]
    )
```

- [ ] **Step 2 : Mettre à jour `tests/test_config.py`**

Dans `tests/test_config.py`, modifier `test_save_and_load_roundtrip` :

Remplacer :
```python
    cfg = DashboardConfig(
        base_currency="USD",
        refresh_interval_minutes=30,
        grid_columns=3,
        terminal_cell_ratio=0.6,
        widgets=[WidgetConfig("GBP/JPY", "6M")],
    )
    save_config(cfg)
    loaded = load_config()
    assert loaded.base_currency == "USD"
    assert loaded.refresh_interval_minutes == 30
    assert loaded.grid_columns == 3
    assert loaded.terminal_cell_ratio == 0.6
    assert loaded.widgets[0].pair == "GBP/JPY"
    assert loaded.widgets[0].scale == "6M"
```

Par :
```python
    cfg = DashboardConfig(
        base_currency="USD",
        refresh_interval_minutes=30,
        terminal_cell_ratio=0.6,
        widgets=[WidgetConfig("GBP/JPY", "6M")],
    )
    save_config(cfg)
    loaded = load_config()
    assert loaded.base_currency == "USD"
    assert loaded.refresh_interval_minutes == 30
    assert loaded.terminal_cell_ratio == 0.6
    assert loaded.widgets[0].pair == "GBP/JPY"
    assert loaded.widgets[0].scale == "6M"
```

- [ ] **Step 3 : Lancer toute la suite de tests**

```bash
pytest -v
```

Résultat attendu : tous les tests `PASSED`.

- [ ] **Step 4 : Commit**

```bash
git add shared/config.py tests/test_config.py
git commit -m "refactor: retirer grid_columns de DashboardConfig (2 colonnes fixes dans WidgetGallery)"
```

---

## Résumé des commits

1. `feat: ajouter GalleryRow avec hauteur fixe`
2. `feat: WidgetGallery.load_widgets — chargement en lot`
3. `feat: WidgetGallery.add_currency_widget — ajout dynamique async`
4. `feat: CurrencyWidget.RequestDelete + nettoyage rangées vides dans WidgetGallery`
5. `feat: remplacer Grid Textual par WidgetGallery dans app.py`
6. `refactor: retirer grid_columns de DashboardConfig (2 colonnes fixes dans WidgetGallery)`
