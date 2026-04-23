# Chantier : Correction du letterboxing iTerm2

## Symptôme

Les graphiques PNG affichés via le protocole iTerm2 inline images présentent une zone noire
à droite de chaque cadre. Le graphique occupe environ 75-80 % de la largeur disponible.

## Cause racine

La séquence iTerm2 spécifie `width=Wchar;height=Hchar;preserveAspectRatio=1`. iTerm2 convertit
en pixels : `W × cell_w` par `H × cell_h`. Si le ratio pixel du cadre ne correspond pas
au ratio du PNG (800×300, ratio 8:3 = 2.667), iTerm2 letterboxe.

Zone noire à droite ↔ `W × cell_w / (H × cell_h) > 8/3` ↔ cadre trop large → PNG limité
par la hauteur, ne remplit pas la largeur.

La valeur `terminal_cell_ratio = cell_w / cell_h` est donc critique. Si elle est plus petite
que le vrai ratio de la police, `display_h` calculé est trop petit, le cadre pixel est trop
large, et les zones noires apparaissent à droite.

## Variables en jeu

| Variable | Rôle | Source |
|----------|------|--------|
| `w` | Largeur du ChartDisplay (colonnes Textual) | `self.size.width` dans `_write_image` |
| `h` | Hauteur du ChartDisplay (lignes Textual) | `self.size.height` dans `_write_image` |
| `display_h` | Hauteur envoyée à iTerm2 | `min(h, ceil(w * ratio / (8/3)))` |
| `cell_ratio` | `cell_w / cell_h` de la police | Config ou CSI 16t |
| `widget_height` | Hauteur totale du CurrencyWidget | Calculé dans `main.py` |

## Comportement du Grid Textual

Mesures avec terminal 150 × 35 lignes, 4 widgets (2×2) :

- Overhead Textual : tabs(3) + footer(1) + bottom-bar(2) = **6 lignes**
- Disponible pour le Grid : 35 − 6 = **29 lignes**
- Avec 2 rangées + 1 gutter : chaque rangée = (29 − 1) / 2 = **14 lignes**
- ChartDisplay = 14 − 4 (2 bordures + header + rate-line) = **10 lignes**

Le Grid avec `height: 1fr` (défaut Textual) compresse les widgets à la hauteur disponible,
indépendamment de `widget_height`. `widget_height` n'est donc utile que pour estimer la
hauteur attendue — la vraie valeur `h` dans `_write_image` est fournie par Textual.

**Tentative `height: auto` sur `#grid`** : les cadres prennent leur vraie hauteur mais ne
remplissent plus l'écran (grand espace vide). Abandonné.

## Pistes explorées

### 1. Ajustement de `terminal_cell_ratio` dans la config (commit d528de3)

Valeur empirique `0.477` pour MesloLGS NF Regular 13pt.
**Problème** : la valeur ne correspond pas au vrai ratio de la police dans ce terminal.
La zone noire persiste.

### 2. Calcul de `display_h` depuis la vraie largeur `w` (session courante)

Au lieu d'envoyer `height=h`, calculer `display_h = ceil(w * ratio / (8/3))` dans
`_write_image`. Cela garantit `display_aspect ≥ PNG_ratio` si `ratio = ratio_vrai`.
**Problème** : `ratio_vrai` n'est pas connu avec précision. Avec `ratio_config = 0.477`
trop petit, `display_h` est sous-estimé et la zone noire persiste.

### 3. CSI 16t via `sys.stdout` (commit 1de5f18, repris en session courante)

Envoi de `\x1b[16t` avant le lancement de Textual pour mesurer `cell_w` et `cell_h` en pixels.
Réponse attendue : `\x1b[6;cell_h;cell_wt`.

**Résultat** : réponse vide. Timeout systématique.

Tentative avec `/dev/tty` (session courante) : non conclusif à ce stade (pas pu tester
après le commit WIP).

Logs de diagnostic :
```
[CSI16t] stdin.isatty()=True
[CSI16t] timeout après 0.5s, réponse brute: ''
[CSI16t] réponse complète: ''
[CSI16t] regex non matché sur: ''
```

### 4. `_compute_widget_height` adaptatif (session courante)

Formule prenant en compte le vrai espace disponible :

```python
h_chart = min(
    inner_width * cell_ratio / image_ratio,   # depuis le ratio PNG
    (available - (nb_rows-1)) / nb_rows - 4  # depuis la hauteur écran
)
```

Améliore l'alignement `widget_height` ↔ `h` réel, mais le letterboxing reste
si `cell_ratio` est incorrect.

## État du code (WIP)

### `main.py`

- `_query_cell_ratio(logger)` : tente CSI 16t via `/dev/tty`, fallback sur config
- `_compute_widget_height(cell_ratio, logger)` : formule hybride (ratio PNG + hauteur écran)
- Logs DEBUG détaillés : `[CSI16t]`, `[calcul]`

### `tui/app.py`

- `DashboardApp.__init__` accepte `cell_ratio` (stocké dans `self.cell_ratio`)

### `tui/widgets/currency_widget.py`

- `_write_image` calcule `display_h = min(h, ceil(w * ratio / (8/3)))` avec
  `ratio = self.app.cell_ratio`
- Logs DEBUG : `[cadre]`, `[image]` avec dimensions PNG, display_h, display_h_exact

## Pistes restantes

1. **CSI 16t** — Comprendre pourquoi iTerm2 ne répond pas. Pistes :
   - Vérifier si la séquence est transmise avant que Textual prenne le contrôle du tty
   - Tester en dehors de l'app : `python -c "import sys; sys.stdout.write('\x1b[16t'); sys.stdout.flush(); import time; time.sleep(1)"`
   - Vérifier si une option iTerm2 bloque les séquences XTWINOPS

2. **Calibration interactive** — Ajouter une commande `--calibrate` ou un écran dédié
   dans l'onglet Configuration : afficher un graphique de test et permettre à l'utilisateur
   d'ajuster `terminal_cell_ratio` avec les flèches jusqu'à que la zone noire disparaisse.

3. **Ratio PNG adaptatif** — Calculer le ratio PNG dans `renderer.py` en fonction
   de `h` réel (mesuré lors du premier rendu) et `cell_ratio`. Régénérer le PNG
   avec les bonnes proportions. Nécessite une communication `_write_image` → daemon.

4. **Mesure par image test** — Générer un PNG 1×1 blanc, l'afficher via iTerm2, et
   mesurer la hauteur occupée visuellement pour en déduire `cell_ratio`.
