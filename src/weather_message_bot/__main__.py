"""CLI entry point: ``python -m weather_message_bot [--test]``."""

from __future__ import annotations

import asyncio
import logging
import sys

import pytz
from dotenv import load_dotenv

from . import scheduler, telegram_sender
from .config import MissingConfigError, load_settings

logger = logging.getLogger(__name__)


# Third-party loggers that would otherwise emit one INFO line per polling cycle (every ~10s).
# `httpx` is the important one: it logs the full request URL, and python-telegram-bot puts the bot
# token in the path, so at INFO the token would be written to the logs on every single poll.
_NOISY_LOGGERS = ("httpx", "httpcore", "apscheduler")


def _quiet_noisy_loggers() -> None:
    """Raise third-party log levels to WARNING to keep the log readable (and token-free)."""
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _run_test(settings, tz) -> None:
    """Send a single message immediately (the ``--test`` path)."""
    asyncio.run(telegram_sender.send_weather_message(settings, tz))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    _quiet_noisy_loggers()

    # Windows needs the selector loop policy for aiohttp/telegram.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    load_dotenv()
    try:
        settings = load_settings()
    except MissingConfigError as exc:
        logger.error("%s", exc)
        return 1

    tz = pytz.timezone(settings.timezone)

    if "--test" in argv:
        logger.info("Sending a test message...")
        _run_test(settings, tz)
        return 0

    logger.info("Starting weather bot... (press Ctrl+C to stop)")
    try:
        scheduler.run(settings, tz)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
