"""Tests for the async OpenWeatherMap client (network stubbed)."""

import re

from aioresponses import aioresponses

from weather_message_bot import weather

_CURRENT = re.compile(r"^https://api\.openweathermap\.org/data/2\.5/weather.*")
_FORECAST = re.compile(r"^https://api\.openweathermap\.org/data/2\.5/forecast.*")


async def test_get_weather_data_returns_json_on_200():
    payload = {"main": {"temp": 20.0}, "name": "Madrid"}
    with aioresponses() as mocked:
        mocked.get(_CURRENT, status=200, payload=payload)
        result = await weather.get_weather_data("Madrid,ES", "key")
    assert result == payload


async def test_get_forecast_data_returns_json_on_200():
    payload = {"list": []}
    with aioresponses() as mocked:
        mocked.get(_FORECAST, status=200, payload=payload)
        result = await weather.get_forecast_data("Madrid,ES", "key")
    assert result == payload


async def test_returns_none_and_logs_on_401(caplog):
    with aioresponses() as mocked:
        mocked.get(_CURRENT, status=401)
        result = await weather.get_weather_data("Madrid,ES", "bad-key")
    assert result is None
    assert any("401" in r.message or "API key" in r.message for r in caplog.records)


async def test_returns_none_on_404():
    with aioresponses() as mocked:
        mocked.get(_CURRENT, status=404)
        result = await weather.get_weather_data("Nowhere,XX", "key")
    assert result is None


async def test_returns_none_on_server_error():
    with aioresponses() as mocked:
        mocked.get(_CURRENT, status=500)
        result = await weather.get_weather_data("Madrid,ES", "key")
    assert result is None


async def test_returns_none_on_exception():
    """A raised transport error degrades to None, never propagates."""
    with aioresponses() as mocked:
        mocked.get(_CURRENT, exception=ConnectionError("boom"))
        result = await weather.get_weather_data("Madrid,ES", "key")
    assert result is None
