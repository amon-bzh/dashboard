# tests/test_config.py
import json
from pathlib import Path
import pytest
from shared.config import DashboardConfig, WidgetConfig, load_config, save_config

def test_default_config_has_three_widgets():
    cfg = DashboardConfig()
    assert len(cfg.widgets) == 3
    assert cfg.widgets[0].pair == "EUR/USD"

def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path / "cache")
    (tmp_path / "cache").mkdir()

    cfg = DashboardConfig(
        base_currency="USD",
        refresh_interval_minutes=30,
        grid_columns=3,
        widgets=[WidgetConfig("GBP/JPY", "6M")],
    )
    save_config(cfg)
    loaded = load_config()
    assert loaded.base_currency == "USD"
    assert loaded.refresh_interval_minutes == 30
    assert loaded.grid_columns == 3
    assert loaded.widgets[0].pair == "GBP/JPY"
    assert loaded.widgets[0].scale == "6M"

def test_load_config_creates_default_if_missing(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path / "cache")
    (tmp_path / "cache").mkdir()
    cfg = load_config()
    assert isinstance(cfg, DashboardConfig)
    assert (tmp_path / "config.json").exists()
