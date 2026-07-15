---
status: draft
created: 2026-07-15
---

# Python packaging, versioning, and skill-suite adaptation

Restructure the single-file bot into a proper `src/`-layout Python package, add SemVer version
control with a changelog and bump tooling, add a pytest suite, and finish adapting the remaining
skills (`implementer`, `pr-review`) to this project. Behavior of the bot is preserved — this is
structure, tooling and docs, not new features.

## Acceptance criteria
- [ ] AC-1: `pip install -e ".[dev]"` succeeds from a clean venv; the console script
  `weather-message-bot` and `python -m weather_message_bot` both start the scheduler.
- [ ] AC-2: `python -m weather_message_bot --test` sends exactly one message and exits 0 (manual —
  see Uncovered).
- [ ] AC-3: `pytest` is green with at least one test per module (`config`, `weather`, `formatting`,
  `telegram_sender`, `scheduler`) and touches no network / no real Telegram.
- [ ] AC-4: `ruff check .` reports no errors.
- [ ] AC-5: the version is single-sourced in `pyproject.toml`; `weather_message_bot.__version__`
  equals it; `bump-my-version bump patch` updates `pyproject.toml`, commits, and creates a `vX.Y.Z`
  git tag.
- [ ] AC-6: `CHANGELOG.md` exists in Keep-a-Changelog format with an initial `0.1.0` entry.
- [ ] AC-7: `DockerFile`, `docker-compose.yaml` and the CI workflow launch `python -m
  weather_message_bot`; the image builds; CI tags the image with the project version.
- [ ] AC-8: `.claude/skills/implementer/` and `.claude/skills/pr-review/` exist and contain **no**
  Java/Maven/JDA/anime references — they cite this project's files, pytest, and commands.
