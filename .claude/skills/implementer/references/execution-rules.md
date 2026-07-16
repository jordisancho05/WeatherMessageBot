# Execution Rules — how to implement in WeatherMessageBot

> Canonical mechanics for writing code in this repo. The `implementer` skill applies them per plan
> subtask; `CLAUDE.md` makes the TDD cycle mandatory for **any** code change, plan or not.

## Inverse TDD (mandatory for every code change)
1. Write the tests that pin the expected behavior first (`pytest`).
2. Run them and **confirm they FAIL (red)** before implementing.
3. Implement until they **PASS (green)**.
4. Don't move on with red tests.
5. If a behavior can't be unit-tested (real Telegram send, real OpenWeatherMap call), say so
   **explicitly**: name what is uncovered and how it was verified instead (it belongs in the plan's
   `Uncovered / manual verification` section, verified via `python -m weather_message_bot --test`).
   Never claim it works without running it.
- Test style per layer: `@.claude/skills/planner/references/test-quality-rules.md`.

## Retry cap
- If a test is still red after **3 distinct implementation attempts** (different approaches, not
  re-runs), STOP: record the failure in the plan's `## Deviations` section (per
  `annotation-format.md`) and ask the user. Grinding past 3 attempts hides a wrong plan assumption.

## Run / test
- Commands via `@.claude/skills/references/common-commands.md` (`pytest`, `ruff`, `pip install -e
  ".[dev]"`, `python -m weather_message_bot`). Tests must never hit the network or a real Telegram bot:
  stub aiohttp with `aioresponses`, mock `telegram.Bot` with `AsyncMock`.
- A step isn't green until `pytest` for it passes **and** `ruff check .` is clean on the touched files.

## Project rules
- Apply every **`CLAUDE.md` "Always Remember"** gotcha — it is always in context, so the list is not
  restated here (secrets in `.env` only; English code / Spanish Telegram text; graceful network
  degradation).
- Code-style additions not in `CLAUDE.md`:
  - **Type hints** on new public functions.
  - New code logs via the `logging` module, not `print` (the legacy `weather_bot.py` used `print`;
    don't propagate it into the new package).
  - Read config from a `Settings` object, never `os.getenv` scattered across modules.
  - Timezone math goes through `pytz`; never inline a second source of "now".

## Scope
- Implement **only** what the plan describes. If an ambiguity or uncovered requirement appears, **STOP
  and ask**; don't improvise outside the plan (the plan's `## Out of scope` is the boundary).
