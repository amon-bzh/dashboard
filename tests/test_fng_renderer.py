from pathlib import Path
import pytest
from daemon.fng_renderer import render_fng_chart, render_fng_error_chart

SAMPLE_FNG = {
    "current": 72,
    "classification": "Greed",
    "history": {
        f"2025-01-{str(i).zfill(2)}": 50 + i
        for i in range(2, 32)
    },
}

def _is_valid_png(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(8) == b"\x89PNG\r\n\x1a\n"

def test_render_fng_chart_creates_png(tmp_path):
    output = tmp_path / "fng.png"
    render_fng_chart(SAMPLE_FNG, output)
    assert output.exists()
    assert _is_valid_png(output)

def test_render_fng_chart_creates_json_meta(tmp_path):
    output = tmp_path / "fng.png"
    render_fng_chart(SAMPLE_FNG, output)
    import json
    meta = json.loads(output.with_suffix(".json").read_text())
    assert meta["current"] == 72
    assert meta["classification"] == "Greed"
    assert "variation_7d" in meta

def test_render_fng_error_chart_creates_png(tmp_path):
    output = tmp_path / "fng_err.png"
    render_fng_error_chart("timeout", output)
    assert output.exists()
    assert _is_valid_png(output)
