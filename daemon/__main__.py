from __future__ import annotations

import asyncio
import os
import signal

from daemon.fetcher import fetch_rates
from daemon.renderer import render_chart, render_error_chart
from logs.logger import get_logger
from shared.config import load_config
from shared.paths import PID_FILE, ensure_dirs, png_path

logger = get_logger("daemon")
_reload_event: asyncio.Event


def _handle_sighup() -> None:
    logger.info("SIGHUP reçu — rechargement de la configuration")
    _reload_event.set()


async def generate_png(pair: str, scale: str) -> None:
    path = png_path(pair, scale)
    logger.debug(f"Génération {pair} {scale} → {path.name}")
    try:
        rates = await fetch_rates(pair, scale)
        render_chart(rates, pair, scale, path)
        logger.info(f"PNG généré : {path.name}")
    except Exception as exc:
        logger.error(f"Échec {pair} {scale} : {exc}")
        render_error_chart(pair, str(exc), path)


async def generate_all(config) -> None:
    tasks = [generate_png(w.pair, w.scale) for w in config.widgets]
    await asyncio.gather(*tasks)


async def main() -> None:
    global _reload_event
    _reload_event = asyncio.Event()

    ensure_dirs()
    PID_FILE.write_text(str(os.getpid()))
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGHUP, _handle_sighup)
    logger.info("Daemon démarré")

    try:
        while True:
            _reload_event.clear()
            config = load_config()
            await generate_all(config)

            interval = config.refresh_interval_minutes * 60
            logger.info(f"Pause de {config.refresh_interval_minutes} min")
            try:
                await asyncio.wait_for(_reload_event.wait(), timeout=interval)
                logger.info("Rechargement déclenché par SIGHUP")
            except asyncio.TimeoutError:
                logger.info("Rafraîchissement planifié")
    finally:
        PID_FILE.unlink(missing_ok=True)
        logger.info("Daemon arrêté")


if __name__ == "__main__":
    asyncio.run(main())
