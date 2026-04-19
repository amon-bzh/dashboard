# Dashboard TUI

Dashboard interactif de suivi de risque de change en temps différé, affiché dans un terminal compatible iTerm2.

## Fonctionnalités

- Affichage de paires de devises (EUR/USD, EUR/GBP, EUR/JPY…) sous forme de widgets graphiques
- Historique sur 1M, 3M, 6M, 1A, 2A ou 5A via [Frankfurter.app](https://frankfurter.app) (données BCE, sans clé API)
- Variation colorée (vert/rouge) et taux courant affiché dans chaque widget
- Rafraîchissement automatique configurable (daemon Launchd)
- Ajout/modification/suppression de paires en live via menu contextuel (touche `m`)
- Onglet de configuration intégré

## Architecture

Deux processus indépendants communiquant via fichiers :

```
daemon (Launchd)                     TUI (Textual)
├── fetche Frankfurter.app           ├── affiche les PNG via protocole iTerm2
└── génère PNG + JSON metadata  ←→  └── envoie SIGHUP au daemon si config change

~/.config/dashboard/
├── config.json        — configuration partagée
├── cache/*.png        — graphiques générés
├── cache/*.json       — métadonnées (taux courant, variation %)
└── daemon.pid         — PID pour SIGHUP
```

## Prérequis

- macOS avec iTerm2 (ou terminal compatible protocole inline images)
- Python 3.12
- Launchd (natif macOS)

## Installation

```bash
# 1. Cloner et créer l'environnement virtuel
git clone <repo>
cd dashboard
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Installer et démarrer le daemon
cp com.user.dashboard.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.dashboard.plist

# 3. Créer le symlink pour lancer le TUI depuis n'importe où
ln -sf "$(pwd)/bin/dashboard" /usr/local/bin/dashboard
```

## Utilisation

```bash
dashboard                        # lancer le TUI
DASHBOARD_LOG_LEVEL=DEBUG dashboard   # mode verbeux
```

**Navigation :**
- `Tab` / clic — basculer entre les onglets Dashboard et Configuration
- `m` — ouvrir le menu contextuel sur le widget focalisé (modifier paire, changer échelle, supprimer)
- `[+] Ajouter une paire` — bouton en bas de la grille

## Développement

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest          # lancer les 17 tests
pytest -v       # mode verbeux

python -m daemon   # lancer le daemon manuellement (hors Launchd)
```

## Configuration

Editée via l'onglet Configuration du TUI ou directement dans `~/.config/dashboard/config.json` :

```json
{
  "base_currency": "EUR",
  "refresh_interval_minutes": 60,
  "grid_columns": 2,
  "widgets": [
    {"pair": "EUR/USD", "scale": "1M"},
    {"pair": "EUR/GBP", "scale": "1M"},
    {"pair": "EUR/JPY", "scale": "1M"}
  ]
}
```

## Logs

```bash
tail -f ~/.config/dashboard/dashboard.log
tail -f ~/.config/dashboard/daemon-stderr.log
```
