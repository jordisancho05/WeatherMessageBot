# pr-review — Deep Checklist

> Used by the `pr-review` skill (step 3). Itemized review against `CLAUDE.md`. Apply **only** the
> sections matching the diff's scope. Each violation → a finding with `file:line` + the broken rule.

## Languages & naming
- Comments / logs / docstrings in **English**.
- User-facing Telegram text (the weather message, recommendations, labels) in **Spanish**.
- Don't rename existing Spanish user-facing literals just for style.

## Secrets (blocker-tier)
- No real token / API key / chat id in the diff — not in code, `docker-compose.yaml`, or workflows.
- `.env` is never added/committed; only `.env.example` with placeholders.
- Compose/CI read secrets via `${VAR}` substitution or `env_file`, never inline values.

## Config
- New settings are read in `config.py` (the `Settings` object), not via scattered `os.getenv`.
- Every new variable is documented in `.env.example` **and** the README config table.
- Required vs optional is explicit; a missing required var fails loudly.

## Async / HTTP
- OpenWeatherMap calls stay async (`aiohttp`); the `ClientSession` is used as a context manager.
- Requests set a timeout (`aiohttp.ClientTimeout`); an added call without one is a warning.
- City / query values go through aiohttp `params`, never string-concatenated into the URL.

## Graceful degradation
- A failed API call returns `None` + logs and never raises up into the daily loop; callers handle
  `None`. A new call that can crash the scheduler is a blocker.

## Timezone
- Time math goes through `pytz`; the local `TIME_SEND_MESSAGE` is converted to UTC for scheduling and
  the message shows the local zone. No second, inline source of "now".

## Telegram
- `send_message` uses the intended `parse_mode`; text that interpolates API fields into Markdown is
  escaped (unescaped `_ * [ ` ` breaks the send).
- The `Bot` is not constructed or called in a test without a mock.

## Packaging / versioning
- Version stays single-sourced in `pyproject.toml`; no second hardcoded version string.
- Dependencies are declared in `pyproject.toml` (not a resurrected `requirements.txt`).
- Entry point stays `python -m weather_message_bot` / the console script; no reference to the deleted
  `weather_bot.py`.

## Tests
- Changed behavior is covered; new code is TDD-shaped per
  `@.claude/skills/planner/references/test-quality-rules.md`.
- No network / no real Telegram: aiohttp stubbed (`aioresponses`), `Bot` mocked (`AsyncMock`).
- Test names / docstrings in English describing the behavior.

## Hygiene / secrets
- No dead or commented-out code left behind; no large unrequested refactors.
- No commit/push performed as part of the review.
