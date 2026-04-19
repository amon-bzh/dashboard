# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexte du projet

Dashboard TUI interactif de suivi de risque de change en temps différé. L'application affiche des paires de devises (ex : EUR/USD) sous forme de widgets graphiques dans un terminal, avec historique et variation colorée. Public cible : investisseurs particuliers, usage medium/long terme, pas de trading intra-day.

- **Cahier des charges :** `cdc_init.md`
- **Spec de design validée :** `docs/superpowers/specs/2026-04-14-dashboard-tui-design.md`
- **Plan d'implémentation (16 tâches) :** `docs/superpowers/plans/2026-04-14-dashboard-tui.md`

## Reprise du travail

Le code applicatif est dans le répertoire **parent** (`/Users/Antoine/Developer/dashboard/`), branche `feature/dashboard-tui`.

**Avancement :** Tasks 1–16 complètes (17 tests ✅). Implémentation terminée.

**Précisions sur la structure du repo :**
- Le repo git est à la racine `/Users/Antoine/Developer/dashboard/` (pas dans `inputs/`)
- `requirements.txt` = dépendances runtime uniquement
- `requirements-dev.txt` = runtime + pytest (utiliser pour les tests)

## Stack technique (décisions validées)

- **Python 3.12**, environnement virtuel `.venv/`
- **TUI :** `textual ≥ 0.80`
- **HTTP :** `httpx` (async)
- **Graphiques :** `matplotlib` (backend `Agg`) + rendu PNG inline via **protocole iTerm2**
- **Données :** Frankfurter.app (BCE, gratuite, sans clé API, données journalières)
- **Dépendances :** `textual`, `httpx`, `matplotlib`, `scipy`, `python-dateutil`
- **Tests :** `pytest`, `pytest-asyncio` (`asyncio_mode = auto`)

## Architecture (deux processus)

```
daemon (com.user.dashboard.plist)          TUI (bin/dashboard → main.py)
├── daemon/__main__.py                     ├── tui/app.py
├── daemon/fetcher.py   → Frankfurter      ├── tui/widgets/currency_widget.py
└── daemon/renderer.py  → PNG             ├── tui/widgets/context_menu.py
                                           └── tui/screens/config_screen.py
shared/
├── config.py   (DashboardConfig, load/save, notify_daemon via SIGHUP)
└── paths.py    (constantes ~/.config/dashboard/)
logs/logger.py  (RotatingFileHandler, DASHBOARD_LOG_LEVEL)
```

**Communication inter-processus :** fichiers partagés uniquement.
- `~/.config/dashboard/config.json` — configuration (lue/écrite par les deux)
- `~/.config/dashboard/cache/<BASE>_<QUOTE>_<ECHELLE>.png` — graphiques
- `~/.config/dashboard/cache/<BASE>_<QUOTE>_<ECHELLE>.json` — `{current, variation_pct}`
- `~/.config/dashboard/daemon.pid` — PID du daemon (pour SIGHUP)

## Commandes de développement

```bash
# Environnement virtuel (déjà créé — se placer dans /Users/Antoine/Developer/dashboard/)
source .venv/bin/activate
pip install -r requirements-dev.txt   # inclut pytest + pytest-asyncio

# Lancer le TUI
dashboard                          # via symlink /usr/local/bin/dashboard
DASHBOARD_LOG_LEVEL=DEBUG dashboard

# Lancer le daemon manuellement (hors Launchd)
python -m daemon

# Tests
pytest
pytest tests/test_fetcher.py::test_fetch_rates_returns_date_rate_dict -v

# Launchd
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.dashboard.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.user.dashboard.plist
launchctl kickstart -k gui/$(id -u)/com.user.dashboard   # restart
launchctl kill SIGTERM gui/$(id -u)/com.user.dashboard   # stop
```

## Gotchas Textual (découverts en session)

- **Routing messages** : monter un widget sur `self.app` coupe le bubbling — les handlers du widget parent ne reçoivent rien. Toujours monter sur `self` si les messages doivent remonter vers le parent.
- **layer: overlay** : nécessite `layers: base overlay;` déclaré dans le CSS de `Screen`, sinon le widget overlay est invisible derrière la grille.
- **pilot.type()** : absent dans Textual ≤ 0.82 — pour les tests, manipuler `Input.value` directement et appeler le handler explicitement.
- **readlink -f** : non disponible sur macOS — utiliser `pwd -P` dans les scripts bash.

## Conventions importantes

- **Async/await** pour tous les appels API dans le daemon
- **SIGHUP** déclenche un rechargement immédiat du daemon (pas de redémarrage)
- **Bordures UI :** `border: solid` (traits fins Unicode) sur tous les widgets
- **Échelles disponibles :** `1M`, `3M`, `6M`, `1A`, `2A`, `5A` (pas de 7J — trop peu de points)
- **Nombre de colonnes** configurable dans `config.json` (`grid_columns`, défaut : 2)
- **Grille scrollable :** `ScrollableContainer` → `Grid` (solution clé en main Textual)
- **Type hints** sur toutes les fonctions publiques
- **Logs :** niveau via `DASHBOARD_LOG_LEVEL` (défaut `INFO`), fichier rotatif 1 Mo × 3

## Rendu iTerm2 — note d'implémentation

Le widget `ChartDisplay` utilise `render_line()` pour injecter la séquence OSC iTerm2 :
```
ESC ] 1337 ; File=inline=1;width=Wchar;height=Hchar;<base64> BEL
```
Si ce rendu ne fonctionne pas dans le contexte Textual, le fallback est `rich-pixels` + `Pillow` (documenté en fin du plan d'implémentation).
