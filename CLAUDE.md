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
tui/widgets/currency_widget.py  — CurrencyWidget + ChartDisplay
tui/screens/config_screen.py    — onglet Configuration
logs/logger.py           — logging niveau DEBUG/INFO/WARNING
```

## Commandes essentielles

```bash
source .venv/bin/activate
pytest -v                         # 18 tests
python -m main                    # lancer le TUI
python -m daemon                  # daemon manuel
DASHBOARD_LOG_LEVEL=DEBUG python -m main
tail -f ~/.config/dashboard/dashboard.log
```

## Points d'attention

**Rendu iTerm2 dans Textual** — `ChartDisplay` écrit la séquence iTerm2 hors du cycle Textual via `sys.__stdout__`. L'accroche correcte est `render_lines()` (appelé même si le cache Textual est actif), pas `render_line()`. Voir [Textual rendering](https://textual.textualize.io/guide/widgets/#render-methods).

**`terminal_cell_ratio`** — ratio `cell_w / cell_h` de la police terminal, stocké dans `config.json`. Détermine la hauteur du widget pour que le graphique 8:3 remplisse la largeur sans letterboxing. Valeur mesurée pour MesloLGS NF Regular 13pt : `0.477`. À ajuster si la police change.

**Daemon SIGHUP** — le TUI envoie `SIGHUP` au daemon (`shared/config.notify_daemon()`) après toute modification de config pour déclencher un rechargement immédiat.

**Config** — `~/.config/dashboard/config.json`. Créée automatiquement avec les valeurs par défaut si absente.

**Logs** — niveau contrôlé par `DASHBOARD_LOG_LEVEL` (env var). Fichiers dans `~/.config/dashboard/`.

## Tests

18 tests dans `tests/`. Pas de mocks réseau : `test_fetcher.py` fait de vrais appels HTTP. `test_tui.py` utilise `App.run_test()` (Textual).

## Références externes

- [Textual docs](https://textual.textualize.io/) — widgets, CSS, événements, `run_test()`
- [iTerm2 inline images protocol](https://iterm2.com/documentation-images.html)
- [Frankfurter API](https://api.frankfurter.dev/v1/) — `GET /v1/{start}..{end}?from=EUR&to=USD`
- [Launchd plist reference](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Matplotlib savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html)
