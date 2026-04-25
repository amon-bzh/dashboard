# CLAUDE.md — Dashboard TUI

## Stack

- **Python 3.12** + venv `.venv/`
- **[Textual](https://textual.textualize.io/)** — framework TUI (widgets, CSS, thème Bloomberg)
- **[Matplotlib](https://matplotlib.org/stable/api/)** — génération des PNG (800×300 px, `figsize=(8,3) dpi=100`)
- **[Frankfurter API](https://api.frankfurter.dev/v1/)** — données BCE paires FX, sans clé API
- **[yfinance](https://pypi.org/project/yfinance/)** — données VIX (`^VIX`) via Yahoo Finance, sans clé API
- **[alternative.me](https://alternative.me/crypto/fear-and-greed-index/)** — Crypto Fear & Greed Index, sans clé API
- **Protocole iTerm2 inline images** — `\x1b]1337;File=inline=1;...` sur `sys.__stdout__`
- **Launchd** — daemon macOS, plist `com.user.dashboard.plist`

## Structure

```
main.py                  — point d'entrée TUI, calcule widget_height
shared/config.py         — DashboardConfig dataclass, load/save JSON
shared/paths.py          — chemins (~/.config/dashboard/) + png_path, vix_png_path, fng_png_path
daemon/fetcher.py        — appels HTTP Frankfurter (async, paires FX)
daemon/renderer.py       — génère PNG FX + JSON métadonnées (palette Bloomberg)
daemon/vix_fetcher.py    — fetch VIX via yfinance (asyncio.to_thread)
daemon/vix_renderer.py   — génère PNG VIX + JSON métadonnées
daemon/fng_fetcher.py    — fetch F&G via alternative.me (async httpx)
daemon/fng_renderer.py   — génère PNG F&G 30j + JSON métadonnées
tui/app.py               — DashboardApp (Textual App), onglets Dashboard/VIX/F&G/Configuration
tui/theme.py             — thème Bloomberg (palette #05070a/amber/cyan)
tui/widgets/gallery.py          — WidgetGallery + GalleryRow (layout 2 colonnes FX)
tui/widgets/currency_widget.py  — CurrencyWidget + ChartDisplay
tui/widgets/vix_widget.py       — VixWidget (chart VIX, period cycling)
tui/widgets/fng_widget.py       — FngWidget (chart F&G 30j, lecture JSON meta)
tui/screens/config_screen.py    — onglet Configuration
logs/logger.py           — logging niveau DEBUG/INFO/WARNING
```

## Commandes essentielles

```bash
source .venv/bin/activate
pytest -v                         # 39 tests
python -m main                    # lancer le TUI
python -m daemon                  # daemon manuel
DASHBOARD_LOG_LEVEL=DEBUG python -m main
tail -f ~/.config/dashboard/dashboard.log
```

## Thème Bloomberg

Défini dans `tui/theme.py` (objet `BLOOMBERG`), enregistré au `on_mount` de `DashboardApp`.

Palette :
- `background` / `panel` : `#05070a`
- `primary` / `accent` : `#ffb020` (amber)
- `secondary` : `#22d3ee` (cyan)
- `success` : `#4ade80`, `error` : `#ef4444`, `warning` : `#f97316`
- `$border` / `$text-muted` : `#6b6355`

Tous les renderers matplotlib utilisent la même palette (`_BG="#05070a"`, etc.).

## Points d'attention

**Rendu iTerm2 dans Textual** — `ChartDisplay` écrit la séquence iTerm2 hors du cycle Textual via `sys.__stdout__`. L'accroche correcte est `render_lines()` (appelé même si le cache Textual est actif), pas `render_line()`. Voir [Textual rendering](https://textual.textualize.io/guide/widgets/#render-methods).

**`display_h = h`** — depuis la suppression de `terminal_cell_ratio`, `_write_image` utilise toute la hauteur disponible du `ChartDisplay`. Le letterboxing peut subsister selon la police, mais la logique CSI 16t a été abandonnée. Voir `docs/letterboxing.md` pour l'historique.

**Daemon SIGHUP** — le TUI envoie `SIGHUP` au daemon (`shared/config.notify_daemon()`) après toute modification de config pour déclencher un rechargement immédiat. Le daemon gère uniquement les paires FX ; VIX et F&G sont chargés à la demande via le bouton "↻ Charger les données".

**Config** — `~/.config/dashboard/config.json`. Créée automatiquement si absente. Champs actuels : `base_currency`, `refresh_interval_minutes`, `widgets[]`.

**Config rétrocompatibilité** — quand un champ est retiré de `DashboardConfig`, ajouter `data.pop("ancien_champ", None)` dans `load_config()` avant la construction du dataclass. Exemple : `grid_columns` et `terminal_cell_ratio` ont été supprimés ainsi.

**Logs** — niveau contrôlé par `DASHBOARD_LOG_LEVEL` (env var). Fichiers dans `~/.config/dashboard/`.

**Layout galerie** — `WidgetGallery(VerticalScroll)` contient des `GalleryRow(Horizontal)` de 2 widgets. `load_widgets(list)` pour le batch initial (sync), `add_currency_widget(widget)` pour l'ajout dynamique (async). 2 colonnes fixes — non configurable. Pour initialiser un `GalleryRow` avec un widget, passer `widgets=[widget]` au constructeur (utilise `compose()`) plutôt que `await row.mount(widget)` après `await self.mount(row)` — évite le problème de mount séquentiel async.

**Suppressions Textual** — vérifier `is_last_in_row` AVANT d'appeler `widget.remove()` : `remove()` est schedulé (non immédiat), donc le DOM n'est pas encore mis à jour au moment du check qui suit.

**Navigation clavier CurrencyWidget** :
- `Tab` / `Shift+Tab` — cycler les périodes (avant/arrière) sur le widget focalisé
- `p` — cycler les périodes (avant, alias de Tab)
- `k` — supprimer le widget courant (poste `RequestDelete`)
- `m` — ouvrir le menu contextuel (modifier paire, changer échelle)

Note : `Tab`/`Shift+Tab` ne sont plus des bindings au niveau `DashboardApp` (focus_next/previous supprimés) — ils sont capturés par `CurrencyWidget` et `VixWidget` quand focalisés.

**VixWidget** — même pattern que `CurrencyWidget` (Tab/Shift+Tab/p pour cycler 1M/3M/6M/1A). Pas de touche `k` (VIX non supprimable).

**FngWidget** — pas de period cycling (toujours 30j). Pas de bindings. Données : `current`, `classification`, `variation_7d`.

**VIX renderer** — couleur inversée par rapport aux paires FX : VIX en hausse → rouge (plus de peur), VIX en baisse → vert (calme). Lignes de référence y=20 (calme) et y=30 (tension).

**CSS Textual** — le combinateur enfant `>` fonctionne dans les sélecteurs Textual (ex : `GalleryRow > CurrencyWidget { width: 1fr; }`).

## Tests

39 tests dans `tests/`. `test_fetcher.py` utilise des mocks HTTP (pas de vrais appels réseau). `test_tui.py` et `test_gallery.py` utilisent `App.run_test()` (Textual). `test_vix_fetcher.py` et `test_fng_fetcher.py` utilisent également des mocks.

## Références externes

- [Textual docs](https://textual.textualize.io/) — widgets, CSS, thèmes, `run_test()`
- [iTerm2 inline images protocol](https://iterm2.com/documentation-images.html)
- [Frankfurter API](https://api.frankfurter.dev/v1/) — `GET /v1/{start}..{end}?from=EUR&to=USD`
- [yfinance](https://pypi.org/project/yfinance/) — `yf.Ticker("^VIX").history(period="1mo")`
- [alternative.me F&G API](https://alternative.me/crypto/fear-and-greed-index/) — `GET /fng/?limit=31`
- [Launchd plist reference](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Matplotlib savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)
