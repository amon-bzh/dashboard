# tests/test_paths.py
from pathlib import Path
from shared.paths import CONFIG_DIR, CACHE_DIR, png_path, ensure_dirs

def test_png_path_naming():
    p = png_path("EUR/USD", "1M")
    assert p.name == "EUR_USD_1M.png"
    assert p.parent == CACHE_DIR

def test_ensure_dirs_creates_directories(tmp_path, monkeypatch):
    monkeypatch.setattr("shared.paths.CONFIG_DIR", tmp_path / "dashboard")
    monkeypatch.setattr("shared.paths.CACHE_DIR", tmp_path / "dashboard" / "cache")
    from shared import paths
    paths.CONFIG_DIR = tmp_path / "dashboard"
    paths.CACHE_DIR = tmp_path / "dashboard" / "cache"
    paths.ensure_dirs()
    assert paths.CONFIG_DIR.exists()
    assert paths.CACHE_DIR.exists()
