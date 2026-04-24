# Spec : WidgetGallery — remplacement du Grid Textual

**Date :** 2026-04-24  
**Statut :** Approuvé

## Contexte

Le `Grid` Textual utilisé dans `app.py` pose des problèmes de contrainte de hauteur (`grid_rows` ignoré, widgets compressés). On le remplace par une classe `WidgetGallery` basée sur `VerticalScroll`, avec un layout CSS pur en 2 colonnes fixes.

## Architecture

### Nouveau fichier : `tui/widgets/gallery.py`

```
WidgetGallery(VerticalScroll)
└── GalleryRow(Horizontal)
    ├── CurrencyWidget
    └── CurrencyWidget
```

**`WidgetGallery(VerticalScroll)`**

- Reçoit `widget_height: int` au constructeur (calculé dans `main.py`, inchangé).
- Méthode `add_currency_widget(widget: CurrencyWidget)` : ajoute le widget dans la dernière `GalleryRow` si elle a < 2 enfants, sinon crée une nouvelle rangée.
- Méthode `all_currency_widgets()` : itère les `GalleryRow` dans l'ordre DOM et retourne tous les `CurrencyWidget` dans l'ordre d'affichage (utilisé par `_update_config`).

**`GalleryRow(Horizontal)` — définie dans `gallery.py`, au même niveau que `WidgetGallery`**

- Reçoit `widget_height: int`.
- Applique `self.styles.height = widget_height` dans `on_mount`.

### CSS

```css
/* dans WidgetGallery.DEFAULT_CSS */
WidgetGallery {
    width: 1fr;
    height: 1fr;
}

/* dans GalleryRow.DEFAULT_CSS */
GalleryRow {
    width: 1fr;
}

GalleryRow > CurrencyWidget {
    width: 1fr;
}
```

La hauteur de `GalleryRow` est appliquée programmatiquement (pas en CSS statique) car elle provient de `main.py`.

## Gestion des rangées

### Ajout

```
1. Chercher la dernière GalleryRow
2. Si elle a < 2 CurrencyWidget → mount le widget dedans
3. Sinon → créer une nouvelle GalleryRow, y monter le widget, monter la row dans la galerie
```

### Suppression

`CurrencyWidget.on_context_menu_delete_widget` appelle `self.remove()` (inchangé). `WidgetGallery` écoute cet événement pour vérifier si la `GalleryRow` parente est devenue vide — si oui, la supprimer. Une rangée passant de 2 à 1 widget reste en place (le widget survivant prend `width: 1fr`).

## Changements dans `app.py`

### Suppressions

- Import `Grid`
- CSS `#grid { layout: grid; grid-gutter: 1; }`
- Dans `_load_widgets` : calculs `nb_cols`, `nb_rows`, `grid_size_columns`, `grid_columns`, `grid_rows`

### Modifications

- Import `WidgetGallery` depuis `tui.widgets.gallery`
- `compose` : `Grid(id="grid")` → `WidgetGallery(self._widget_height, id="gallery")`
- `_load_widgets` : `grid.mount(CurrencyWidget(...))` → `gallery.add_currency_widget(CurrencyWidget(...))`
- `_handle_add_pair` : idem
- Toutes les `query_one("#grid", Grid)` → `query_one("#gallery", WidgetGallery)`

### Inchangé

- `main.py` et `_compute_widget_height`
- `widget_height` transmis à `DashboardApp` puis à `WidgetGallery`

## Changements dans `shared/config.py`

- `grid_columns: int = 2` retiré de `DashboardConfig` (2 colonnes désormais fixes dans `WidgetGallery`)
- Tests associés à `grid_columns` mis à jour

## Ce qui n'est pas dans le scope

- Modification de l'algorithme de calcul de `widget_height` dans `main.py`
- Réorganisation des widgets lors d'une suppression (repack des rangées)
- Support d'un nombre de colonnes configurable
