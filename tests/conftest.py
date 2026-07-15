"""Shared pytest fixtures."""

import pytest

_ENV_KEYS = (
    "TELEGRAM_TOKEN",
    "WEATHER_API_KEY",
    "CHAT_ID",
    "CITY",
    "TIME_SEND_MESSAGE",
    "TIMEZONE",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Isolate config tests from the developer's real environment / .env."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
