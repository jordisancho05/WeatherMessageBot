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
- The daily job is registered with a **tz-aware** `time` on PTB's `JobQueue`
  (`run_daily(cb, time=parse_daily_time(hhmm, tz))`) — correct on a local or UTC/Docker clock; no
  manual local→UTC math, which is wrong when the host clock isn't UTC. The message shows the local
  zone. No second, inline source of "now".

## Telegram
- `send_message` uses the intended `parse_mode`; API fields interpolated into the message are HTML
  `html.escape`d (the message uses HTML parse mode).
- The `Bot` is used through its async lifecycle (`async with bot:` → initialize/shutdown) **only when
  this code owns it**; a Bot borrowed from a running `Application` is passed with `manage_bot=False`
  and never shut down (that would stop polling). Failures entering the context degrade gracefully,
  never raising out of `send_weather_message`.
- The `Bot` is not constructed or called in a test without a mock.

## Secrets in logs
- No log line can contain the bot token or an api key. `httpx` logs request URLs and PTB embeds the
  token in the path, so `httpx`/`httpcore`/`apscheduler` must stay at WARNING
  (`__main__._quiet_noisy_loggers()`). Raising the root level to DEBUG, removing a logger from
  `_NOISY_LOGGERS`, or logging a URL / `Bot` repr re-leaks it and is a blocker.

## Commands / authorization
- **Every** command handler gates on `commands.is_authorized()` before doing any work; an
  unauthorized chat gets the refusal and triggers **no** OpenWeatherMap call. A new handler missing
  the gate, or calling the API before it, is a blocker: the bot is publicly reachable and the API key
  has a limited quota.
- Handlers read `settings`/`tz` from `context.bot_data`, not module-level globals. Per-chat state
  (e.g. the `/time` cooldown) lives in `chat_data`; a module-level dict would leak across chats and
  is a blocker.
- A quota-spending command is rate limited **after** the auth gate, with the timestamp recorded only
  once the reply was served (recording before/on failure locks the user out for the whole cooldown).
  Elapsed time uses `time.monotonic()`, not `time.time()` — a system-clock jump must not lock it out.
- Handler failures are logged and answered with a generic Spanish message — no internal detail
  (exception text, token, URL) reaches the chat.
- Tests cover both sides of the gate: the owner path **and** a stranger path asserting the fetch was
  never awaited.

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
