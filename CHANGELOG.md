# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **`/time` command**: ask the bot for the current weather on demand. Replies with a short
  "right now" message (temperature, feels-like, conditions, humidity) built by the new
  `format_current_weather_message()`; it needs only the current-weather call, no forecast.
- **`/start` command** listing the available commands.
- **Authorization gate** (`commands.is_authorized`): Telegram bots are discoverable by anyone, so
  every command is restricted to the configured `CHAT_ID`. An unauthorized chat gets a short refusal
  and **no** OpenWeatherMap call is made, so strangers cannot burn the API quota.
- **Rate limiting on `/time`**: one reply per chat every `TIME_COMMAND_COOLDOWN` seconds (new env
  var, default `30`, `0` disables it). A repeat inside the window is answered with the remaining wait
  and makes no API call. The cooldown starts only on a *served* reply, so a failed lookup can be
  retried immediately; timestamps use a monotonic clock, so a system-clock change cannot lock the
  command out. State lives in PTB's per-chat `chat_data`. `/start` is not limited (it calls no API).

### Changed
- The bot now runs as a `python-telegram-bot` `Application` with polling, so it both listens for
  commands and sends the daily message from a single asyncio loop. `scheduler.run()` replaces
  `scheduler.schedule_daily_message()`.
- The daily job moved from `schedule` to PTB's `JobQueue` (`run_daily` with a timezone-aware
  `datetime.time`), keeping the correct wall-clock behavior on both a local and a UTC/Docker clock.
- `send_weather_message()` accepts `manage_bot=False` so the daily job reuses the `Application`'s
  already-initialized Bot instead of shutting down its connection pool (which would stop polling).

### Removed
- The `schedule` dependency (replaced by PTB's `JobQueue`, which arrives via the new
  `python-telegram-bot[job-queue]` extra).

## [1.0.0] - 2026-07-16

First stable release.

### Added
- Message now shows today's **temperature range** (min–max from the forecast) alongside the current
  temperature, e.g. `27–32°C (ahora 29°C, se siente como 31°C)`. Falls back to just the current
  temperature when the forecast is unavailable.
- **Heat warnings**: an extra line when today's max reaches 34°C (stay hydrated / avoid midday sun)
  or 40°C (extreme-heat warning). Thresholds are `_HEAT_WARN` / `_HEAT_EXTREME` in `formatting.py`.
- 10s request timeout (`aiohttp.ClientTimeout`) on the OpenWeatherMap calls so a hung connection
  cannot block the daily loop.

### Changed
- The Telegram `Bot` is now used through its async lifecycle (`async with bot:` → `initialize()` /
  `shutdown()`), closing the httpx connection pool deterministically per send. Graceful degradation is
  preserved: a failure entering the Bot context is logged and never raises.
- Weather message now uses Telegram **HTML** parse mode with API-provided fields `html.escape`d, so a
  `_ * [ <` in a city name or description can no longer break (or inject into) the message.
- Rain probability is now the max `pop` (probability of precipitation) among today's forecast
  intervals, instead of the fraction of intervals carrying a `rain` key.

### Fixed
- On a send failure the chat now receives a generic message; the internal exception detail stays in
  the log instead of being sent to the user.
- **Daily job fired at the wrong time when not running in UTC.** The schedule was computed by
  converting the local time to UTC and handing the UTC string to `schedule`, which fires against the
  *host* clock — so on a machine whose clock isn't UTC (e.g. a local run in `Europe/Madrid`) the job
  ran offset by the UTC difference (and often skipped to the next day). Now the job is registered with
  `schedule.every().day.at(TIME_SEND_MESSAGE, TIMEZONE)`, timezone-aware and correct on both a local
  and a UTC/Docker clock. The loop also polls every 20s instead of 60s.

## [0.1.0] - 2026-07-15

### Added
- `src/`-layout package `weather_message_bot` with a `python -m weather_message_bot` /
  `weather-message-bot` entry point.
- `pyproject.toml` with pinned runtime deps, a `dev` extra (pytest, pytest-asyncio, aioresponses,
  ruff, bump-my-version), ruff and pytest configuration, and SemVer versioning.
- pytest suite covering config, weather client, message formatting, Telegram sender, scheduler,
  entry point and version (no network / no real Telegram).
- This changelog and single-sourced `__version__`.

### Changed
- Split the single-file `weather_bot.py` into `config`, `weather`, `formatting`, `telegram_sender`,
  `scheduler` and `__main__` modules (behavior preserved).
- New package code logs via the `logging` module instead of `print`.
- Docker image now installs the package and runs `python -m weather_message_bot`.

### Removed
- `weather_bot.py` (replaced by the package).
- `requirements.txt` (dependencies now live in `pyproject.toml`).

[Unreleased]: https://github.com/jordisancho05/WeatherMessageBot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jordisancho05/WeatherMessageBot/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/jordisancho05/WeatherMessageBot/releases/tag/v0.1.0
