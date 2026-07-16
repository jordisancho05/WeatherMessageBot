"""Daily scheduling.

The daily job is registered at the configured local ``TIME_SEND_MESSAGE`` **in the configured
timezone**: `schedule` (>=1.2) resolves it against the given zone, so it fires at the right
wall-clock time whether the host runs in that timezone (local) or in UTC (Docker).
"""

from __future__ import annotations

import asyncio
import logging
import time

import schedule

from . import telegram_sender
from .config import Settings

logger = logging.getLogger(__name__)

# How often the loop checks for due jobs (seconds).
_POLL_SECONDS = 20


def _run_once(settings: Settings, tz) -> None:
    """Bridge the sync scheduler to the async send on a fresh event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(telegram_sender.send_weather_message(settings, tz))
    finally:
        loop.close()


def schedule_daily_message(settings: Settings, tz, *, block: bool = True) -> None:
    """Register the daily job at the configured time/zone and (by default) run the loop forever."""
    schedule.every().day.at(settings.time_send_message, settings.timezone).do(
        _run_once, settings, tz
    )
    logger.info(
        "Scheduled daily message at %s (%s)", settings.time_send_message, settings.timezone
    )
    while block:
        schedule.run_pending()
        time.sleep(_POLL_SECONDS)
