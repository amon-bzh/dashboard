# CLAUDE.md — Dashboard TUI

## Stack

- **Python 3.12** + venv `.venv/`
- **[Textual](https://textual.textualize.io/)** — framework TUI (widgets, CSS, événements)
- **[Matplotlib](https://matplotlib.org/stable/api/)** — génération des PNG (800×300 px, `figsize=(8,3) dpi=100`)
- **[Frankfurter API](https://api.frankfurter.dev/v1/)** — données BCE, sans clé API
- **Protocole iTerm2 inline images** — `\x1b]1337;File=inline=1;...` sur `sys.__stdout__`
- **Launchd** — daemon macOS, plist `com.user.dashboard.plist`

## Structure

```
main.py                  — point d'entrée TUI, calcule widget_height
shared/config.py         — DashboardConfig dataclass, load/save JSON
shared/paths.py          — chemins (~/.config/dashboard/)
daemon/fetcher.py        — appels HTTP Frankfurter (async)
daemon/renderer.py       — génère PNG + JSON métadonnées
tui/app.py               — DashboardApp (Textual App)
tui/widgets/gallery.py          — WidgetGallery + GalleryRow (layout 2 colonnes)
tui/widgets/currency_widget.py  — CurrencyWidget + ChartDisplay
tui/screens/config_screen.py    — onglet Configuration
logs/logger.py           — logging niveau DEBUG/INFO/WARNING
```

## Commandes essentielles

```bash
source .venv/bin/activate
pytest -v                         # 22 tests
python -m main                    # lancer le TUI
python -m daemon                  # daemon manuel
DASHBOARD_LOG_LEVEL=DEBUG python -m main
tail -f ~/.config/dashboard/dashboard.log
```

## Points d'attention

**Rendu iTerm2 dans Textual** — `ChartDisplay` écrit la séquence iTerm2 hors du cycle Textual via `sys.__stdout__`. L'accroche correcte est `render_lines()` (appelé même si le cache Textual est actif), pas `render_line()`. Voir [Textual rendering](https://textual.textualize.io/guide/widgets/#render-methods).

**`terminal_cell_ratio`** — ratio `cell_w / cell_h` de la police terminal, stocké dans `config.json`. Détermine `display_h` dans `_write_image` pour que le graphique 8:3 remplisse la largeur sans letterboxing. Valeur par défaut `0.477` (MesloLGS NF Regular 13pt) probablement incorrecte — voir `docs/letterboxing.md`.

**Letterboxing iTerm2** — chantier ouvert. Synthèse des pistes explorées (CSI 16t, `display_h` dynamique, `height: auto` Grid, `_compute_widget_height` adaptatif) dans `docs/letterboxing.md`.

**Daemon SIGHUP** — le TUI envoie `SIGHUP` au daemon (`shared/config.notify_daemon()`) après toute modification de config pour déclencher un rechargement immédiat.

**Config** — `~/.config/dashboard/config.json`. Créée automatiquement avec les valeurs par défaut si absente.

**Logs** — niveau contrôlé par `DASHBOARD_LOG_LEVEL` (env var). Fichiers dans `~/.config/dashboard/`.

**Layout galerie** — `WidgetGallery(VerticalScroll)` contient des `GalleryRow(Horizontal)` de 2 widgets. `load_widgets(list)` pour le batch initial (sync), `add_currency_widget(widget)` pour l'ajout dynamique (async). 2 colonnes fixes — non configurable. Pour initialiser un `GalleryRow` avec un widget, passer `widgets=[widget]` au constructeur (utilise `compose()`) plutôt que `await row.mount(widget)` après `await self.mount(row)` — évite le problème de mount séquentiel async.

**Suppressions Textual** — vérifier `is_last_in_row` AVANT d'appeler `widget.remove()` : `remove()` est schedulé (non immédiat), donc le DOM n'est pas encore mis à jour au moment du check qui suit.

**Config rétrocompatibilité** — quand un champ est retiré de `DashboardConfig`, ajouter `data.pop("ancien_champ", None)` dans `load_config()` avant la construction du dataclass : le `~/.config/dashboard/config.json` de production peut encore contenir l'ancienne clé.

**CSS Textual** — le combinateur enfant `>` fonctionne dans les sélecteurs Textual (ex : `GalleryRow > CurrencyWidget { width: 1fr; }`).

## Tests

22 tests dans `tests/`. Pas de mocks réseau : `test_fetcher.py` fait de vrais appels HTTP. `test_tui.py` et `test_gallery.py` utilisent `App.run_test()` (Textual).

## Références externes

- [Textual docs](https://textual.textualize.io/) — widgets, CSS, événements, `run_test()`
- [iTerm2 inline images protocol](https://iterm2.com/documentation-images.html)
- [Frankfurter API](https://api.frankfurter.dev/v1/) — `GET /v1/{start}..{end}?from=EUR&to=USD`
- [Launchd plist reference](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Matplotlib savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)
