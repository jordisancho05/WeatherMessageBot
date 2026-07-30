"""Tests for the bot runtime: daily-job registration and handler wiring (no network)."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytz

from weather_message_bot import scheduler
from weather_message_bot.config import Settings

_TZ = pytz.timezone("Europe/Madrid")
_SETTINGS = Settings(
    telegram_token="t",
    weather_api_key="k",
    chat_id="123",
    time_send_message="03:42",
    timezone="Europe/Madrid",
)


def test_parse_daily_time_is_timezone_aware():
    """The daily time carries the configured zone, so it is machine-clock independent."""
    parsed = scheduler.parse_daily_time("03:42", _TZ)

    assert parsed == time(3, 42, tzinfo=_TZ)
    assert parsed.tzinfo is _TZ


def test_build_application_registers_daily_job_and_commands(monkeypatch):
    """The Application gets both command handlers and one daily job at the configured time."""
    application = MagicMock()
    application.bot_data = {}
    builder = MagicMock()
    builder.token.return_value = builder
    builder.build.return_value = application
    monkeypatch.setattr(scheduler.Application, "builder", lambda: builder)

    result = scheduler.build_application(_SETTINGS, _TZ)

    assert result is application
    builder.token.assert_called_once_with("t")

    # Handlers are registered for /start and /time.
    registered = [call.args[0] for call in application.add_handler.call_args_list]
    assert len(registered) == 2
    assert {name for handler in registered for name in handler.commands} == {"start", "time"}

    # Exactly one daily job, at the configured local time and zone.
    application.job_queue.run_daily.assert_called_once()
    kwargs = application.job_queue.run_daily.call_args.kwargs
    assert kwargs["time"] == time(3, 42, tzinfo=_TZ)

    # Handlers read config from bot_data.
    assert application.bot_data["settings"] is _SETTINGS
    assert application.bot_data["tz"] is _TZ


async def test_daily_job_reuses_the_application_bot(monkeypatch):
    """The daily job must not shut down the shared Bot, or polling would stop."""
    send = AsyncMock()
    monkeypatch.setattr(scheduler.telegram_sender, "send_weather_message", send)
    context = MagicMock()
    context.bot_data = {"settings": _SETTINGS, "tz": _TZ}

    await scheduler._daily_job(context)

    send.assert_awaited_once_with(_SETTINGS, _TZ, bot=context.bot, manage_bot=False)
