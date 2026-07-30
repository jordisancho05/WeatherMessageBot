"""Telegram command handlers.

Bots are discoverable by anyone on Telegram, so every handler is gated on the configured
`CHAT_ID`: an unauthorized chat gets a short refusal and no API call is made (the
OpenWeatherMap key has a limited quota). `/time` is additionally rate limited per chat, so
repeated calls cannot burn that quota either. User-facing text stays in Spanish.
"""

from __future__ import annotations

import logging
import time as time_module

from telegram import Update
from telegram.ext import ContextTypes

from . import formatting, weather
from .config import Settings

logger = logging.getLogger(__name__)

# chat_data key holding the monotonic timestamp of the last served /time.
_LAST_TIME_KEY = "last_time_command"

_DENIED = "🚫 Este bot es privado y no está disponible para este chat."
_ERROR = "❌ No se pudo obtener la información meteorológica. Inténtalo más tarde."
_COOLDOWN = "⏳ Espera {seconds}s antes de volver a consultar el tiempo."
_START = (
    "👋 <b>Bot del tiempo</b>\n\n"
    "Comandos disponibles:\n"
    "/time — el tiempo ahora mismo\n"
    "/start — este mensaje\n\n"
    "Además recibirás un resumen automático cada día."
)


def is_authorized(update: Update, settings: Settings) -> bool:
    """True when the update comes from the configured chat.

    `CHAT_ID` is a string in `Settings` while Telegram reports an int, so compare as strings.
    """
    chat = update.effective_chat
    if chat is None:
        return False
    return str(chat.id) == str(settings.chat_id)


def _cooldown_remaining(chat_data: dict, cooldown: int, now: float) -> int:
    """Seconds still to wait before this chat may run `/time` again (0 when allowed).

    Uses a monotonic clock so a system-clock change cannot lock the command out. Rounded up, so a
    non-zero wait never reports "0 seconds".
    """
    if cooldown <= 0:  # 0 disables the limit
        return 0
    last = chat_data.get(_LAST_TIME_KEY)
    if last is None:
        return 0
    elapsed = now - last
    if elapsed >= cooldown:
        return 0
    # Guard against a monotonic value from a previous process (e.g. after a restart).
    if elapsed < 0:
        return 0
    return max(1, round(cooldown - elapsed))


async def _reply(update: Update, text: str) -> None:
    """Answer the incoming message, tolerating a missing message object."""
    if update.effective_message is not None:
        await update.effective_message.reply_text(text, parse_mode="HTML")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ``/start``: show the available commands."""
    settings: Settings = context.bot_data["settings"]
    if not is_authorized(update, settings):
        logger.warning("Rejected /start from unauthorized chat %s", update.effective_chat)
        await _reply(update, _DENIED)
        return
    await _reply(update, _START)


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ``/time``: reply with the current weather for the configured city."""
    settings: Settings = context.bot_data["settings"]
    if not is_authorized(update, settings):
        logger.warning("Rejected /time from unauthorized chat %s", update.effective_chat)
        await _reply(update, _DENIED)
        return

    # Rate limit only after the auth check, so a rejected chat never occupies the cooldown slot.
    chat_data = context.chat_data if context.chat_data is not None else {}
    now = time_module.monotonic()
    remaining = _cooldown_remaining(chat_data, settings.time_command_cooldown, now)
    if remaining:
        logger.info("Rate limited /time; %ss remaining", remaining)
        await _reply(update, _COOLDOWN.format(seconds=remaining))
        return

    tz = context.bot_data["tz"]
    try:
        weather_data = await weather.get_weather_data(settings.city, settings.weather_api_key)
        await _reply(update, formatting.format_current_weather_message(weather_data, tz))
        # Only a served reply starts the cooldown, so a failure doesn't lock the command out.
        chat_data[_LAST_TIME_KEY] = now
        logger.info("Answered /time")
    except Exception:
        # Log the full detail; the chat only sees a generic message (no detail leaked).
        logger.exception("Failed to answer /time")
        await _reply(update, _ERROR)
