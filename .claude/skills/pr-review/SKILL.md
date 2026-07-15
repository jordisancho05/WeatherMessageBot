---
name: pr-review
description: Review a PR / diff against this project's rules and gotchas. Use when the user says "revisa esta PR", "revisa los cambios", "code review".
---

# pr-review

Review changes against `CLAUDE.md`. The deep, itemized checklist lives in
`references/checklist-deep.md`; the skill's behavior is validated by `evals/evals.json`.

## Procedure
1. **Get the diff.** If not provided, ask for it (or `git diff <base>...<head>`).
2. **Scope it.** Identify the touched layers/usecases (weather, telegram, scheduling, general:
   config/packaging/CI/docs). Only the matching checklist sections apply.
3. **Run the checklist** in `references/checklist-deep.md` (languages → secrets → config → async/HTTP →
   graceful degradation → timezone → telegram → packaging/versioning → tests → hygiene). Load it on demand.
4. **Report** the structured summary below; each finding cites `file:line` and the rule it breaks.

## Output
Structured summary (omit empty buckets):
- ❌ Blockers — must fix before merge: a real secret / `.env` value in the diff; a `CLAUDE.md`
  prohibition broken (hardcoded token/API key in code/compose/CI, committing `.env`); a network/
  Telegram call added to a test; changed behavior with no test.
- ⚠️ Warnings — should fix: convention/rule break with contained impact (`os.getenv` outside
  `config.py`, `print` instead of `logging` in the package, missing request timeout, inline timezone,
  wrong language in a user-facing string, unescaped Markdown in the message). Always state the risk.
- ✅ Recommendations — optional improvements: style, structure, small refactors; no rule broken.

## References (load on demand)
- `references/checklist-deep.md` — full itemized review checklist (rules, gotchas, tests).
- `@.claude/skills/references/project-architecture.md` — layer/module map (only if scope is unclear).
- `@.claude/skills/references/common-workflows.md` — the recipe the change should have followed.

## Evals
`evals/evals.json` — labeled diff scenarios with the findings each review must catch (plus a clean
negative case). Use it to validate changes to this skill or `checklist-deep.md`: a regression is a
case whose expected findings stop being produced, or a clean case that starts producing findings.
