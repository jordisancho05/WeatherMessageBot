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


def _forecast_with_pops(pops: list[float], day: str | None = None):
    """Build a `list` of 3h intervals dated `day` (today by default) with the given `pop` values."""
    day = day or _NOW.strftime("%Y-%m-%d")
    items = [
        {"dt_txt": f"{day} {i * 3:02d}:00:00", "pop": pop} for i, pop in enumerate(pops)
    ]
    return {"list": items}


def _forecast_with_temps(ranges: list[tuple[float, float]], day: str | None = None):
    """Build today's 3h intervals carrying (temp_min, temp_max) in `main`."""
    day = day or _NOW.strftime("%Y-%m-%d")
    items = [
        {
            "dt_txt": f"{day} {i * 3:02d}:00:00",
            "main": {"temp_min": tmin, "temp_max": tmax},
            "pop": 0,
        }
        for i, (tmin, tmax) in enumerate(ranges)
    ]
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
    assert "<b>" in msg  # rendered as HTML


def test_dynamic_fields_are_html_escaped():
    """API-provided fields with HTML-special chars are escaped, not injected raw."""
    weather = {**_WEATHER, "name": "Tom & Jerry"}
    msg = formatting.format_weather_message(weather, None, _TZ, now=_NOW)
    assert "Tom &amp; Jerry" in msg
    assert "Tom & Jerry" not in msg


@pytest.mark.parametrize(
    "forecast, expected",
    [
        (None, 0),
        ({"list": []}, 0),
    ],
)
def test_rain_probability_zero_cases(forecast, expected):
    assert formatting.rain_probability(forecast, _NOW) == expected


def test_rain_probability_uses_max_pop_of_today():
    # highest probability of precipitation among today's intervals -> 40%
    assert formatting.rain_probability(_forecast_with_pops([0.1, 0.4, 0.2]), _NOW) == 40.0


def test_rain_probability_ignores_other_days():
    assert formatting.rain_probability(_forecast_with_pops([0.9], day="2020-01-01"), _NOW) == 0.0


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


def test_temperature_range_returns_today_min_and_max():
    forecast = _forecast_with_temps([(20, 28), (22, 32), (19, 30)])
    assert formatting.temperature_range(forecast, _NOW) == (19, 32)


@pytest.mark.parametrize(
    "forecast",
    [
        None,
        {"list": []},
        _forecast_with_pops([0.5]),  # intervals without a `main` block
    ],
)
def test_temperature_range_none_when_unavailable(forecast):
    assert formatting.temperature_range(forecast, _NOW) is None


def test_temperature_range_ignores_other_days():
    forecast = _forecast_with_temps([(10, 40)], day="2020-01-01")
    assert formatting.temperature_range(forecast, _NOW) is None


@pytest.mark.parametrize(
    "max_temp, expected",
    [
        (None, ""),
        (28, ""),
        (33.9, ""),
        (34, "calor"),  # normal warning
        (39, "calor"),
        (40, "extremo"),  # extreme warning
        (45, "extremo"),
    ],
)
def test_heat_warning_thresholds(max_temp, expected):
    result = formatting.heat_warning(max_temp)
    if expected:
        assert expected in result
        assert result  # non-empty
    else:
        assert result == ""


def test_extreme_warning_is_not_the_normal_one():
    assert "extremo" in formatting.heat_warning(41)
    assert "extremo" not in formatting.heat_warning(35)


def test_message_shows_range_and_current_temperature():
    forecast = _forecast_with_temps([(24, 27), (25, 32)])
    msg = formatting.format_weather_message(_WEATHER, forecast, _TZ, now=_NOW)
    assert "24–32°C" in msg  # min-max range for today
    assert "ahora 22.5°C" in msg  # current temperature
    assert "se siente como 24.1°C" in msg


def test_message_falls_back_to_current_temp_without_forecast():
    msg = formatting.format_weather_message(_WEATHER, None, _TZ, now=_NOW)
    assert "22.5°C" in msg
    assert "ahora" not in msg  # no range -> no "ahora" wording


def test_message_includes_heat_warning_when_hot():
    forecast = _forecast_with_temps([(28, 35)])  # max 35 -> warning
    msg = formatting.format_weather_message(_WEATHER, forecast, _TZ, now=_NOW)
    assert "Aviso" in msg


def test_message_has_no_heat_warning_when_mild():
    forecast = _forecast_with_temps([(18, 24)])  # max 24 -> no warning
    msg = formatting.format_weather_message(_WEATHER, forecast, _TZ, now=_NOW)
    assert "Aviso" not in msg
