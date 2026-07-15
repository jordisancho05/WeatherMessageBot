# WeatherMessageBot — Architecture

> Detailed architecture. Day-to-day rules live in `CLAUDE.md` (repo root).

Telegram bot in Python. Once a day, at a configurable local time, it fetches the current weather and a
5-day forecast from OpenWeatherMap, builds a Spanish message (temperature, conditions, rain
chance, a recommendation) and sends it to a Telegram chat.

## Package map (`src/weather_message_bot/`)
- `__init__.py` — exposes `__version__` (read from installed metadata via `importlib.metadata`).
- `__main__.py` — CLI entry point (`python -m weather_message_bot [--test]`): loads config, builds the
  bot, runs the scheduler or the one-shot `--test` send. Forces `WindowsSelectorEventLoopPolicy` on
  Windows.
- `config.py` — `Settings` loaded from env (`.env` via `python-dotenv`). Required:
  `TELEGRAM_TOKEN`, `WEATHER_API_KEY`, `CHAT_ID`. Optional with defaults: `CITY` (`Madrid,ES`),
  `TIME_SEND_MESSAGE` (`07:00`), `TIMEZONE` (`Europe/Madrid`). Missing a required var fails loudly.
- `weather.py` — async OpenWeatherMap client: `get_weather_data()` (current) and
  `get_forecast_data()` (5-day / 3h), both bounded by a 10s `ClientTimeout`. **Graceful degradation**:
  return `None` + log on HTTP 401/404/other, never raise.
- `formatting.py` — pure functions: rain probability = max `pop` among today's next-24h (8×3h)
  intervals, weather emoji from the description, and `format_weather_message()` building the Spanish
  body (HTML parse mode; API-provided fields `html.escape`d).
- `telegram_sender.py` — wraps `telegram.Bot`; `send_weather_message()` orchestrates fetch → format →
  `send_message(parse_mode='HTML')`; on failure logs the detail and sends the chat a generic message.
- `scheduler.py` — `schedule_daily_message()` registers the daily `schedule` job at the local
  `TIME_SEND_MESSAGE` in the configured timezone (via `schedule`'s native tz support, correct on a
  local or a UTC/Docker clock); loops `run_pending()`; bridges sync `schedule` to the async send on a
  fresh event loop.

## Layering
`config` → `weather` (client) + `formatting` (pure) → `telegram_sender` (send) → `scheduler` (cron
loop) → `__main__` (CLI). Times use `pytz`; scheduling is timezone-aware via `schedule`'s tz support
and the message shows the local time and zone. Network failures degrade gracefully and must never crash the daily
loop.

## Stack and versioning
See `CLAUDE.md` (root) and `.github/copilot-instructions.md` (Stack section = canonical dependency
versions). Version follows SemVer, single-sourced in `pyproject.toml`, tagged `vX.Y.Z` in git and
tracked in `CHANGELOG.md`.
