"""Pure message-building helpers.

No I/O: given the OpenWeatherMap payloads and a timezone, produce the Spanish message (HTML parse
mode). User-facing text stays in Spanish; code and docstrings in English.
"""

from __future__ import annotations

import html
from datetime import datetime

_NO_WEATHER = "❌ No se pudo obtener información meteorológica"

# Today's max temperature (°C) at which a heat warning / an extreme-heat warning is added.
_HEAT_WARN = 34
_HEAT_EXTREME = 40


def rain_probability(forecast_data: dict | None, now: datetime) -> float:
    """Highest probability of precipitation (``pop``) among today's next-24h intervals (8×3h)."""
    if not forecast_data:
        return 0.0
    window = forecast_data.get("list", [])[:8]
    current_date = now.strftime("%Y-%m-%d")
    today = [entry for entry in window if entry.get("dt_txt", "")[:10] == current_date]
    if not today:
        return 0.0
    return max(entry.get("pop", 0) for entry in today) * 100


def temperature_range(forecast_data: dict | None, now: datetime) -> tuple[float, float] | None:
    """Today's (min, max) temperature from the forecast, or ``None`` if unavailable."""
    if not forecast_data:
        return None
    window = forecast_data.get("list", [])[:8]
    current_date = now.strftime("%Y-%m-%d")
    today = [entry for entry in window if entry.get("dt_txt", "")[:10] == current_date]
    mins = [e["main"]["temp_min"] for e in today if "temp_min" in e.get("main", {})]
    maxs = [e["main"]["temp_max"] for e in today if "temp_max" in e.get("main", {})]
    if not mins or not maxs:
        return None
    return (min(mins), max(maxs))


def heat_warning(max_temp: float | None) -> str:
    """Spanish heat-warning line for today's max temperature; empty string if it isn't hot."""
    if max_temp is None:
        return ""
    if max_temp >= _HEAT_EXTREME:
        return (
            "🥵 <b>Aviso:</b> calor extremo (≥40°C). Evita el sol en las horas centrales, "
            "hidrátate bien y no hagas esfuerzos al aire libre."
        )
    if max_temp >= _HEAT_WARN:
        return (
            "🌡️ <b>Aviso:</b> hará bastante calor. Bebe agua, busca la sombra "
            "y evita el sol del mediodía."
        )
    return ""


def weather_emoji(description: str) -> str:
    """Pick an emoji from the weather description (Spanish or English keywords)."""
    text = description.lower()
    if "lluvia" in text or "rain" in text:
        return "🌧️"
    if "nube" in text or "cloud" in text:
        return "☁️"
    if "nieve" in text or "snow" in text:
        return "❄️"
    if "tormenta" in text or "storm" in text:
        return "⛈️"
    return "☀️"


def recommendation(probability: float) -> str:
    """Spanish recommendation line based on the rain probability."""
    if probability > 50:
        return "☂️ <b>Recomendación:</b> ¡No olvides llevar paraguas hoy!"
    if probability > 20:
        return "🌦️ <b>Recomendación:</b> Posibilidad de lluvia, considera llevar paraguas"
    return "☀️ <b>Recomendación:</b> Día sin lluvia prevista, ¡disfruta!"


def format_weather_message(
    weather_data: dict | None,
    forecast_data: dict | None,
    tz,
    now: datetime | None = None,
) -> str:
    """Build the Spanish Markdown weather message."""
    if not weather_data:
        return _NO_WEATHER

    now = now or datetime.now(tz)

    temp = weather_data["main"]["temp"]
    feels_like = weather_data["main"]["feels_like"]
    humidity = weather_data["main"]["humidity"]
    description = weather_data["weather"][0]["description"].title()
    city_name = weather_data["name"]

    probability = rain_probability(forecast_data, now)
    emoji = weather_emoji(description)
    temp_range = temperature_range(forecast_data, now)

    # HTML parse mode: escape API-provided fields so `< > &` can't break or inject markup.
    safe_city = html.escape(city_name)
    safe_description = html.escape(description)

    if temp_range:
        tmin, tmax = temp_range
        temp_line = (
            f"🌡️ <b>Temperatura:</b> {tmin:.0f}–{tmax:.0f}°C "
            f"(ahora {temp:.1f}°C, se siente como {feels_like:.1f}°C)"
        )
    else:
        temp_line = f"🌡️ <b>Temperatura:</b> {temp:.1f}°C (se siente como {feels_like:.1f}°C)"

    message = f"""🌤️ <b>Buenos días! Aquí tienes el clima de hoy</b>

📍 <b>{safe_city}</b>
{temp_line}
{emoji} <b>Condiciones:</b> {safe_description}
💧 <b>Humedad:</b> {humidity}%
🌧️ <b>Probabilidad de lluvia:</b> {probability:.0f}%

"""
    message += recommendation(probability)

    warning = heat_warning(temp_range[1] if temp_range else None)
    if warning:
        message += f"\n{warning}"

    message += (
        f"\n\n⏰ Enviado automáticamente a las {now.strftime('%H:%M')} ({tz.zone})"
    )
    return message
