"""Tests for env-based configuration loading."""

import pytest

from weather_message_bot.config import MissingConfigError, Settings, load_settings


def _set_required(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "token")
    monkeypatch.setenv("WEATHER_API_KEY", "key")
    monkeypatch.setenv("CHAT_ID", "123")


def test_load_settings_applies_defaults(monkeypatch):
    """Only the required vars set -> optional ones fall back to their defaults."""
    _set_required(monkeypatch)

    settings = load_settings()

    assert settings == Settings(
        telegram_token="token",
        weather_api_key="key",
        chat_id="123",
        city="Madrid,ES",
        time_send_message="07:00",
        timezone="Europe/Madrid",
    )


def test_load_settings_reads_all_values(monkeypatch):
    """Every var set -> read verbatim, no default applied."""
    _set_required(monkeypatch)
    monkeypatch.setenv("CITY", "Barcelona,ES")
    monkeypatch.setenv("TIME_SEND_MESSAGE", "08:30")
    monkeypatch.setenv("TIMEZONE", "Europe/Paris")

    settings = load_settings()

    assert settings.city == "Barcelona,ES"
    assert settings.time_send_message == "08:30"
    assert settings.timezone == "Europe/Paris"


@pytest.mark.parametrize("missing", ["TELEGRAM_TOKEN", "WEATHER_API_KEY", "CHAT_ID"])
def test_missing_required_var_fails_loudly(monkeypatch, missing):
    """A missing required var raises MissingConfigError naming it."""
    _set_required(monkeypatch)
    monkeypatch.delenv(missing)

    with pytest.raises(MissingConfigError) as exc:
        load_settings()

    assert missing in str(exc.value)
