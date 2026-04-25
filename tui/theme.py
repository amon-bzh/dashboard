# tui/theme.py
from textual.theme import Theme

BLOOMBERG = Theme(
    name="bloomberg",
    primary="#ffb020",
    secondary="#22d3ee",
    accent="#22d3ee",
    background="#05070a",
    surface="#0a0d12",
    panel="#05070a",
    warning="#f97316",
    error="#ef4444",
    success="#4ade80",
    dark=True,
    variables={
        "border": "#6b6355",
        "text-muted": "#6b6355",
        "text-disabled": "#3a3530",
    }
)
