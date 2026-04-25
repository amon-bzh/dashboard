from pathlib import Path
import pytest
from daemon.vix_renderer import render_vix_chart, render_vix_error_chart

SAMPLE_VIX = {
    "2025-01-02": 18.5,
    "2025-01-03": 19.2,
    "2025-01-06": 17.8,
    "2025-01-07": 21.3,
    "2025-01-08": 20.1,
}

def _is_valid_png(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(8) == b"\x89PNG\r\n\x1a\n"

def test_render_vix_chart_creates_png(tmp_path):
    output = tmp_path / "vix.png"
    render_vix_chart(SAMPLE_VIX, "1M", output)
    assert output.exists()
    assert _is_valid_png(output)

def test_render_vix_chart_creates_json_meta(tmp_path):
    output = tmp_path / "vix.png"
    render_vix_chart(SAMPLE_VIX, "1M", output)
    import json
    meta = json.loads(output.with_suffix(".json").read_text())
    assert "current" in meta
    assert "variation_pct" in meta
    assert meta["current"] == pytest.approx(20.1, abs=0.01)

def test_render_vix_error_chart_creates_png(tmp_path):
    output = tmp_path / "vix_err.png"
    render_vix_error_chart("timeout", output)
    assert output.exists()
    assert _is_valid_png(output)
