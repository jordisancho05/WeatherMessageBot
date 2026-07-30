# CLAUDE.md

Guidance for Claude Code (and other agents) working in this repo. `.github/copilot-instructions.md`
is kept in sync with this file.

## What this is
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
Docker: `docker build -f DockerFile -t weather-telegram-bot:latest .` then `docker compose up -d`
(reads config from `.env`). CI builds and pushes the image to GHCR on push to `master`
(`.github/workflows/docker-publish.yml`). Full commands: `.claude/skills/references/common-commands.md`.

## Architecture (`src/weather_message_bot/`)
- `config.py` — `Settings` (frozen dataclass) + `load_settings()` reading env; required
  `TELEGRAM_TOKEN`/`WEATHER_API_KEY`/`CHAT_ID`, defaulted
  `CITY`/`TIME_SEND_MESSAGE`/`TIMEZONE`/`TIME_COMMAND_COOLDOWN` (int seconds, validated).
- `weather.py` — async `get_weather_data()` / `get_forecast_data()`; return `None` and **log** on
  HTTP 401/404/other, never raise.
- `formatting.py` — pure `rain_probability()` (max `pop` today), `temperature_range()` (today's
  min–max), `heat_warning()` (≥34°C / ≥40°C), `weather_emoji()`, `recommendation()`,
  `format_weather_message()` (Spanish, HTML parse mode; shows temp range + current) and
  `format_current_weather_message()` (the short `/time` reply; current conditions only, no forecast).
  API-provided fields are `html.escape`d.
- `telegram_sender.py` — `send_weather_message()` orchestrates fetch → format →
  `bot.send_message(parse_mode='HTML')`; with `manage_bot=True` (default, the `--test` one-shot) it
  drives the Bot lifecycle via `async with bot:` (initialize/shutdown → pool closed), with
  `manage_bot=False` (the daily job) it reuses the `Application`'s running Bot untouched. On failure
  logs the detail and sends the chat a generic message (no internal detail leaked); every failure,
  including entering the Bot context, is swallowed.
- `commands.py` — `/time` and `/start` handlers plus `is_authorized()`, which restricts every command
  to `CHAT_ID` (compared as strings: Telegram reports an int). Handlers read `settings`/`tz` from
  `context.bot_data`. Unauthorized chats get `_DENIED` and no API call is made. `/time` is then rate
  limited by `_cooldown_remaining()` (monotonic clock, state in per-chat `chat_data`); the cooldown is
  recorded only after a served reply, so a failure doesn't lock the command out.
- `scheduler.py` — `build_application()` wires the handlers and registers the daily job on PTB's
  `JobQueue` via `run_daily` with a tz-aware `datetime.time` (`parse_daily_time()`) — correct on a
  local or a UTC/Docker clock; `run()` calls `run_polling()`, so the daily job and command polling
  share one asyncio loop.
- `__main__.py` — `main()` parses `--test`, forces `WindowsSelectorEventLoopPolicy` on win32, loads
  `.env`, builds `Settings`, runs the bot (`scheduler.run`) or the one-shot send. `__init__.py`
  exposes `__version__` (from installed metadata).

## Conventions
- Read config from the `Settings` object, never scattered `os.getenv`. New code logs via `logging`,
  not `print`. Type-hint new public functions.
- Times use `pytz`; scheduling is timezone-aware via a tz-aware `time` on PTB's `JobQueue` (no manual
  UTC math), and the message shows the local time/zone.
- Network failures degrade gracefully (return `None`, log, still try to notify the chat of the
  error) — keep that pattern; a failed API call must not crash the daily loop.
- Version is single-sourced in `pyproject.toml` (SemVer); changes tracked in `CHANGELOG.md`.
