# Dashboard TUI

Dashboard interactif de suivi de risque financier en temps différé, affiché dans un terminal compatible iTerm2.

## Fonctionnalités

- **Paires de devises** (EUR/USD, EUR/GBP, EUR/JPY…) — graphiques sur 1M, 3M, 6M, 1A, 2A, 5A via [Frankfurter API](https://api.frankfurter.dev/v1/) (données BCE, sans clé API)
- **VIX** — indice de volatilité implicite (Yahoo Finance), niveaux de référence 20/30, périodes 1M/3M/6M/1A
- **Fear & Greed Index** — Crypto F&G (alternative.me), historique 30 jours, classification colorée
- Variation colorée (vert/rouge) et valeur courante dans chaque widget
- Rafraîchissement automatique configurable (daemon Launchd) pour les paires FX
- Ajout/modification/suppression de paires en live via menu contextuel (`m`) ou touche `k`
- Thème Bloomberg (noir #05070a, amber, cyan)
- Onglet de configuration intégré

## Architecture

Deux processus indépendants communiquant via fichiers :

```
daemon (Launchd)                     TUI (Textual)
├── fetche Frankfurter API (FX)      ├── affiche les PNG via protocole iTerm2
└── génère PNG + JSON metadata  ←→  └── envoie SIGHUP au daemon si config change

VIX + F&G : chargés à la demande via bouton "↻ Charger les données"

~/.config/dashboard/
├── config.json        — configuration partagée
├── cache/*.png        — graphiques générés (800×300 px)
├── cache/*.json       — métadonnées (valeur courante, variation %)
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
dashboard                             # lancer le TUI
DASHBOARD_LOG_LEVEL=DEBUG dashboard   # mode verbeux
```

**Navigation :**
- `←` / `→` — naviguer entre les onglets du TabbedContent
- `Tab` / `Shift+Tab` — cycler les périodes sur le widget focalisé (paires FX, VIX)
- `p` — idem (alias de Tab)
- `k` — supprimer la paire de devises focalisée
- `m` — ouvrir le menu contextuel (modifier paire, changer échelle, supprimer)
- `[+] Ajouter une paire` — bouton en bas de la grille
- `↻ Charger les données` — charger/rafraîchir FX + VIX + F&G
- `q` — quitter

**Onglets :**
- **Dashboard** — galerie de paires de devises (2 colonnes)
- **VIX** — Volatility Index avec niveaux de référence
- **F&G** — Fear & Greed Index 30 jours
- **Configuration** — paramètres et purge du cache

## Configuration

Editée via l'onglet Configuration du TUI ou directement dans `~/.config/dashboard/config.json` :

```json
{
  "base_currency": "EUR",
  "refresh_interval_minutes": 60,
  "widgets": [
    {"pair": "EUR/USD", "scale": "1M"}
  ]
}
```

## Développement

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt

pytest          # lancer les 39 tests
pytest -v       # mode verbeux

python -m daemon   # lancer le daemon manuellement (hors Launchd)
```

## Logs

```bash
tail -f ~/.config/dashboard/dashboard.log
tail -f ~/.config/dashboard/daemon-stderr.log
```
