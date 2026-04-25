from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "dashboard"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"
PID_FILE = CONFIG_DIR / "daemon.pid"
LOG_FILE = CONFIG_DIR / "dashboard.log"


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def png_path(pair: str, scale: str) -> Path:
    base, quote = pair.split("/")
    return CACHE_DIR / f"{base}_{quote}_{scale}.png"


def vix_png_path(scale: str) -> Path:
    return CACHE_DIR / f"VIX_{scale}.png"


def fng_png_path() -> Path:
    return CACHE_DIR / "FNG.png"
