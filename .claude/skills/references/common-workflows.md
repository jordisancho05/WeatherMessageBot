# Common Workflows — WeatherMessageBot

> Loaded by `planner` (domain-analysis Step 3) and `implementer` when a change matches one of these
> recipes. Each recipe lists the files to touch in order and the test that pins it.

## Add a config variable
1. `config.py` → add the field to `Settings`; `os.getenv('NAME', default)` (or required-check if no
   sane default). Document it in `.env.example` **and** the README config table.
2. Consumer module reads it from `Settings`, never `os.getenv` directly.
3. Test: `tests/test_config.py` → default applied when unset; value read when set; required var missing
   → fails loudly (`monkeypatch.delenv`).
- Gotcha: if the var is a secret, it stays in `.env` only — never in `docker-compose.yaml` or the
  workflow.

## Add a field to the weather message
1. `weather.py` → make sure the OpenWeatherMap response already carries it (current vs forecast
   endpoint); no new call if it's in the existing payload.
2. `formatting.py` → add the line to `format_weather_message()` (Spanish label + emoji) and, if it's a
   derived value, a small pure helper.
3. Test: `tests/test_formatting.py` → feed a sample payload dict, assert the new line renders; add a
   `parametrize` case if it branches.

## Change the schedule / time handling
1. `scheduler.py` → the daily job registration lives here (`build_application`).
2. Register on PTB's `JobQueue` with `run_daily(callback, time=parse_daily_time(HH:MM, tz))` — the
   `time` must carry `tzinfo` so it resolves correctly on a local or a UTC/Docker clock. Don't
   reintroduce manual UTC math. The message still displays the local time + zone.
3. The job callback receives the `Application`'s Bot: pass it through as
   `send_weather_message(..., bot=context.bot, manage_bot=False)`. Never let the job shut that Bot
   down — it would stop command polling.
4. Test: `tests/test_scheduler.py` → assert `parse_daily_time()` returns the expected tz-aware `time`,
   and that `build_application()` registers exactly one `run_daily` job (mock the builder;
   machine-independent, no polling).

## Add a command (e.g. `/foo`)
1. `commands.py` → add an `async def foo_command(update, context)` handler. **First line of work must
   be the `is_authorized()` gate**: on failure reply `_DENIED` and `return` before any API call —
   Telegram bots are public, and the OpenWeatherMap key has a limited quota.
2. Read config from `context.bot_data["settings"]` / `["tz"]`, not module globals.
3. If the command hits OpenWeatherMap, rate limit it **after** the auth gate: reuse
   `_cooldown_remaining(context.chat_data, cooldown, time.monotonic())` and record the timestamp only
   once the reply was actually served (a failure must not lock the user out). Per-chat state belongs
   in `chat_data`, never a module global.
4. Wrap the work in `try/except`: log the detail, reply a generic Spanish error (never leak internals).
5. `scheduler.py` → register it: `application.add_handler(CommandHandler("foo", commands.foo_command))`.
6. `commands.py` → list it in `_START` so `/start` stays accurate.
7. Test: `tests/test_commands.py` → owner chat gets the content; a stranger chat gets the refusal
   **and** the fetch is `assert_not_awaited()`; a raising fetch is handled without leaking the detail.
   If rate limited: a quick repeat is refused with no API call, and it works again after the cooldown.
8. Docs: the README command table and the `/newbot` command list in BotFather (optional).

## Add a command-line flag
1. `__main__.py` → parse `sys.argv` (or `argparse`); keep `--test` behavior intact.
2. Test: `tests/test_main.py` (or extend) → invoke the entry with the flag via monkeypatched
   collaborators; assert the branch taken, no real network/Telegram.

## Bump the version (SemVer)
1. Decide bump: **patch** (fix), **minor** (backward-compatible feat), **major** (breaking).
2. `bump-my-version bump <part>` → updates `pyproject.toml`, commits, and tags `vX.Y.Z`.
3. Move the `CHANGELOG.md` `## [Unreleased]` entries under a new `## [X.Y.Z] - <date>` heading.
4. `git push --follow-tags`. CI publishes the image; tag the release if desired.
- Single source of truth: version lives in `pyproject.toml`; `__version__` reads it via
  `importlib.metadata`. Never hardcode the version in two places.
