from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget


class CurrencyWidget(Widget):
    """Stub — sera implémenté en Task 10."""

    def __init__(self, pair: str, scale: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pair = pair
        self.scale = scale

    def compose(self) -> ComposeResult:
        return
        yield  # type: ignore[misc]

    def refresh_if_updated(self) -> None:
        """Stub — sera implémenté en Task 10."""
        pass
