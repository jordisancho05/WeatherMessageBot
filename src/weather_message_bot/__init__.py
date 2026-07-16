"""Telegram bot that sends a daily weather message from OpenWeatherMap."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("weather-message-bot")
except PackageNotFoundError:  # not installed (e.g. running from a raw checkout)
    __version__ = "0.0.0"

__all__ = ["__version__"]
