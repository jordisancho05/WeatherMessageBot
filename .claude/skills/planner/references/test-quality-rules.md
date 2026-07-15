# Test Quality Rules — how to test in WeatherMessageBot

> Used by the `planner` skill to write each GRAPH STEP's **Tests** block, and by `implementer` when
> running them. Reflects the intended conventions in `tests/` (pytest).

## TDD-first (mandatory)
The red→green cycle is defined once, in
`@.claude/skills/implementer/references/execution-rules.md` (canonical); it applies to every code
subtask. Build/test via `@.claude/skills/references/common-commands.md` (`pytest`). This file only
defines **how the tests themselves are written**.

## Style per layer
- **Pure logic / formatting** (`formatting.py`, rain-probability calc) → plain
  `pytest` unit tests, no I/O. Feed sample dicts (the shape OpenWeatherMap returns), assert on the
  output string/number. Use `@pytest.mark.parametrize` for the emoji/recommendation branches.
  E.g. `tests/test_formatting.py`.
- **Async HTTP client** (`weather.py`) → `pytest-asyncio` + `aioresponses` to stub the aiohttp calls;
  **never hit the real API**. Assert the parsed result and the graceful-degradation path (HTTP
  401/404/error → returns `None`, no exception). E.g. `tests/test_weather.py`.
- **Telegram sender** (`telegram_sender.py`) → mock the `Bot` with `unittest.mock.AsyncMock`; assert
  `send_message` is called with the expected `chat_id`, text and `parse_mode='HTML'`, and that a
  send failure still tries the error-notification path. E.g. `tests/test_telegram_sender.py`.
- **Config** (`config.py`) → `monkeypatch.setenv` / `delenv`; assert defaults, and that a missing
  required var (`TELEGRAM_TOKEN`, `WEATHER_API_KEY`, `CHAT_ID`) fails loudly. E.g. `tests/test_config.py`.

## Conventions
- Files `tests/test_<module>.py`; functions `test_<behavior>`. Shared fixtures in `tests/conftest.py`.
- Test names / docstrings in **English** describing the behavior, not the function: "returns None and
  logs when the API answers 401".
- **No network, no real Telegram** in any test. Stub aiohttp (`aioresponses`) and the `Bot`
  (`AsyncMock`).
- Async tests marked `@pytest.mark.asyncio` (or `asyncio_mode = "auto"` in `pyproject.toml`).
- User-facing text that gets asserted stays in **Spanish** (the message literals); code stays English.

## How to fill `Tests` in a GRAPH STEP
- **Why (TDD)**: the observable behavior the test blocks before implementing.
- **How**: `tests/<test_xxx.py>` → `test_<behavior>` + the chosen style (pure unit / aioresponses /
  AsyncMock / monkeypatch). If extending an existing test, name it.
