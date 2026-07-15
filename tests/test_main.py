"""Tests for the CLI entry point (collaborators mocked, no network)."""

from unittest.mock import MagicMock

import weather_message_bot.__main__ as entry
from weather_message_bot.config import MissingConfigError, Settings

_SETTINGS = Settings(telegram_token="t", weather_api_key="k", chat_id="123")


def _stub_config(monkeypatch, settings=_SETTINGS):
    monkeypatch.setattr(entry, "load_dotenv", lambda: None)
    monkeypatch.setattr(entry, "load_settings", lambda: settings)


def test_test_flag_runs_oneshot_not_scheduler(monkeypatch):
    _stub_config(monkeypatch)
    run_test = MagicMock()
    schedule = MagicMock()
    monkeypatch.setattr(entry, "_run_test", run_test)
    monkeypatch.setattr(entry.scheduler, "schedule_daily_message", schedule)

    assert entry.main(["--test"]) == 0
    run_test.assert_called_once()
    schedule.assert_not_called()


def test_default_runs_scheduler_not_oneshot(monkeypatch):
    _stub_config(monkeypatch)
    run_test = MagicMock()
    schedule = MagicMock()
    monkeypatch.setattr(entry, "_run_test", run_test)
    monkeypatch.setattr(entry.scheduler, "schedule_daily_message", schedule)

    assert entry.main([]) == 0
    schedule.assert_called_once()
    run_test.assert_not_called()


def test_missing_config_returns_nonzero(monkeypatch):
    monkeypatch.setattr(entry, "load_dotenv", lambda: None)

    def _raise():
        raise MissingConfigError("TELEGRAM_TOKEN")

    monkeypatch.setattr(entry, "load_settings", _raise)

    assert entry.main([]) == 1
