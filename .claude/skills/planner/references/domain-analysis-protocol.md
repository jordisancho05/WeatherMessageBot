# Domain Analysis Protocol — from goal to usecase + files

> Used by the `planner` skill before writing the plan. Turns a goal into: a **usecase**, the affected
> **layer/files** and the applicable **gotchas**, which feed the GRAPH STEPS.

## Step 1 — Classify the `usecase`
- **weather** — OpenWeatherMap calls, rain-probability calc, message building/formatting. Files:
  `weather.py`, `formatting.py`.
- **telegram** — sending messages to the chat, bot interaction, error notification. Files:
  `telegram_sender.py`.
- **scheduling** — the daily job, local↔UTC conversion, timezone handling, the run loop. Files:
  `scheduler.py`.
- **general** — cross-cutting: config/env (`config.py`), CLI entry (`__main__.py`), packaging
  (`pyproject.toml`), CI (`.github/workflows/`), docs (`README.md`, `CLAUDE.md`), tooling, versioning.
If it spans several, pick the **main domain** of the change; if purely cross-cutting, `general`.

## Step 2 — Locate the layer (use `project-architecture.md` + `project-tree.md`)
Flow order: `config` → `weather` (client + `formatting`) → `telegram` (sender) → `scheduler`
(orchestration + cron loop) → `__main__` (CLI). Map each subtask to its layer and to a concrete file
(existing or `(NEW)`).

## Step 3 — Common workflows
If the change matches a common recipe (add a config variable, add a scraped/weather field to the
message, change the schedule, add a command-line flag, bump the version), load
`@.claude/skills/references/common-workflows.md` and apply its steps. That file is the single source —
don't restate its steps here.

## Step 4 — Gotchas to flag in the steps
- Flag the **`CLAUDE.md` "Always Remember"** gotchas the affected files hit (always in context — don't
  restate the list): never commit secrets (`.env`), English code / Spanish user-facing text, graceful
  network degradation (return `None`, never crash the daily loop).
- Code-style additions live in `@.claude/skills/implementer/references/execution-rules.md` (type
  hints, `logging` not `print` for new code, `pytz`/timezone handling).
- Structural gotcha: the venv folder is `weathermessagebot/` (gitignored); the source package is
  `weather_message_bot/` — keep them distinct so `.gitignore` doesn't swallow the source.

## Protocol output
1. Chosen `usecase` (justified in one line).
2. List of candidate components/files per subtask (layer + file + function/pattern).
3. Applicable gotchas.
This carries over to each GRAPH STEP's `How` and to the `Plan references` section.
