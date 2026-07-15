"""Tests for the pure message-building layer."""

from datetime import datetime

import pytest
import pytz

from weather_message_bot import formatting

_TZ = pytz.timezone("Europe/Madrid")
_NOW = _TZ.localize(datetime(2026, 7, 15, 7, 0))

_WEATHER = {
    "main": {"temp": 22.5, "feels_like": 24.1, "humidity": 65},
    "weather": [{"description": "cielo despejado"}],
    "name": "Madrid",
}


def _forecast_with_rain(n_rain: int):
    """Build a `list` of 8 3h intervals dated today, `n_rain` of them carrying rain."""
    day = _NOW.strftime("%Y-%m-%d")
    items = []
    for i in range(8):
        entry = {"dt_txt": f"{day} {i * 3:02d}:00:00"}
        if i < n_rain:
            entry["rain"] = {"3h": 1.0}
        items.append(entry)
    return {"list": items}


def test_returns_error_string_when_no_weather():
    assert formatting.format_weather_message(None, None, _TZ, now=_NOW).startswith("❌")


def test_message_includes_core_fields():
    msg = formatting.format_weather_message(_WEATHER, None, _TZ, now=_NOW)
    assert "Madrid" in msg
    assert "22.5°C" in msg
    assert "se siente como 24.1°C" in msg
    assert "Cielo Despejado" in msg  # .title() applied
    assert "65%" in msg
    assert "(Europe/Madrid)" in msg
    assert "07:00" in msg


@pytest.mark.parametrize(
    "forecast, expected",
    [
        (None, 0),
        ({"list": []}, 0),
    ],
)
def test_rain_probability_zero_cases(forecast, expected):
    assert formatting.rain_probability(forecast, _NOW) == expected


def test_rain_probability_counts_today_rain_over_window():
    # 2 rainy intervals out of an 8-interval window -> 25%
    assert formatting.rain_probability(_forecast_with_rain(2), _NOW) == 25.0


@pytest.mark.parametrize(
    "description, emoji",
    [
        ("lluvia ligera", "🌧️"),
        ("light rain", "🌧️"),
        ("nubes dispersas", "☁️"),
        ("nieve", "❄️"),
        ("tormenta", "⛈️"),
        ("cielo despejado", "☀️"),
    ],
)
def test_weather_emoji(description, emoji):
    assert formatting.weather_emoji(description) == emoji


@pytest.mark.parametrize(
    "probability, snippet",
    [
        (80, "¡No olvides llevar paraguas hoy!"),
        (30, "considera llevar paraguas"),
        (5, "¡disfruta!"),
    ],
)
def test_recommendation_branches(probability, snippet):
    assert snippet in formatting.recommendation(probability)
