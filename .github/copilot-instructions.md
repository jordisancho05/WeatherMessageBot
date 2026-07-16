# GitHub Copilot Instructions — WeatherMessageBot

> This file is kept in sync with `CLAUDE.md` (repo root). See it for the full picture.

Telegram bot in **Python**. Once a day, at a configurable time, it fetches the weather from
OpenWeatherMap and sends a formatted message (temperature, conditions, chance of rain, a
recommendation) to a Telegram chat. Packaged app under `src/weather_message_bot/`.

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
- Dev: `pytest`, `pytest-asyncio`, `aioresponses`, `ruff`, `bump-my-version` (the `dev` extra).

## Run & Test
```bash
pip install -e ".[dev]"        # editable install + dev tools
python main.py                  # run the daily scheduler (root launcher)
python main.py --test           # send one message immediately and exit
# equivalent: python -m weather_message_bot | weather-message-bot (console script)
pytest                          # test suite (no network / no real Telegram)
ruff check .                    # lint
```
Docker: `docker build -f DockerFile -t weather-telegram-bot:latest .` then `docker compose up -d`.

## Architecture (`src/weather_message_bot/`)
- `config.py` — `Settings` + `load_settings()` (env; required token/api-key/chat-id, defaulted
  city/time/timezone).
- `weather.py` — async `get_weather_data()` / `get_forecast_data()`; return `None` and **log** on
  HTTP 401/404/other, never raise.
- `formatting.py` — pure `rain_probability()` (max `pop` today), `temperature_range()` (today's
  min–max), `heat_warning()` (≥34°C / ≥40°C), `weather_emoji()`, `recommendation()`,
  `format_weather_message()` (Spanish, HTML parse mode; shows temp range + current). API-provided
  fields are `html.escape`d.
- `telegram_sender.py` — `send_weather_message()` orchestrates fetch → format →
  `bot.send_message(parse_mode='HTML')` inside `async with bot:` (initialize/shutdown); on failure
  logs the detail and sends the chat a generic message (no internal detail leaked); all failures
  swallowed.
- `scheduler.py` — `schedule_daily_message()` registers the daily job at the local
  `TIME_SEND_MESSAGE` in the configured timezone (via `schedule`'s native tz support — correct on a
  local or a UTC/Docker clock), loops `run_pending()`; bridges sync `schedule` to the async send.
- `__main__.py` — `main()` (parses `--test`, `WindowsSelectorEventLoopPolicy` on win32, loads `.env`,
  runs scheduler or one-shot send). `__init__.py` exposes `__version__`.

## Conventions
- Read config from the `Settings` object, not scattered `os.getenv`. New code logs via `logging`,
  not `print`. Type-hint new public functions.
- Times are handled with `pytz`; scheduling is timezone-aware via `schedule`'s tz support (no manual
  UTC math), and the message shows the local time and zone.
- Network failures degrade gracefully (return `None`, log, and still try to notify the chat of the
  error) — keep that pattern; don't let a failed API call crash the daily loop.
