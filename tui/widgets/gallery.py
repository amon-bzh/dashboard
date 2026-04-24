from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll


class GalleryRow(Horizontal):
    DEFAULT_CSS = """
    GalleryRow {
        width: 1fr;
    }
    """

    def __init__(self, widget_height: int, widgets: list | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._widget_height = widget_height
        self._initial_widgets: list = widgets or []

    def compose(self) -> ComposeResult:
        yield from self._initial_widgets

    def on_mount(self) -> None:
        self.styles.height = self._widget_height


class WidgetGallery(VerticalScroll):
    DEFAULT_CSS = """
    WidgetGallery {
        width: 1fr;
        height: 1fr;
    }
    GalleryRow > CurrencyWidget {
        width: 1fr;
    }
    """

    def __init__(self, widget_height: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._widget_height = widget_height

    def load_widgets(self, widgets: list) -> None:
        """Charge un lot de CurrencyWidget en créant des rangées de 2."""
        rows = []
        for i in range(0, len(widgets), 2):
            rows.append(GalleryRow(widget_height=self._widget_height, widgets=widgets[i:i + 2]))
        if rows:
            self.mount(*rows)

    def all_currency_widgets(self) -> list:
        """Retourne tous les CurrencyWidget dans l'ordre DOM (ordre d'affichage)."""
        from tui.widgets.currency_widget import CurrencyWidget
        return list(self.query(CurrencyWidget))
