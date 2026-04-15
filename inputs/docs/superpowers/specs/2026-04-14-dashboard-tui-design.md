# Design : Dashboard TUI de Suivi de Risque de Change

**Date :** 2026-04-14
**Statut :** Validé

---

## 1. Contexte et objectif

Application terminal (TUI) interactive pour surveiller l'évolution de paires de devises étrangères. Public cible : investisseurs particuliers suivant des actifs à l'étranger. Usage medium/long terme, pas de trading intra-day.

Référence : `cdc_init.md`

---

## 2. Décisions de conception

| Point | Décision |
|---|---|
| Devise de base | Valeur par défaut uniquement — chaque widget affiche une paire libre |
| Layout initial | 3 paires pré-configurées : EUR/USD, EUR/GBP, EUR/JPY (échelle 1M) |
| Graphiques | matplotlib, rendu inline via protocole iTerm2 |
| Terminal cible | iTerm2 |
| Persistance | Must-have v1 — `~/.config/dashboard/config.json` |
| Interactions | Menu contextuel (clic droit ou touche `m` sur widget focalisé) |
| Alertes visuelles | Hors scope v1 — emplacement réservé dans l'onglet Config |
| Notifications externes | V2 (Pushover, email, iMessage) |
| Fréquence refresh | Configurable dans l'onglet Configuration |
| Données historiques | Journalières uniquement — Frankfurter.app |
| Bordures UI | Traits fins (`border: solid`) pour maximiser l'espace utile |

---

## 3. Architecture générale

Deux processus distincts communiquant via fichiers partagés et signal UNIX.

```
┌─────────────────────────────────────────┐
│  daemon (com.user.dashboard.plist)       │
│  - Lit config.json                       │
│  - Fetch Frankfurter.app (async/httpx)   │
│  - Génère PNG via matplotlib             │
│  - Dort jusqu'au prochain interval       │
│  - Sur SIGHUP : relit config + regénère  │
└──────────────┬──────────────────────────┘
               │ écrit PNG
               ▼
   ~/.config/dashboard/
   ├── config.json          ← partagé daemon + TUI
   ├── daemon.pid           ← PID du daemon (pour SIGHUP)
   └── cache/
       ├── EUR_USD_1M.png
       ├── EUR_USD_6M.png
       └── ...

┌─────────────────────────────────────────┐
│  TUI Textual (bin/dashboard)             │
│  - Lit config.json au démarrage          │
│  - Affiche les PNG (protocole iTerm2)    │
│  - Poll le cache toutes les 5s           │
│  - Menu contextuel sur les widgets       │
│  - Sur modif config : écrit + SIGHUP     │
└─────────────────────────────────────────┘
```

**Nommage des PNG :** `<BASE>_<QUOTE>_<ECHELLE>.png`
Exemples : `EUR_USD_1M.png`, `GBP_JPY_5A.png`

---

## 4. Structure des modules

```
dashboard/
├── bin/
│   └── dashboard              # Script shell : active .venv + lance main.py
│                              # → symlink : /usr/local/bin/dashboard
├── daemon/
│   ├── __main__.py            # Point d'entrée daemon, gestion SIGHUP
│   ├── fetcher.py             # Client Frankfurter.app (httpx async)
│   └── renderer.py            # Génération PNG matplotlib
├── tui/
│   ├── app.py                 # DashboardApp (Textual App)
│   ├── widgets/
│   │   ├── currency_widget.py # Widget devise : en-tête, taux, PNG
│   │   └── context_menu.py    # Menu contextuel flottant
│   └── screens/
│       └── config_screen.py   # Onglet Configuration
├── shared/
│   ├── config.py              # Lecture/écriture config.json + SIGHUP
│   └── paths.py               # Constantes de chemins
├── logs/
│   └── logger.py              # Logging avec niveau DEBUG
├── main.py                    # Lance le TUI
├── requirements.txt
└── com.user.dashboard.plist
```

---

## 5. Format de configuration

**`~/.config/dashboard/config.json` :**

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

Le fichier `daemon.pid` est écrit par le daemon au démarrage et supprimé à l'arrêt.

---

## 6. Données historiques

API : **Frankfurter.app** — données journalières (jours ouvrés uniquement), gratuite, sans clé.

| Échelle | Période | Points approximatifs |
|---|---|---|
| 1M | 1 mois | ~22 pts |
| 3M | 3 mois | ~65 pts |
| 6M | 6 mois | ~130 pts |
| 1A | 1 an | ~260 pts |
| 2A | 2 ans | ~520 pts |
| 5A | 5 ans | ~1 300 pts |

