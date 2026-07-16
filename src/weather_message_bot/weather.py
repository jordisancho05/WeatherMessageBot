"""Async OpenWeatherMap client.

Graceful degradation: on any HTTP error or transport failure the fetchers return ``None`` and log;
they never raise, so a failed call cannot crash the daily loop.
"""

from __future__ import annotations

import logging

import aiohttp

logger = logging.getLogger(__name__)

_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Bound every request so a hung connection cannot block the daily loop forever.
_TIMEOUT = aiohttp.ClientTimeout(total=10)


async def _fetch(url: str, city: str, api_key: str) -> dict | None:
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "es"}
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 401:
                    logger.error("OpenWeatherMap 401: invalid or missing API key")
                elif response.status == 404:
                    logger.error("OpenWeatherMap 404: city '%s' not found", city)
                else:
                    logger.error("OpenWeatherMap error: HTTP %s", response.status)
                return None
    except Exception:
        logger.exception("OpenWeatherMap request failed")
        return None


async def get_weather_data(city: str, api_key: str) -> dict | None:
    """Fetch current weather for ``city``; ``None`` on failure."""
    return await _fetch(_CURRENT_URL, city, api_key)


async def get_forecast_data(city: str, api_key: str) -> dict | None:
    """Fetch the 5-day / 3-hour forecast for ``city``; ``None`` on failure."""
    return await _fetch(_FORECAST_URL, city, api_key)
