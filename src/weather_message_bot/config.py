"""Environment-based configuration.

`load_settings()` reads from `os.environ` only; loading the `.env` file is the caller's
responsibility (see `__main__`), which keeps this module pure and testable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_REQUIRED = ("TELEGRAM_TOKEN", "WEATHER_API_KEY", "CHAT_ID")

_DEFAULTS = {
    "CITY": "Madrid,ES",
    "TIME_SEND_MESSAGE": "07:00",
    "TIMEZONE": "Europe/Madrid",
    # Minimum seconds between two /time replies in the same chat (0 disables the limit).
    "TIME_COMMAND_COOLDOWN": "30",
}


class MissingConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the bot."""

    telegram_token: str
    weather_api_key: str
    chat_id: str
    city: str = _DEFAULTS["CITY"]
    time_send_message: str = _DEFAULTS["TIME_SEND_MESSAGE"]
    timezone: str = _DEFAULTS["TIMEZONE"]
    time_command_cooldown: int = int(_DEFAULTS["TIME_COMMAND_COOLDOWN"])


def _load_cooldown() -> int:
    """Read `TIME_COMMAND_COOLDOWN` as a non-negative int, failing loudly on a bad value."""
    raw = os.environ.get("TIME_COMMAND_COOLDOWN", _DEFAULTS["TIME_COMMAND_COOLDOWN"])
    try:
        seconds = int(raw)
    except ValueError:
        raise MissingConfigError(
            f"TIME_COMMAND_COOLDOWN must be a whole number of seconds, got {raw!r}."
        ) from None
    if seconds < 0:
        raise MissingConfigError(
            f"TIME_COMMAND_COOLDOWN must be zero or positive, got {seconds}."
        )
    return seconds


def load_settings() -> Settings:
    """Build `Settings` from the environment, failing loudly on missing required vars."""
    missing = [key for key in _REQUIRED if not os.environ.get(key)]
    if missing:
        raise MissingConfigError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Create a .env file following .env.example."
        )

    return Settings(
        telegram_token=os.environ["TELEGRAM_TOKEN"],
        weather_api_key=os.environ["WEATHER_API_KEY"],
        chat_id=os.environ["CHAT_ID"],
        city=os.environ.get("CITY", _DEFAULTS["CITY"]),
        time_send_message=os.environ.get("TIME_SEND_MESSAGE", _DEFAULTS["TIME_SEND_MESSAGE"]),
        timezone=os.environ.get("TIMEZONE", _DEFAULTS["TIMEZONE"]),
        time_command_cooldown=_load_cooldown(),
    )
