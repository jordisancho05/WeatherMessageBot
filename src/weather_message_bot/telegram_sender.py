"""Telegram sending layer.

Orchestrates fetch → format → send. When this module owns the Bot (the ``--test`` one-shot) it is
used through its async lifecycle (``async with bot:`` → ``initialize()`` on enter, ``shutdown()`` on
exit) so the httpx connection pool is closed deterministically. When the Bot belongs to a running
`Application` (the daily job) pass ``manage_bot=False``: it is already initialized and shutting it
down would kill the polling. On failure it still tries to notify the chat of the error (user-facing
text stays in Spanish); every failure — including entering the Bot context — is logged and swallowed
so the daily loop survives.
"""

from __future__ import annotations

import contextlib
import logging

from telegram import Bot

from . import formatting, weather
from .config import Settings

logger = logging.getLogger(__name__)


async def send_weather_message(
    settings: Settings, tz, bot: Bot | None = None, *, manage_bot: bool = True
) -> None:
    """Fetch the weather and send the formatted message to the configured chat."""
    bot = bot or Bot(token=settings.telegram_token)
    # Only drive the Bot lifecycle when we own it; a shared Application Bot must stay running.
    lifecycle = bot if manage_bot else contextlib.AsyncExitStack()
    try:
        async with lifecycle:
            try:
                weather_data = await weather.get_weather_data(
                    settings.city, settings.weather_api_key
                )
                forecast_data = await weather.get_forecast_data(
                    settings.city, settings.weather_api_key
                )
                message = formatting.format_weather_message(weather_data, forecast_data, tz)

                await bot.send_message(chat_id=settings.chat_id, text=message, parse_mode="HTML")
                logger.info("Weather message sent successfully")
            except Exception:
                # Log the full detail; send the chat only a generic message (no detail leaked).
                logger.exception("Failed to send weather message")
                await bot.send_message(
                    chat_id=settings.chat_id,
                    text="❌ No se pudo obtener la información meteorológica. Inténtalo más tarde.",
                )
    except Exception:
        # Entering/leaving the Bot context or the fallback notice failed — log, never raise.
        logger.exception("Weather message could not be delivered")
