# WeatherMessageBot — Architecture

> Detailed architecture. Day-to-day rules live in `CLAUDE.md` (repo root).

Telegram bot in Python. Once a day, at a configurable local time, it fetches the current weather and a
5-day forecast from OpenWeatherMap, builds a Spanish message (temperature, conditions, rain
chance, a recommendation) and sends it to a Telegram chat. It also serves the `/time` and `/start`
commands on demand, restricted to the configured chat.

## Package map (`src/weather_message_bot/`)
- `__init__.py` — exposes `__version__` (read from installed metadata via `importlib.metadata`).
- `__main__.py` — CLI entry point (`python -m weather_message_bot [--test]`): loads config, builds the
  bot, runs the bot (daily job + polling) or the one-shot `--test` send. Forces
  `WindowsSelectorEventLoopPolicy` on Windows.
- `config.py` — `Settings` loaded from env (`.env` via `python-dotenv`). Required:
  `TELEGRAM_TOKEN`, `WEATHER_API_KEY`, `CHAT_ID`. Optional with defaults: `CITY` (`Madrid,ES`),
  `TIME_SEND_MESSAGE` (`07:00`), `TIMEZONE` (`Europe/Madrid`), `TIME_COMMAND_COOLDOWN` (`30`, the
  `/time` rate limit in seconds; `0` disables it). Missing a required var — or a non-integer/negative
  cooldown — fails loudly with `MissingConfigError`.
- `weather.py` — async OpenWeatherMap client: `get_weather_data()` (current) and
  `get_forecast_data()` (5-day / 3h), both bounded by a 10s `ClientTimeout`. **Graceful degradation**:
  return `None` + log on HTTP 401/404/other, never raise.
- `formatting.py` — pure functions: rain probability = max `pop` among today's next-24h (8×3h)
  intervals, `temperature_range()` (today's min–max from the forecast), `heat_warning()` (extra line
  at ≥34°C / ≥40°C), weather emoji from the description, and `format_weather_message()` building the
  Spanish body (HTML parse mode; API-provided fields `html.escape`d; shows the temp range + current),
  plus `format_current_weather_message()` — the short `/time` reply, current conditions only (no
  forecast call needed, so it stays cheap in API quota).
- `telegram_sender.py` — wraps `telegram.Bot`; `send_weather_message()` orchestrates fetch → format →
  `send_message(parse_mode='HTML')`. With `manage_bot=True` (default, the `--test` one-shot) it drives
  the Bot lifecycle via `async with bot:` (initialize/shutdown → deterministic pool close); with
  `manage_bot=False` (the daily job) it reuses the `Application`'s already-initialized Bot, since
  shutting that one down would stop polling. On failure logs the detail and sends the chat a generic
  message; all failures swallowed.
- `commands.py` — command handlers `/time` (current weather) and `/start` (help), plus
  `is_authorized()`. **Telegram bots are discoverable by anyone**, so every handler gates on the
  configured `CHAT_ID` (compared as strings — Telegram reports an int) and an unauthorized chat gets a
  Spanish refusal with **no** OpenWeatherMap call. Handlers read `settings`/`tz` from
  `context.bot_data` rather than closing over them, which keeps them testable.
  `/time` is additionally rate limited by `_cooldown_remaining()`: one reply per
  `TIME_COMMAND_COOLDOWN` seconds per chat, so repeated calls can't burn the quota either. State is
  the last-served monotonic timestamp in PTB's per-chat `chat_data` (never a module global, which
  would leak across chats). Two deliberate choices: the check runs *after* the auth gate so a stranger
  can't occupy the owner's cooldown slot, and the timestamp is recorded only after a **served** reply
  so a failed lookup can be retried at once.
- `scheduler.py` — `build_application()` builds the PTB `Application`, registers the `/start` and
  `/time` handlers, seeds `bot_data`, and schedules the daily job on the `JobQueue` via `run_daily`
  with a tz-aware `datetime.time` (`parse_daily_time()`, correct on a local or a UTC/Docker clock).
  `run()` calls `run_polling()`, so the daily job and command polling share one asyncio loop.

## Layering
`config` → `weather` (client) + `formatting` (pure) → `telegram_sender` (send) + `commands`
(handlers) → `scheduler` (Application: daily job + polling) → `__main__` (CLI). Times use `pytz`;
scheduling is timezone-aware via a tz-aware `time` on the `JobQueue` and the message shows the local
time and zone. Network failures degrade gracefully and must never crash the daily loop.

## Stack and versioning
See `CLAUDE.md` (root) and `.github/copilot-instructions.md` (Stack section = canonical dependency
versions). Version follows SemVer, single-sourced in `pyproject.toml`, tagged `vX.Y.Z` in git and
tracked in `CHANGELOG.md`.
