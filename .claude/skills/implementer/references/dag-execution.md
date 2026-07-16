# DAG Execution — step execution order

> Used by the `implementer` skill. Defines how to walk a plan's GRAPH STEPS respecting their waves and
> dependencies.

## Waves and dependencies
- Plans group steps into **waves** (A / B / C…). Within a wave steps are **independent →
  parallelizable** where safe; across waves there is a **dependency**.
- Respect each step's **`Depends on`** field: don't start a step until its dependencies are green.

## Walk
1. Resolve the topological order from the waves + `Depends on`.
2. Run wave by wave; within each wave tackle the independent steps before moving on.
3. **Tests per wave**: when closing a wave, run its steps' tests (`pytest`, see `execution-rules.md`)
   before advancing; if anything is red, don't open the next wave.
4. **Final gate**: after the last wave, run the **full suite** (`pytest`) plus `ruff check .` — not
   just the touched tests. Per-wave runs don't catch cross-wave regressions; the plan isn't done until
   the whole suite is green and lint is clean.

## Resuming
- When resuming a half-done plan, start only from the pending `[ ]` subtasks (see
  `annotation-format.md`) and rebuild the wave order from what's left.
