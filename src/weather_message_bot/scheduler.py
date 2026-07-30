"""Bot runtime: daily job + command polling.

Both live in a single `Application` so one asyncio loop drives everything. The daily message is
registered on PTB's `JobQueue` via ``run_daily`` with a timezone-aware `time`, so it fires at the
right wall-clock time whether the host runs in that timezone (local) or in UTC (Docker).
"""

from __future__ import annotations

import logging
from datetime import time as dt_time

from telegram.ext import Application, CommandHandler

from . import commands, telegram_sender
from .config import Settings

logger = logging.getLogger(__name__)


def parse_daily_time(time_send_message: str, tz) -> dt_time:
    """Parse ``HH:MM`` into a timezone-aware `time` for `JobQueue.run_daily`."""
    hour, minute = (int(part) for part in time_send_message.split(":"))
    return dt_time(hour=hour, minute=minute, tzinfo=tz)


async def _daily_job(context) -> None:
    """JobQueue callback: send the daily weather message reusing the shared Bot."""
    settings: Settings = context.bot_data["settings"]
    tz = context.bot_data["tz"]
    await telegram_sender.send_weather_message(settings, tz, bot=context.bot, manage_bot=False)


def build_application(settings: Settings, tz) -> Application:
    """Build the `Application` with the command handlers and the daily job registered."""
    application = Application.builder().token(settings.telegram_token).build()

    # Handlers read config from bot_data instead of closing over it, so they stay testable.
    application.bot_data["settings"] = settings
    application.bot_data["tz"] = tz

    application.add_handler(CommandHandler("start", commands.start_command))
    application.add_handler(CommandHandler("time", commands.time_command))

    application.job_queue.run_daily(
        _daily_job, time=parse_daily_time(settings.time_send_message, tz), name="daily_weather"
    )
    logger.info(
        "Scheduled daily message at %s (%s); listening for /time",
        settings.time_send_message,
        settings.timezone,
    )
    return application


def run(settings: Settings, tz) -> None:
    """Run the bot: daily job plus command polling, until interrupted."""
    build_application(settings, tz).run_polling()
