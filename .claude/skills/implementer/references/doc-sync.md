# Doc Sync — keep the docs true after implementing

> Used by the `implementer` skill (step 5), once the suite is green. Docs that describe behavior the
> code no longer has are worse than no docs: the next session trusts them.
>
> **Audit, don't recall.** "I don't think any doc mentions this" is not a check. Grep is.

## The doc set (all of it, every time)
| File | Describes |
|------|-----------|
| `CLAUDE.md` | Canonical project-wide rules/gotchas ("Always Remember"), architecture, run/test |
| `.github/copilot-instructions.md` | Mirror of `CLAUDE.md` + the **Stack** section (canonical home of dependency versions) |
| `README.md` | User-facing setup, run, Docker, config table, versioning |
| `.claude/skills/references/project-architecture.md` | Module map, layering, responsibilities |
| `.claude/skills/references/project-tree.md` | Directory tree, per-file one-liners |
| `.claude/skills/references/common-commands.md` | Env / run / test / lint / bump / Docker commands |
| `.claude/skills/references/common-workflows.md` | Recipes (add config var / weather field / schedule / CLI flag / version bump) |
| `.claude/skills/planner/references/*`, `.claude/skills/implementer/references/*`, `.claude/skills/pr-review/references/*` | Planning / execution / review mechanics |
| `CHANGELOG.md` | Released changes (Keep a Changelog) |

## Procedure
1. **List what actually changed**: every module/function added, renamed or deleted; every behavior
   whose description would now be wrong; every dependency version; every command; every new gotcha.
2. **Grep the doc set for each item** — one `Grep` over `**/*.md` with the symbols alternated
   (`weather_bot|format_weather_message|requirements.txt|…`). Search the **behavior words** too, not
   just identifiers: a doc can describe a behavior without naming the function.
3. **Fix every hit** that the change made false. Deleting `weather_bot.py` → also drop it from the
   tree/command lists. Changing an entry point → fix every `python weather_bot.py` occurrence.
4. **New reusable gotcha?** It belongs in `CLAUDE.md` "Always Remember" (canonical), with at most a
   one-line echo in the copilot mirror. A recipe-specific one goes in `common-workflows.md`.
5. **Single source of truth**: edit the canonical doc; don't restate the same fact in several files.
   Dependency versions live in the copilot **Stack** section only.
6. **Report a table**: every doc in the set, marked `updated (what)` or `checked — unaffected`. Never
   claim "docs are in sync" without having listed them.

## Pitfalls seen in practice
- Bumping the version and updating only `pyproject.toml`, while the README still says `python
  weather_bot.py`.
- Deleting `requirements.txt` but leaving install instructions that reference it.
- Splitting a module and leaving `project-architecture.md` describing the old single-file layout.
