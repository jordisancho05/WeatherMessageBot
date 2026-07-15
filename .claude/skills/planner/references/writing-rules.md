# Writing Rules — how to write a plan

> Used by the `planner` skill to write the plan document. Defines the structure, style and language of
> the `.plan/<usecase>/<type>/<slug>.md` file.

## Mandatory sections (in this order)
0. **YAML frontmatter** — `status: draft` and `created: <YYYY-MM-DD>` (absolute date, never "today").
   The planner always writes `draft`; later status transitions belong to `implementer`
   (its `annotation-format.md`).
1. `# <Plan name>` — clear title, no type prefixes.
2. `## Acceptance criteria` — `[ ]` checklist of **verifiable** conditions, **numbered `AC-1`, `AC-2`, …**
   (what can be checked when done). Nothing vague ("works fine" ❌; "`--test` sends one message and
   exits 0" ✅).
3. `## GRAPH STEPS` — the graph steps (schema in the **Full template** below).
4. `## Out of scope` — explicit non-goals. This is the boundary the implementer's "implement only what
   the plan describes" rule enforces; anything ambiguous at execution time is checked against it.
5. `## Uncovered / manual verification` — behavior that can't be unit-tested (real Telegram send, real
   OpenWeatherMap call) + how to verify it instead (e.g. `python -m weather_message_bot --test`).
   Write `- None` if everything is covered. The implementer echoes this list in its final report.
6. `## Checklist` — one `[ ]` per step, in execution order.
7. `## Plan references` — `@` refs to internal docs touched + project files involved.

Group steps into **waves**: within a wave steps are parallelizable; across waves there is a
dependency. State it at the start of GRAPH STEPS (text, waves A/B/C, or Mermaid).

## Full template (output, single source for the GRAPH STEP schema)
```markdown
---
status: draft
created: <YYYY-MM-DD>
---

# <Plan name>

## Acceptance criteria
- [ ] AC-1: <verifiable criterion>
- [ ] AC-2: <verifiable criterion>

## GRAPH STEPS
> Waves: A = {parallel steps}; B = {depend on A}; ...

### Step <id> — <short name>
- **Why**: <reason / problem it solves>
- **How**: `<project file>` → `<function or pattern>`
- **Subtasks**:
  - <atomic subtask 1>
  - <atomic subtask 2>
- **Tests**:
  - **Why (TDD)**: <behavior the tests pin, written first and red>
  - **How**: `tests/<test_xxx.py>` → `test_<behavior>` (style per layer → `test-quality-rules`: pure unit | aioresponses async | AsyncMock Bot | monkeypatch env)
- **Covers**: AC-<n>[, AC-<m>] | "enabler, no AC"
- **Depends on**: <previous ids | "none">

## Out of scope
- <explicit non-goal 1>

## Uncovered / manual verification
- <uncovered behavior + how it is verified manually> | None

## Checklist
- [ ] Step 1 — ...
- [ ] Step 2 — ...

## Plan references
- @.claude/skills/references/project-architecture.md
- @.claude/skills/references/common-workflows.md  (if it matches a recipe)
- <project files touched>
```

## How rules
- **Always concrete**: real repo file + function or pattern (`weather.get_forecast_data`,
  `formatting.format_weather_message`, "new `Settings` dataclass in `config.py`"). Never "modify the
  weather code".
- If the file doesn't exist yet, mark it `(NEW)` and state the target module.
- **Traceability, both ways**: every `AC-n` is covered by at least one step's `Covers`; every step
  covers at least one AC or states `enabler, no AC` (setup/refactor that unlocks other steps). An AC no
  step covers, or a step no AC needs, is a planning bug — fix the plan before writing it.
- **Subtask sizing**: one subtask = one red→green cycle, ideally touching **one** production file. If a
  subtask needs several files or several test cycles, split it.

## Language and style
- Plan text in **English**; identifiers, file names, functions and tests in their **real form** (don't
  translate `format_weather_message`, `WeatherBot`, `test_...`).
- When describing future code or user-facing text, respect the `CLAUDE.md` language split (English
  code, Spanish Telegram text — it's always in context, don't restate it in the plan).
- Concise and scannable: short sentences, bullets, no filler. The plan should read at a glance and run
  without ambiguity.
- Don't include discarded alternatives: only the recommended approach.
