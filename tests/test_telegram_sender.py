"""Tests for the Telegram sending layer (Bot mocked, no network)."""

from unittest.mock import AsyncMock

import pytz

from weather_message_bot import telegram_sender
from weather_message_bot.config import Settings

_TZ = pytz.timezone("Europe/Madrid")
_SETTINGS = Settings(telegram_token="t", weather_api_key="k", chat_id="123")
_WEATHER = {
    "main": {"temp": 22.5, "feels_like": 24.1, "humidity": 65},
    "weather": [{"description": "cielo despejado"}],
    "name": "Madrid",
}


def _stub_weather(monkeypatch, weather_value=_WEATHER, forecast_value=None):
    monkeypatch.setattr(
        telegram_sender.weather, "get_weather_data", AsyncMock(return_value=weather_value)
    )
    monkeypatch.setattr(
        telegram_sender.weather, "get_forecast_data", AsyncMock(return_value=forecast_value)
    )


async def test_sends_formatted_message_as_markdown(monkeypatch):
    _stub_weather(monkeypatch)
    bot = AsyncMock()

    await telegram_sender.send_weather_message(_SETTINGS, _TZ, bot=bot)

    bot.send_message.assert_awaited_once()
    kwargs = bot.send_message.await_args.kwargs
    assert kwargs["chat_id"] == "123"
    assert kwargs["parse_mode"] == "HTML"
    assert "Madrid" in kwargs["text"]


async def test_send_failure_notifies_chat_without_leaking_detail(monkeypatch):
    _stub_weather(monkeypatch)
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=[RuntimeError("boom secret detail"), None])

    await telegram_sender.send_weather_message(_SETTINGS, _TZ, bot=bot)

    assert bot.send_message.await_count == 2
    error_text = bot.send_message.await_args_list[1].kwargs["text"]
    assert "❌" in error_text
    assert "boom secret detail" not in error_text  # internal detail stays in the log


async def test_secondary_failure_is_swallowed(monkeypatch):
    """If even the error notification fails, the call still returns cleanly."""
    _stub_weather(monkeypatch)
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=RuntimeError("always down"))

    await telegram_sender.send_weather_message(_SETTINGS, _TZ, bot=bot)  # must not raise
