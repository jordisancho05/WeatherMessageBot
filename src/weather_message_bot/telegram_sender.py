"""Telegram sending layer.

Orchestrates fetch → format → send. On failure it still tries to notify the chat of the error
(user-facing text stays in Spanish); a secondary failure is swallowed so the daily loop survives.
"""

from __future__ import annotations

import logging

from telegram import Bot

from . import formatting, weather
from .config import Settings

logger = logging.getLogger(__name__)


async def send_weather_message(settings: Settings, tz, bot: Bot | None = None) -> None:
    """Fetch the weather and send the formatted message to the configured chat."""
    bot = bot or Bot(token=settings.telegram_token)
    try:
        weather_data = await weather.get_weather_data(settings.city, settings.weather_api_key)
        forecast_data = await weather.get_forecast_data(settings.city, settings.weather_api_key)
        message = formatting.format_weather_message(weather_data, forecast_data, tz)

        await bot.send_message(chat_id=settings.chat_id, text=message, parse_mode="Markdown")
        logger.info("Weather message sent successfully")
    except Exception as exc:
        logger.exception("Failed to send weather message")
        try:
            await bot.send_message(
                chat_id=settings.chat_id,
                text=f"❌ Error al obtener información meteorológica: {exc}",
            )
        except Exception:
            logger.exception("Failed to send the error notification too")
