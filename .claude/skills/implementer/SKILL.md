---
name: implementer
description: Execute a plan already written in .plan/ test-first (inverse TDD), marking subtasks done. Use when the user says "implementa el plan", "ejecuta el plan", "desarrolla esto", "implementer".
---

# implementer

Execute a plan produced by the `planner` skill. The plan file is the source of truth for state; follow
`CLAUDE.md` throughout.

## Procedure
1. **Select the plan**:
   - If the user passed a path/name (e.g. `@.plan/<usecase>/<type>/<slug>.md`), use it.
   - Otherwise, **list** with Glob the plans under `.plan/**` whose frontmatter `status` is not `done`
     (a plan without frontmatter counts as pending) and **ask** which one to implement. Do not guess.
   - On start, set the plan's frontmatter to `status: in-progress` (transitions per
     `references/annotation-format.md`).
2. **Pre-flight freshness check**: grep every file/function the plan's `How` lines name. If any is
   missing or renamed, the plan has drifted — **report the drift and ask** before executing; don't
   silently adapt the plan to the new reality.
3. **Execute** the GRAPH STEPS in graph order per `references/dag-execution.md` (waves + `Depends on`),
   applying `references/execution-rules.md` (inverse TDD, retry cap, run/test, project rules).
4. **Annotate** progress in the plan file per `references/annotation-format.md` (`[ ]` → `[x]` as you
   close each subtask; deviations recorded in `## Deviations`).
5. **Sync the docs** (once the suite is green) — **audit, don't recall**. Follow
   `references/doc-sync.md`: grep every touched symbol/behavior/version across the **whole doc set**
   and report the result file by file. A doc is only "up to date" once you have *searched* it, not
   because you don't remember writing about it.
6. **Done**: with the final gate green (full suite + `ruff`, `dag-execution.md` §Walk), set the plan's
   `status: done` and show:
   implemented summary, the full-suite result, the **AC evidence table** (each `AC-n` → the test or
   measure that proves it, via the steps' `Covers` links), the plan's `Uncovered / manual verification`
   list (what was verified manually and how), the updated plan path, and the doc-sync table from
   step 5 (every doc, each marked updated or checked-and-unaffected).

## References
**Always needed — read them in a single parallel batch** (don't load them serially):
- `references/execution-rules.md` — inverse TDD, run/test, `CLAUDE.md` rules, scope.
- `references/dag-execution.md` — walk steps by waves and dependencies.
- `references/annotation-format.md` — mark progress in the plan.
- `references/doc-sync.md` — audit the doc set after green (step 5).
- `../references/common-commands.md` — run/test commands (`pytest`, `ruff`, module entry).

Load on demand only when needed:
- `../references/common-workflows.md` — when the plan matches a recipe (add config var, add weather
  field, change schedule, add CLI flag, bump version).
