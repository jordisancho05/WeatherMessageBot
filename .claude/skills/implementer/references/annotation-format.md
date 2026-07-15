# Annotation Format — how to mark progress in the plan

> Used by the `implementer` skill to annotate the `.plan/<usecase>/<type>/<slug>.md` file as it
> progresses. The plan is the source of truth for state.

## Status lifecycle (frontmatter)
- The plan's YAML frontmatter `status` is owned by `implementer`: `draft` (as written by `planner`) →
  `in-progress` (set when execution starts) → `done` (set only when every AC is verified and the full
  suite is green + lint clean). A plan without frontmatter is treated as `draft`.
- Never move `status` backwards; an abandoned plan stays `in-progress` with its open `[ ]` telling the
  story.

## What to mark
- When finishing **each subtask**, mark its entry in the plan's **`## Checklist`**: `[ ]` → `[x]`.
- If the plan also lists subtasks inside a `### Step` as `[ ]`, mark them too when closed.
- Mark an **`Acceptance criteria`** item (`[ ]` → `[x]`) only when it's **verified** (a test/measure
  proving it), not when the code is written. Which steps prove which AC is given by the steps'
  `Covers` field.

## Deviations
- When reality diverges from the plan (a `How` target changed, an approach failed, the retry cap in
  `execution-rules.md` was hit), record it in a **`## Deviations`** section at the end of the plan
  (create it on first use). One bullet per deviation: **step, what diverged, why, decision taken**.
- A deviation that changes scope or approach is **not** yours to decide: STOP, annotate it, ask the
  user. Only record-and-continue when the fix is mechanical (e.g. a file was renamed and the plan's
  intent is untouched).

## How
- Edit the plan file in place; change only the affected `[ ]`.
- **Don't rewrite** the rest of the plan (Why/How/Tests/order): it stays intact.
- Keep it in sync: a step isn't marked done while its tests are red.

## Resuming
- To resume, the remaining `[ ]` in `## Checklist` are the pending work; the `[x]` are already done and
  not re-run.
