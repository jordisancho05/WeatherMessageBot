# WeatherMessageBot — Project Structure

> Structure reference. The authoritative guide (stack, run, conventions, gotchas) lives in `CLAUDE.md`
> (root). Detailed architecture lives in `project-architecture.md`.

## Directory tree
```text
PWeatherMessageBot/
├── pyproject.toml            # Metadata + version (SemVer) + deps + tool config (ruff, pytest)
├── main.py                   # Root launcher: `python main.py [--test]`
├── CHANGELOG.md              # Keep a Changelog format
├── README.md
├── CLAUDE.md
├── .env.example
├── DockerFile
├── docker-compose.yaml
├── src/
│   └── weather_message_bot/          # NB: distinct from the gitignored venv `weathermessagebot/`
│       ├── __init__.py               # __version__
│       ├── __main__.py               # CLI entry: python -m weather_message_bot [--test]
│       ├── config.py                 # Settings from env
│       ├── weather.py                # OpenWeatherMap async client
│       ├── formatting.py             # Message building (Spanish) + rain calc + emoji
│       ├── telegram_sender.py        # Send + error notification
│       └── scheduler.py              # Timezone-aware daily job registration + loop
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_weather.py
│   ├── test_formatting.py
│   ├── test_telegram_sender.py
│   └── test_scheduler.py
├── .plan/                            # Plans (planner→implementer)
│   └── <usecase>/<type>/<slug>.md    # usecase: weather|telegram|scheduling|general; type: feat|fix|refactor
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/docker-publish.yml
└── .claude/skills/{caveman,planner,implementer,pr-review,references}/
```

## Notes
- The venv folder is `weathermessagebot/` (gitignored). The source package is `weather_message_bot/`
  under `src/` — different names on purpose so `.gitignore` doesn't swallow the source.
- `DockerFile` has a capital F; the workflow and docs reference it as `-f DockerFile`.