- [ ] AC-9: `README.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `project-tree.md` and
  `project-architecture.md` describe the new structure and entry point; the doc-sync table is clean.

## GRAPH STEPS
> Waves: A = {S1, S2, S3} (foundation + skill docs, parallel); B = {S4..S9} (code split, depend on
> S1, sequential-ish by import graph); C = {S10, S11, S12} (versioning + integration + docs, depend
> on B).

### Step 1 — Packaging foundation (`pyproject.toml` + tooling)
- **Why**: a package/build definition is the base for the `src` layout, the console script, the dev
  deps, and single-sourced versioning.
- **How**: `pyproject.toml` (NEW) → `[build-system]` (hatchling), `[project]` (name
  `weather-message-bot`, `version = "0.1.0"`, runtime deps copied from `requirements.txt`),
  `[project.scripts]` `weather-message-bot = "weather_message_bot.__main__:main"`,
  `[project.optional-dependencies] dev = [pytest, pytest-asyncio, aioresponses, ruff, bump-my-version]`,
  `[tool.ruff]`, `[tool.pytest.ini_options] asyncio_mode = "auto"`.
- **Subtasks**:
  - Write `pyproject.toml` with metadata, deps, script, optional dev deps, ruff + pytest config.
  - Decide dep source of truth: `pyproject.toml`. Remove `requirements.txt` (DockerFile switches to
    `pip install .` in S11) or keep it as a generated lock — pick removal to avoid drift.
- **Tests**:
  - **Why (TDD)**: no unit test; verified by `pip install -e ".[dev]"` succeeding (enabler).
  - **How**: manual — `pip install -e ".[dev]"` in a clean `.venv`.
- **Covers**: enabler, no AC (unlocks AC-1, AC-4, AC-5)
- **Depends on**: none

### Step 2 — Adapt `implementer` skill + references
- **Why**: finish restoring the skill suite; the current repo has planner but not implementer.
- **How**: `.claude/skills/implementer/{SKILL.md, references/{execution-rules,dag-execution,annotation-format,doc-sync}.md}`
  (NEW, adapted from AivilBot) → replace Java/Maven/TDD-for-Java with pytest inverse-TDD, `ruff`,
  `python -m weather_message_bot --test`; point cross-refs at this project's references; drop
  anime/music workflow refs (use `common-workflows.md`).
- **Subtasks**:
  - `SKILL.md`: same procedure; references point to the adapted files + `common-commands.md`.
  - `execution-rules.md`: inverse TDD via pytest, retry cap, `ruff`, project rules from `CLAUDE.md`
    (type hints, `logging` not `print` for new code, graceful degradation).
  - `dag-execution.md`: waves/deps (framework-agnostic — light edits only).
  - `annotation-format.md`: framework-agnostic — light edits only.
  - `doc-sync.md`: rewrite the doc-set table for this repo's docs (README, CLAUDE, copilot, tree,
    architecture, common-commands/workflows, planner/implementer refs).
- **Tests**:
  - **Why (TDD)**: docs, not code — verified by AC-8 grep (no Java terms) + internal links resolve.
  - **How**: manual — `grep -riE "maven|jda|anime|mvn|@Slf4j|Spring" .claude/skills/implementer` → empty.
- **Covers**: AC-8
- **Depends on**: none

### Step 3 — Adapt `pr-review` skill + references + evals
- **Why**: finish restoring the skill suite with a review checklist that matches this project.
- **How**: `.claude/skills/pr-review/{SKILL.md, references/checklist-deep.md, evals/evals.json}` (NEW,
  adapted) → checklist sections become: languages (English code / Spanish Telegram text), secrets
  (`.env`, no tokens in compose/CI), graceful degradation, timezone (`pytz`, no inline zone),
  async/aiohttp session use, pytest coverage of changed behavior, hygiene. Rewrite `evals.json`
  scenarios around weather/telegram/scheduling diffs.
- **Subtasks**:
  - `SKILL.md`: scope buckets = weather / telegram / scheduling / general; output = Blockers/Warnings/Recs.
  - `checklist-deep.md`: Python/Telegram rules only.
  - `evals/evals.json`: 2–3 labeled diff scenarios + one clean negative case.
- **Tests**:
  - **Why (TDD)**: docs — verified by AC-8 grep + `evals.json` parses as valid JSON.
  - **How**: manual — `python -c "import json,pathlib;json.loads(pathlib.Path('.claude/skills/pr-review/evals/evals.json').read_text())"`.
- **Covers**: AC-8
- **Depends on**: none

### Step 4 — Extract `config.py`
- **Why**: isolate env loading/validation so every module reads a `Settings` object, not `os.getenv`.
- **How**: `src/weather_message_bot/config.py` (NEW) → `Settings` (dataclass) + `load_settings()`
  reading env via `python-dotenv`; required `TELEGRAM_TOKEN`/`WEATHER_API_KEY`/`CHAT_ID` raise a clear
  error when missing; `CITY`/`TIME_SEND_MESSAGE`/`TIMEZONE` defaulted.
- **Subtasks**:
  - Move the env-reading + validation out of `main()` into `load_settings()`.
- **Tests**:
  - **Why (TDD)**: defaults applied when unset; set values read; a missing required var fails loudly.
  - **How**: `tests/test_config.py` → `monkeypatch.setenv/delenv` (pure unit).
- **Covers**: AC-3
- **Depends on**: S1

### Step 5 — Extract `weather.py` (async OpenWeatherMap client)
- **Why**: isolate the network layer and its graceful degradation.
- **How**: `src/weather_message_bot/weather.py` (NEW) → `get_weather_data()` / `get_forecast_data()`
  (async, aiohttp), return `None` + `logging` on 401/404/other, never raise.
- **Subtasks**:
  - Move both fetchers; take config values as params (no global reads).
- **Tests**:
  - **Why (TDD)**: 200 → parsed dict; 401/404/500 → `None` and logged, no exception.
  - **How**: `tests/test_weather.py` → `pytest-asyncio` + `aioresponses` (no network).
- **Covers**: AC-3
- **Depends on**: S1

### Step 6 — Extract `formatting.py` (pure)
- **Why**: pure message-building is the easiest to test and pin; keep it side-effect free.
- **How**: `src/weather_message_bot/formatting.py` (NEW) → `rain_probability(forecast)`,
  `weather_emoji(description)`, `format_weather_message(weather, forecast, tz)` (Spanish Markdown).
- **Subtasks**:
  - Move `format_weather_message` + split the emoji and rain-chance logic into small pure helpers.
- **Tests**:
  - **Why (TDD)**: message renders the expected Spanish lines; emoji + recommendation branch on inputs.
  - **How**: `tests/test_formatting.py` → plain unit + `@pytest.mark.parametrize`.
- **Covers**: AC-3
- **Depends on**: S1

### Step 7 — Extract `telegram_sender.py`
- **Why**: isolate Telegram I/O and the orchestration fetch→format→send.
- **How**: `src/weather_message_bot/telegram_sender.py` (NEW) → wraps `telegram.Bot`;
  `send_weather_message(settings)` orchestrates and on failure still notifies the chat of the error.
- **Subtasks**:
  - Move `send_weather_message`; depend on `weather` + `formatting` (import graph, not globals).
- **Tests**:
  - **Why (TDD)**: `send_message` called with expected `chat_id`/text/`parse_mode='Markdown'`; a send
    failure triggers the error-notification path.
  - **How**: `tests/test_telegram_sender.py` → `unittest.mock.AsyncMock` on `Bot`.
- **Covers**: AC-3
- **Depends on**: S5, S6

### Step 8 — Extract `scheduler.py`
- **Why**: isolate the local→UTC conversion and the daily loop.
- **How**: `src/weather_message_bot/scheduler.py` (NEW) → `to_utc(time_send, tz)`,
  `schedule_daily_message(settings)`; bridges sync `schedule` to the async send on a fresh loop.
- **Subtasks**:
  - Move the conversion + `schedule.every().day.at(...)` registration + `run_async_task` bridge.
- **Tests**:
  - **Why (TDD)**: a known local time + zone converts to the expected UTC string (no sleeping, no loop).
  - **How**: `tests/test_scheduler.py` → pure unit on `to_utc`.
- **Covers**: AC-3
- **Depends on**: S7

### Step 9 — `__main__.py` + `__init__.py`, retire `weather_bot.py`
- **Why**: wire the package entry point; expose `__version__`; drop the monolith.
- **How**: `src/weather_message_bot/__main__.py` (NEW) → `main()` parses `--test`, forces
  `WindowsSelectorEventLoopPolicy` on win32, calls scheduler or one-shot send;
  `src/weather_message_bot/__init__.py` (NEW) → `__version__ = importlib.metadata.version(...)`.
  Delete `weather_bot.py`.
- **Subtasks**:
  - Write `__main__.main()` wiring config→sender/scheduler.
  - Write `__init__.__version__`.
  - Delete `weather_bot.py`.
- **Tests**:
  - **Why (TDD)**: `--test` takes the one-shot branch, default takes the scheduler branch (both with
    mocked collaborators, no network).
  - **How**: `tests/test_main.py` → monkeypatch `scheduler`/`telegram_sender`; assert branch taken.
- **Covers**: AC-1, AC-3
- **Depends on**: S4, S5, S6, S7, S8

### Step 10 — Versioning: `__version__`, `CHANGELOG.md`, bump tooling
- **Why**: the requested "control de versión" — SemVer, single-sourced, with a changelog and a bump
  command.
- **How**: `pyproject.toml` `[tool.bumpversion]` (or `.bumpversion.toml`) tracking the `version`
  field + tag `v{new_version}`; `CHANGELOG.md` (NEW, Keep a Changelog) with `0.1.0`; confirm
  `weather_message_bot.__version__` resolves via `importlib.metadata`.
- **Subtasks**:
  - Add bump-my-version config (files it edits, `tag = true`, `tag_name = "v{new_version}"`).
  - Write `CHANGELOG.md` with `[Unreleased]` + `[0.1.0]`.
- **Tests**:
  - **Why (TDD)**: `__version__` equals the `pyproject` version.
  - **How**: `tests/test_version.py` → assert `__version__` matches; `bump-my-version bump patch
    --dry-run` verified manually (see Uncovered).
- **Covers**: AC-5, AC-6
- **Depends on**: S9

### Step 11 — Update Docker / compose / CI to the new entry + version tag
- **Why**: the container and CI must run the package and can tag images with the version.
- **How**: `DockerFile` → `COPY` the package + `pyproject.toml`, `pip install .`, `CMD ["python",
  "-m", "weather_message_bot"]`; `docker-compose.yaml` unchanged (env substitution stays);
  `.github/workflows/docker-publish.yml` → add a step reading the version from `pyproject.toml` and
  add a `:${version}` image tag alongside `:latest` and `:${{ github.sha }}`.
- **Subtasks**:
  - Rewrite `DockerFile` for the package install + module entry.
  - Add the version-read step + version tag in the workflow.
- **Tests**:
  - **Why (TDD)**: not unit-testable — verified by a local `docker build` and a CI run (see Uncovered).
  - **How**: manual — `docker build -f DockerFile -t weather-telegram-bot:test .`.
- **Covers**: AC-7
- **Depends on**: S9, S10

### Step 12 — Doc sync
- **Why**: keep README/CLAUDE/copilot/tree/architecture true to the new layout and entry point.
- **How**: audit per `implementer/references/doc-sync.md`; update the run commands, structure and
  version notes; flip `project-tree.md`/`project-architecture.md` "current vs target" now that target
  is real.
- **Subtasks**:
  - README: run via `python -m weather_message_bot`, install via `pip install .`, add versioning +
    CHANGELOG notes.
  - CLAUDE.md + copilot: entry point, `pytest`/`ruff` commands, module map.
  - `project-tree.md` / `project-architecture.md`: drop the "current = single file" note.
- **Tests**:
  - **Why (TDD)**: docs — verified by the doc-sync grep table.
  - **How**: manual — grep every renamed symbol/command across `**/*.md`.
- **Covers**: AC-9
- **Depends on**: S9, S10, S11

## Out of scope
- New bot features or new weather data fields (message content stays as today).
- Switching libraries (`schedule`, `aiohttp`, `python-telegram-bot`, `pytz` stay).
- Any deploy/hosting change beyond adding a version tag to the built image.
- Renaming the venv folder `weathermessagebot/` (only noted so the new package `weather_message_bot/`
  doesn't collide with the gitignore rule).
- Revoking the previously-exposed Telegram token / API key (separate security action, already flagged).

## Uncovered / manual verification
- Real Telegram send + real OpenWeatherMap call → `python -m weather_message_bot --test` against a
  real bot/chat (AC-2).
- Docker image build + multi-arch CI push → one `docker build` locally and one CI run on push (AC-7).
- `bump-my-version` tagging → `bump-my-version bump patch --dry-run` inspected once before real use
  (AC-5).

## Checklist
- [ ] Step 1 — Packaging foundation (`pyproject.toml` + tooling)
- [ ] Step 2 — Adapt `implementer` skill + references
- [ ] Step 3 — Adapt `pr-review` skill + references + evals
- [ ] Step 4 — Extract `config.py`
- [ ] Step 5 — Extract `weather.py`
- [ ] Step 6 — Extract `formatting.py`
- [ ] Step 7 — Extract `telegram_sender.py`
- [ ] Step 8 — Extract `scheduler.py`
- [ ] Step 9 — `__main__.py` + `__init__.py`, retire `weather_bot.py`
- [ ] Step 10 — Versioning: `__version__`, `CHANGELOG.md`, bump tooling
- [ ] Step 11 — Update Docker / compose / CI
- [ ] Step 12 — Doc sync

## Plan references
- @.claude/skills/references/project-architecture.md
- @.claude/skills/references/project-tree.md
- @.claude/skills/references/common-commands.md
- @.claude/skills/references/common-workflows.md
- weather_bot.py (source being split)
- pyproject.toml (NEW), CHANGELOG.md (NEW), DockerFile, docker-compose.yaml,
  .github/workflows/docker-publish.yml
- .claude/skills/implementer/**, .claude/skills/pr-review/** (NEW, adapted)
