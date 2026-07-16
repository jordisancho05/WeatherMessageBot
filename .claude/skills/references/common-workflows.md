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
1. `scheduler.py` → the daily job registration lives here.
2. Register with `schedule.every().day.at(TIME_SEND_MESSAGE, TIMEZONE)` — pass the zone so `schedule`
   resolves it correctly on a local or a UTC/Docker clock. Don't reintroduce manual UTC math. The
   message still displays the local time + zone.
3. Test: `tests/test_scheduler.py` → schedule the job with `block=False` and assert `schedule.jobs[0]`
   has the expected `at_time` and `at_time_zone` (machine-independent; don't run the loop).

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
