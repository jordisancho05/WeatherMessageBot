"""Tests for the command handlers, focused on the chat_id authorization gate (no network)."""

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import pytz

from weather_message_bot import commands
from weather_message_bot.config import Settings

_TZ = pytz.timezone("Europe/Madrid")
_SETTINGS = Settings(telegram_token="t", weather_api_key="k", chat_id="123")
_WEATHER = {
    "main": {"temp": 22.5, "feels_like": 24.1, "humidity": 65},
    "weather": [{"description": "cielo despejado"}],
    "name": "Madrid",
}


def _update(chat_id):
    """Build an Update whose effective_chat has the given id and a mocked reply."""
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_message.reply_text = AsyncMock()
    return update


def _context(settings=_SETTINGS, chat_data=None):
    context = MagicMock()
    context.bot_data = {"settings": settings, "tz": _TZ}
    context.chat_data = {} if chat_data is None else chat_data
    return context


def _reply_text(update):
    return update.effective_message.reply_text.await_args.kwargs.get(
        "text", update.effective_message.reply_text.await_args.args[0]
    )


def test_is_authorized_compares_int_chat_id_against_string_setting():
    """Telegram reports an int chat id while Settings holds a string."""
    assert commands.is_authorized(_update(123), _SETTINGS)
    assert not commands.is_authorized(_update(999), _SETTINGS)


async def test_time_replies_with_current_weather_for_the_owner(monkeypatch):
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    update = _update(123)

    await commands.time_command(update, _context())

    fetch.assert_awaited_once_with("Madrid,ES", "k")
    text = _reply_text(update)
    assert "Madrid" in text
    assert "22.5" in text


async def test_time_from_stranger_is_refused_without_calling_the_api(monkeypatch):
    """An unauthorized chat must not burn OpenWeatherMap quota."""
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    update = _update(999)

    await commands.time_command(update, _context())

    fetch.assert_not_awaited()
    assert "privado" in _reply_text(update)


async def test_start_from_stranger_is_refused():
    update = _update(999)

    await commands.start_command(update, _context())

    assert "privado" in _reply_text(update)


async def test_start_lists_commands_for_the_owner():
    update = _update(123)

    await commands.start_command(update, _context())

    assert "/time" in _reply_text(update)


async def test_time_failure_notifies_without_leaking_detail(monkeypatch):
    monkeypatch.setattr(
        commands.weather,
        "get_weather_data",
        AsyncMock(side_effect=RuntimeError("boom secret detail")),
    )
    update = _update(123)

    await commands.time_command(update, _context())  # must not raise

    text = _reply_text(update)
    assert "❌" in text
    assert "boom secret detail" not in text  # internal detail stays in the log


async def test_time_handles_unavailable_weather(monkeypatch):
    """A failed fetch returns None, which the formatter turns into the fallback message."""
    monkeypatch.setattr(commands.weather, "get_weather_data", AsyncMock(return_value=None))
    update = _update(123)

    await commands.time_command(update, _context())

    assert "❌" in _reply_text(update)


# --- rate limiting -------------------------------------------------------------------------


async def test_second_time_call_is_rate_limited_without_calling_the_api(monkeypatch):
    """A quick repeat is refused and, crucially, spends no OpenWeatherMap quota."""
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    context = _context()  # shared chat_data across both calls

    await commands.time_command(_update(123), context)
    assert fetch.await_count == 1

    second = _update(123)
    await commands.time_command(second, context)

    assert fetch.await_count == 1  # no second API call
    assert "Espera" in _reply_text(second)


async def test_time_is_served_again_after_the_cooldown_elapses(monkeypatch):
    """Once the cooldown passes the command works normally again."""
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    context = _context()

    await commands.time_command(_update(123), context)
    # Pretend the recorded call happened a full cooldown ago.
    context.chat_data[commands._LAST_TIME_KEY] -= _SETTINGS.time_command_cooldown

    third = _update(123)
    await commands.time_command(third, context)

    assert fetch.await_count == 2
    assert "Madrid" in _reply_text(third)


async def test_zero_cooldown_disables_rate_limiting(monkeypatch):
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    settings = replace(_SETTINGS, time_command_cooldown=0)
    context = _context(settings=settings)

    await commands.time_command(_update(123), context)
    await commands.time_command(_update(123), context)

    assert fetch.await_count == 2


async def test_failed_fetch_does_not_start_the_cooldown(monkeypatch):
    """A failure must not lock the user out; the retry should go through."""
    fetch = AsyncMock(side_effect=[RuntimeError("boom"), _WEATHER])
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    context = _context()

    await commands.time_command(_update(123), context)
    retry = _update(123)
    await commands.time_command(retry, context)

    assert fetch.await_count == 2
    assert "Madrid" in _reply_text(retry)


async def test_rate_limit_is_per_chat(monkeypatch):
    """PTB gives each chat its own chat_data, so one chat's cooldown can't block another."""
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)

    await commands.time_command(_update(123), _context())
    other_chat = _update(123)
    await commands.time_command(other_chat, _context())  # separate chat_data

    assert fetch.await_count == 2


async def test_unauthorized_chat_does_not_consume_the_cooldown(monkeypatch):
    """A stranger must not be able to put the owner's /time on cooldown."""
    fetch = AsyncMock(return_value=_WEATHER)
    monkeypatch.setattr(commands.weather, "get_weather_data", fetch)
    context = _context()

    await commands.time_command(_update(999), context)
    assert commands._LAST_TIME_KEY not in context.chat_data

    owner = _update(123)
    await commands.time_command(owner, context)

    assert fetch.await_count == 1
    assert "Madrid" in _reply_text(owner)


def test_cooldown_remaining_rounds_up_and_handles_edge_cases():
    cooldown = 30
    assert commands._cooldown_remaining({}, cooldown, now=100.0) == 0  # no previous call
    assert commands._cooldown_remaining({commands._LAST_TIME_KEY: 100.0}, 0, now=100.0) == 0
    # 29.9s elapsed still reports a wait of at least 1s, never 0.
    assert commands._cooldown_remaining({commands._LAST_TIME_KEY: 100.0}, cooldown, 129.9) == 1
    assert commands._cooldown_remaining({commands._LAST_TIME_KEY: 100.0}, cooldown, 130.0) == 0
    # A timestamp in the future (stale monotonic after a restart) must not lock the command out.
    assert commands._cooldown_remaining({commands._LAST_TIME_KEY: 500.0}, cooldown, 100.0) == 0
