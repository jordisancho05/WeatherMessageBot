"""Daily scheduling.

The configured local ``TIME_SEND_MESSAGE`` is converted to UTC before registering the job; the
message itself still displays the local time and zone (see `formatting`).
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime

import pytz
import schedule

from . import telegram_sender
from .config import Settings

logger = logging.getLogger(__name__)


def to_utc(time_send: str, tz, on_date: date | None = None) -> str:
    """Convert a local ``HH:MM`` for ``tz`` into the equivalent UTC ``HH:MM``."""
    on_date = on_date or datetime.now().date()
    local_time = datetime.strptime(time_send, "%H:%M").time()
    local_aware = tz.localize(datetime.combine(on_date, local_time))
    return local_aware.astimezone(pytz.UTC).strftime("%H:%M")


def _run_once(settings: Settings, tz) -> None:
    """Bridge the sync scheduler to the async send on a fresh event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(telegram_sender.send_weather_message(settings, tz))
    finally:
        loop.close()


def schedule_daily_message(settings: Settings, tz, *, block: bool = True) -> None:
    """Register the daily job at the configured time and (by default) run the loop forever."""
    utc_str = to_utc(settings.time_send_message, tz)
    schedule.every().day.at(utc_str).do(_run_once, settings, tz)
    logger.info(
        "Scheduled daily message at %s (%s) -> %s UTC",
        settings.time_send_message,
        tz.zone,
        utc_str,
    )
    while block:
        schedule.run_pending()
        time.sleep(60)
