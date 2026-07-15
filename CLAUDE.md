# CLAUDE.md

Guidance for Claude Code (and other agents) working in this repo. `.github/copilot-instructions.md`
is kept in sync with this file.

## What this is
Telegram bot in **Python**. Once a day, at a configurable time, it fetches the weather from
OpenWeatherMap and sends a formatted message (temperature, conditions, chance of rain, a
recommendation) to a Telegram chat. Single-file app: `weather_bot.py`.

## Always Remember
- **Never commit secrets.** `TELEGRAM_TOKEN`, `WEATHER_API_KEY` and `CHAT_ID` live in `.env` only
  (already gitignored). Never hardcode them in `docker-compose.yaml`, workflows, or code.
- **Code language split**: comments, logs and docstrings in **English**; user-facing Telegram text
  (the weather message, recommendations) in **Spanish** — don't translate those literals.
- **Don't commit or push** unless explicitly asked.

## Stack
- **Python 3.11**
- `python-telegram-bot` 20.7 — Telegram Bot API
- `aiohttp` 3.9.1 — async HTTP calls to OpenWeatherMap
- `schedule` 1.2.0 — daily job scheduling
- `python-dotenv` 1.0.0 — load `.env`
- `pytz` — time-zone handling

## Run & Test
```bash
pip install -r requirements.txt
python weather_bot.py          # run the daily scheduler
python weather_bot.py --test   # send one message immediately and exit
```
Docker: `docker build -f DockerFile -t weather-telegram-bot:latest .` then `docker compose up -d`
(reads config from `.env`). CI builds and pushes the image to GHCR on push to `master`
(`.github/workflows/docker-publish.yml`).

There is no automated test suite; verify changes with `--test` against a real bot/chat.

## Architecture (`weather_bot.py`)
- `WeatherBot` class holds all logic:
  - `get_weather_data()` / `get_forecast_data()` — async calls to OpenWeatherMap (current + 5-day
    forecast). Both return `None` and print a diagnostic on HTTP 401/404/other, never raise.
  - `format_weather_message()` — builds the Spanish Markdown message; derives the emoji from the
    description and the rain chance from the next 24h of forecast (8 × 3h intervals).
  - `send_weather_message()` — orchestrates fetch → format → `bot.send_message(parse_mode='Markdown')`.
  - `schedule_daily_message()` — converts local `TIME_SEND_MESSAGE` to UTC, registers the daily job,
    loops `run_pending()` every 60s.
  - `run_async_task()` — bridges `schedule` (sync) to the async send on a fresh event loop.
- `main()` reads config from env (`TELEGRAM_TOKEN`, `WEATHER_API_KEY`, `CHAT_ID` required; `CITY`,
  `TIME_SEND_MESSAGE`, `TIMEZONE` have defaults), validates required vars, then runs the scheduler or
  the `--test` path. On Windows it forces `WindowsSelectorEventLoopPolicy`.

## Conventions
- Times use `pytz`; the scheduler works in UTC internally but the message shows the local time/zone.
- Network failures degrade gracefully (return `None`, print, still try to notify the chat of the
  error) — keep that pattern; a failed API call must not crash the daily loop.
