# GitHub Copilot Instructions — WeatherMessageBot

> This file is kept in sync with `CLAUDE.md` (repo root). See it for the full picture.

Telegram bot in **Python**. Once a day, at a configurable time, it fetches the weather from
OpenWeatherMap and sends a formatted message (temperature, conditions, chance of rain, a
recommendation) to a Telegram chat. It also answers `/time` (weather right now) and `/start` on
demand. Packaged app under `src/weather_message_bot/`.

## Always Remember
- **Never commit secrets.** `TELEGRAM_TOKEN`, `WEATHER_API_KEY` and `CHAT_ID` live in `.env` only
  (already gitignored). Never hardcode them in `docker-compose.yaml`, workflows, or code.
- **Code language split**: comments, logs and docstrings in **English**; user-facing Telegram text
  (the weather message, recommendations) in **Spanish** — don't translate those literals.
- **Every new command handler must gate on `commands.is_authorized()`** before doing any work.
  Telegram bots are discoverable by anyone; an unauthorized chat must get the refusal and trigger
  **no** OpenWeatherMap call (the API key has a limited quota).
- **Don't commit or push** unless explicitly asked.

## Stack
- **Python 3.11**
- `python-telegram-bot[job-queue]` 20.7 — Telegram Bot API, command polling and the daily
  `JobQueue` job (the extra brings APScheduler)
- `aiohttp` 3.9.1 — async HTTP calls to OpenWeatherMap
- `python-dotenv` 1.0.0 — load `.env`
- `pytz` — time-zone handling
- Dev: `pytest`, `pytest-asyncio`, `aioresponses`, `ruff`, `bump-my-version` (the `dev` extra).

## Run & Test
```bash
pip install -e ".[dev]"        # editable install + dev tools
python main.py                  # run the bot: daily job + command polling (root launcher)
python main.py --test           # send one message immediately and exit
# equivalent: python -m weather_message_bot | weather-message-bot (console script)
pytest                          # test suite (no network / no real Telegram)
ruff check .                    # lint
```
Docker: `docker build -f DockerFile -t weather-telegram-bot:latest .` then `docker compose up -d`.

## Architecture (`src/weather_message_bot/`)
- `config.py` — `Settings` + `load_settings()` (env; required token/api-key/chat-id, defaulted
  city/time/timezone/`TIME_COMMAND_COOLDOWN`).
- `weather.py` — async `get_weather_data()` / `get_forecast_data()`; return `None` and **log** on
  HTTP 401/404/other, never raise.
- `formatting.py` — pure `rain_probability()` (max `pop` today), `temperature_range()` (today's
  min–max), `heat_warning()` (≥34°C / ≥40°C), `weather_emoji()`, `recommendation()`,
  `format_weather_message()` (Spanish, HTML parse mode; shows temp range + current) and
  `format_current_weather_message()` (the short `/time` reply; current conditions only, no forecast).
  API-provided fields are `html.escape`d.
- `telegram_sender.py` — `send_weather_message()` orchestrates fetch → format →
  `bot.send_message(parse_mode='HTML')`; `manage_bot=True` (default, the `--test` one-shot) drives the
  Bot lifecycle via `async with bot:` (initialize/shutdown), `manage_bot=False` (the daily job) reuses
  the `Application`'s running Bot untouched; on failure logs the detail and sends the chat a generic
  message (no internal detail leaked); all failures swallowed.
- `commands.py` — `/time` and `/start` handlers plus `is_authorized()`, restricting every command to
  `CHAT_ID` (compared as strings: Telegram reports an int). Handlers read `settings`/`tz` from
  `context.bot_data`; unauthorized chats get the refusal and no API call is made. `/time` is then rate
  limited per chat via `_cooldown_remaining()` (monotonic clock, state in `chat_data`; recorded only
  after a served reply).
- `scheduler.py` — `build_application()` wires the handlers and registers the daily job on PTB's
  `JobQueue` via `run_daily` with a tz-aware `datetime.time` (`parse_daily_time()`) — correct on a
  local or a UTC/Docker clock; `run()` calls `run_polling()`, so the daily job and command polling
  share one asyncio loop.
- `__main__.py` — `main()` (parses `--test`, `WindowsSelectorEventLoopPolicy` on win32, loads `.env`,
  runs the bot or the one-shot send). `__init__.py` exposes `__version__`.

## Conventions
- Read config from the `Settings` object, not scattered `os.getenv`. New code logs via `logging`,
  not `print`. Type-hint new public functions.
- Times are handled with `pytz`; scheduling is timezone-aware via a tz-aware `time` on PTB's
  `JobQueue` (no manual UTC math), and the message shows the local time and zone.
- Network failures degrade gracefully (return `None`, log, and still try to notify the chat of the
  error) — keep that pattern; don't let a failed API call crash the daily loop.
