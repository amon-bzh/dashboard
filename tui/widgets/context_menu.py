from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from textual.message import Message

FOCUS_COLOR = "#00b4d8"


class ContextMenu(Widget):
    """Menu contextuel flottant pour un CurrencyWidget."""

    DEFAULT_CSS = f"""
    ContextMenu {{
        layer: overlay;
        border: solid {FOCUS_COLOR};
        background: $surface;
        width: 24;
        height: auto;
        padding: 0;
    }}
    ContextMenu Label {{
        height: 1;
        padding: 0 1;
    }}
    ContextMenu Label:hover {{
        background: {FOCUS_COLOR};
        color: $background;
    }}
    """

    class EditPair(Message):
        pass

    class ChangeScale(Message):
        pass

    class DeleteWidget(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Label("✎  Modifier la paire", id="menu-edit")
        yield Label("⊞  Changer l'échelle", id="menu-scale")
        yield Label("✕  Supprimer", id="menu-delete")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.remove()
            event.stop()

    def on_label_click(self, event) -> None:
        label_id = event.widget.id
        if label_id == "menu-edit":
            self.post_message(self.EditPair())
        elif label_id == "menu-scale":
            self.post_message(self.ChangeScale())
        elif label_id == "menu-delete":
            self.post_message(self.DeleteWidget())
        self.remove()
