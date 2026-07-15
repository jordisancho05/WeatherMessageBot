"""Pure message-building helpers.

No I/O: given the OpenWeatherMap payloads and a timezone, produce the Spanish Markdown message.
User-facing text stays in Spanish; code and docstrings in English.
"""

from __future__ import annotations

import html
from datetime import datetime

_NO_WEATHER = "❌ No se pudo obtener información meteorológica"


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

    # HTML parse mode: escape API-provided fields so `< > &` can't break or inject markup.
    safe_city = html.escape(city_name)
    safe_description = html.escape(description)

    message = f"""🌤️ <b>Buenos días! Aquí tienes el clima de hoy</b>

📍 <b>{safe_city}</b>
🌡️ <b>Temperatura:</b> {temp:.1f}°C (se siente como {feels_like:.1f}°C)
{emoji} <b>Condiciones:</b> {safe_description}
💧 <b>Humedad:</b> {humidity}%
🌧️ <b>Probabilidad de lluvia:</b> {probability:.0f}%

"""
    message += recommendation(probability)
    message += (
        f"\n\n⏰ Enviado automáticamente a las {now.strftime('%H:%M')} ({tz.zone})"
    )
    return message