Endpoint utilisé : `https://api.frankfurter.app/<date_debut>..<date_fin>?from=EUR&to=USD`

---

## 7. Cycle de vie du daemon

1. Démarrage → lit `config.json`, écrit `daemon.pid`
2. Génère les PNG manquants ou périmés pour toutes les paires × toutes les échelles
   — *Un PNG est considéré périmé si son âge dépasse `refresh_interval_minutes`*
3. Dort `refresh_interval_minutes`
4. Réveil → re-fetch et regénère tous les PNG
5. Sur `SIGHUP` → interrompt le sleep, relit `config.json`, regénère uniquement les PNG affectés par les changements

---

## 8. Interface TUI

```
┌─────────────────────────────────────────────────┐
│  Dashboard TUI           [Dashboard] [Config]    │
├─────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐         │
│ │ EUR/USD · 1M    │ │ EUR/GBP · 1M    │         │
│ │ 1.0842  +0.3%   │ │ 0.8561  -0.1%   │         │
│ │ ~~~graphe~~~    │ │ ~~~graphe~~~    │         │
│ └─────────────────┘ └─────────────────┘         │
│ ┌─────────────────┐ ┌─────────────────┐         │
│ │ EUR/JPY · 1M    │ │      [+]        │         │
│ │ 163.2   +1.2%   │ │                 │         │
│ │ ~~~graphe~~~    │ │  Ajouter        │         │
│ └─────────────────┘ └─────────────────┘         │
└─────────────────────────────────────────────────┘
```

**Widget devise (`CurrencyWidget`) :**
- En-tête : paire + échelle active (`EUR/USD · 1M`)
- Taux actuel + variation % colorée (vert hausse / rouge baisse)
- PNG matplotlib affiché via protocole iTerm2
- Spinner si PNG absent (daemon pas encore passé)
- Message d'erreur en rouge si paire invalide

**Menu contextuel** (clic droit ou touche `m`) :
```
┌──────────────────────┐
│ ✎  Modifier la paire  │
│ ⊞  Changer l'échelle  │
│ ✕  Supprimer         │
└──────────────────────┘
```

**Onglet Configuration :**
- Devise de base (input texte)
- Intervalle de rafraîchissement en minutes (input numérique)
- Nombre de colonnes de la grille (input numérique, défaut : 2)
- Emplacement réservé "Seuils d'alerte" (désactivé, labellisé "Prochainement")
- Bouton "Appliquer" → écrit `config.json` + SIGHUP au daemon

**Grille scrollable :** Textual offre une solution clé en main — un `ScrollableContainer` (scrollbars automatiques sur les deux axes) encapsulant un `Grid`. Le nombre de colonnes est appliqué dynamiquement au démarrage et à chaque modification de config :
```python
grid.styles.grid_size_columns = config.grid_columns
grid.styles.grid_columns = " ".join(["1fr"] * config.grid_columns)
```
Si le contenu dépasse la hauteur du terminal, le scroll vertical s'active automatiquement.

**Poll du cache :** `set_interval()` Textual toutes les 5 secondes — rafraîchit les widgets dont le PNG a une date de modification plus récente.

**Bordures :** `border: solid` (traits fins Unicode) sur tous les widgets, menus et modales.

---

## 9. Logging

- Logger unique `dashboard`, fichier rotatif `~/.config/dashboard/dashboard.log`
- Rotation : 1 Mo max, 3 fichiers conservés
- Niveau configurable via `DASHBOARD_LOG_LEVEL` (défaut : `INFO`)
- Chaque ligne préfixée par le composant : `[daemon]` ou `[tui]`
- Mode debug : `DASHBOARD_LOG_LEVEL=DEBUG dashboard`

---

## 10. Gestion des erreurs

| Situation | Comportement daemon | Comportement TUI |
|---|---|---|
| API indisponible | Log WARNING, conserve PNG existant, réessaie au cycle suivant | Affiche PNG existant (potentiellement périmé) |
| Paire invalide | Génère PNG d'erreur (texte centré) | Affiche le PNG d'erreur en rouge |
| Timeout API (>10s) | Log ERROR, passe à la paire suivante | Idem API indisponible |
| Daemon non démarré | — | Spinner dans chaque widget + message statusbar |
| PNG absent du cache | — | Spinner d'attente |

---

## 11. Hors scope v1

- Alertes sur seuils de taux
- Notifications externes (Pushover, email, iMessage) — prévues en v2
- Données infra-journalières
- Support multi-terminaux (Kitty, WezTerm, etc.) — iTerm2 uniquement en v1
