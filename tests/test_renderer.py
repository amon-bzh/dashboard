from pathlib import Path
import pytest
from daemon.renderer import render_chart, render_error_chart

SAMPLE_RATES = {
    "2025-01-02": 1.050,
    "2025-01-03": 1.055,
    "2025-01-06": 1.048,
    "2025-01-07": 1.060,
    "2025-01-08": 1.072,
}

def _is_valid_png(path: Path) -> bool:
    with open(path, "rb") as f:
        header = f.read(8)
    return header == b"\x89PNG\r\n\x1a\n"

def test_render_chart_creates_png(tmp_path):
    output = tmp_path / "test.png"
    render_chart(SAMPLE_RATES, "EUR/USD", "1M", output)
    assert output.exists()
    assert _is_valid_png(output)

def test_render_chart_green_when_up(tmp_path):
    output = tmp_path / "up.png"
    rates = {"2025-01-02": 1.00, "2025-01-03": 1.10}
    render_chart(rates, "EUR/USD", "1M", output)
    assert output.exists()

def test_render_error_chart_creates_png(tmp_path):
    output = tmp_path / "error.png"
    render_error_chart("EUR/XYZ", "Paire invalide", output)
    assert output.exists()
    assert _is_valid_png(output)
