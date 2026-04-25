# [HISTORIQUE] Chantier letterboxing iTerm2

> **Note :** Ce document décrit une architecture abandonnée. Le champ `terminal_cell_ratio`
> et toute la logique CSI 16t ont été supprimés. `_write_image` utilise désormais
> `display_h = h` (toute la hauteur disponible du `ChartDisplay`). Le letterboxing peut
> subsister selon la police terminal mais n'est plus traité activement.

---

## Symptôme (historique)

Les graphiques PNG affichés via le protocole iTerm2 inline images présentaient une zone noire
à droite de chaque cadre. Le graphique occupait environ 75-80 % de la largeur disponible.

## Cause racine

La séquence iTerm2 spécifie `width=Wchar;height=Hchar;preserveAspectRatio=1`. iTerm2 convertit
en pixels : `W × cell_w` par `H × cell_h`. Si le ratio pixel du cadre ne correspond pas
au ratio du PNG (800×300, ratio 8:3 = 2.667), iTerm2 letterboxe.

Zone noire à droite ↔ `W × cell_w / (H × cell_h) > 8/3` ↔ cadre trop large → PNG limité
par la hauteur, ne remplit pas la largeur.

## Pistes explorées et abandonnées

### 1. `terminal_cell_ratio` dans la config (supprimé)

Valeur empirique `0.477` pour MesloLGS NF Regular 13pt. Stocké dans `DashboardConfig`,
exposé dans l'écran Configuration, utilisé dans `_compute_widget_height` (main.py) et
`_write_image` (currency_widget.py).

**Supprimé** — trop imprécis, configuration manuelle fastidieuse, valeur par défaut incorrecte
pour la majorité des polices.

### 2. CSI 16t via `/dev/tty`

Envoi de `\x1b[16t` avant le lancement de Textual pour mesurer `cell_w`/`cell_h` en pixels.
Réponse attendue : `\x1b[6;cell_h;cell_wt`.

**Résultat** : réponse vide, timeout systématique sur iTerm2. Abandonné.

### 3. `display_h` calculé depuis le ratio PNG

`display_h = ceil(w * ratio / (8/3))` dans `_write_image`. Nécessite un `ratio` correct.

**Supprimé** avec `terminal_cell_ratio`.

## État actuel

`_write_image` envoie `height=h` (hauteur réelle du `ChartDisplay` en cellules).
Le letterboxing potentiel est accepté comme limitation connue.

## Pistes futures éventuelles

1. **Calibration interactive** — écran dédié dans Configuration avec graphique de test
   et réglage visuel de la hauteur.
2. **Ratio PNG adaptatif** — régénérer le PNG avec les proportions correspondant à
   la taille réelle du widget.
