# tests/test_logger.py
import logging
import os
from logs.logger import get_logger


def test_logger_returns_named_logger():
    """Test that get_logger returns a logger with the expected name."""
    # Clear any existing handlers to avoid test pollution
    logging.getLogger("dashboard.daemon").handlers.clear()
    logger = get_logger("daemon")
    assert logger.name == "dashboard.daemon"


def test_logger_respects_env_level(monkeypatch, tmp_path):
    """Test that logger respects DASHBOARD_LOG_LEVEL environment variable."""
    import shared.paths as p
    p.LOG_FILE = tmp_path / "dashboard.log"
    monkeypatch.setenv("DASHBOARD_LOG_LEVEL", "DEBUG")
    # Force a fresh logger without handlers
    import logging
    test_logger_name = "dashboard.test_level"
    logging.getLogger(test_logger_name).handlers.clear()

    # Reimport to get fresh logger with new env
    import importlib
    import logs.logger as mod
    importlib.reload(mod)

    logger = mod.get_logger("test_level")
    assert logger.level == logging.DEBUG
