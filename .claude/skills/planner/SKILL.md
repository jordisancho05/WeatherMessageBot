---
name: planner
description: Create a development plan for a feature/fix/refactor in this Python Telegram bot. Classifies the usecase, maps the goal to concrete files/tests, and writes the plan to disk at .plan/<usecase>/<type>/<slug>.md. Writes the plan and STOPS (does not implement). Use when the user says "planifica", "crea un plan", "nueva feature", "planner".
---

# Planner Skill

Analyze a goal (feat / fix / refactor), map it to the project's real files and tests, **write the
plan** to `.plan/<usecase>/<type>/<slug>.md`, then **STOP**: do not implement or chain into
`implementer` (that step is launched by the user).

## Plan Path
`.plan/<usecase>/<type>/<slug>.md` (create the folders if missing).
- **usecase** ∈ `weather` | `telegram` | `scheduling` | `general` (cross-cutting: config, packaging,
  CI, docs, tooling, versioning).
- **type** ∈ `feat` | `fix` | `refactor`.
- **slug** kebab-case, ≤5 words (`add-humidity-alert`, `src-layout-migration`).

## Procedure
1. **Glob `.plan/**` once**: if a plan for this goal already exists, edit it instead of duplicating.
2. Read `references/domain-analysis-protocol.md` → `usecase` + candidate components/files + gotchas.
3. If any requirement is ambiguous, **gather ALL questions and ask them in a single round** (not serially).
4. Split into atomic subtasks and group them into **waves** (parallel within a wave; dependent across waves).
5. Write the plan following `references/writing-rules.md` (structure + template, single source) and
   `references/test-quality-rules.md` (how to write the Tests block per layer).
6. **STOP.** Report the saved plan path and tell the user to launch `implementer` (pointing it at this
   plan) when they want to build it. Do not start implementing.

## References
**Always needed — read them in a single parallel batch** (don't load them serially):
- `references/domain-analysis-protocol.md` — classify usecase, map layer/files, gotchas.
- `references/writing-rules.md` — structure, language, format and **template** of the plan (single source).
- `references/test-quality-rules.md` — how to write each step's Tests block.
- `../references/project-architecture.md` — module map + layering (map subtasks to real files).

Load on demand only when needed:
- `../references/project-tree.md` — exact paths / visual tree (only if `project-architecture` doesn't pin the file).
- `../references/common-workflows.md` — recipes for the common changes (add config var, add weather
  field, change schedule, bump version).
