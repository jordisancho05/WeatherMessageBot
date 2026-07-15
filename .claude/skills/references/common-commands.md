# Common Commands — WeatherMessageBot

> Python project. Commands assume Windows + PowerShell (adjust the venv activate path on other OSes).

## Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt          # runtime deps
# after the pyproject migration:
pip install -e ".[dev]"                   # editable install + dev tools (pytest, ruff, ...)
```

## Run
```powershell
python weather_bot.py                      # current: run the daily scheduler
python weather_bot.py --test               # current: send one message now and exit
# after the src-layout migration:
python -m weather_message_bot              # run the daily scheduler
python -m weather_message_bot --test       # send one message now and exit
```

## Test
```powershell
pytest                                     # whole suite
pytest tests/test_weather.py               # one file
pytest tests/test_weather.py::test_returns_none_on_401   # one test
pytest -k formatting                       # by keyword
pytest -q                                  # quiet
```
- No network / no real Telegram in tests: aiohttp stubbed with `aioresponses`, `Bot` mocked with
  `AsyncMock`. Async tests use `pytest-asyncio`.

## Lint / format
```powershell
ruff check .                               # lint
ruff check . --fix                         # autofix
ruff format .                              # format
```

## Version bump (SemVer, after the versioning setup)
```powershell
bump-my-version bump patch                 # 0.1.0 -> 0.1.1  (or: minor / major)
git push --follow-tags                     # push the commit + the vX.Y.Z tag
```
- Version is single-sourced in `pyproject.toml`; the git tag `vX.Y.Z` and `CHANGELOG.md` entry follow.

## Docker
```powershell
docker build -f DockerFile -t weather-telegram-bot:latest .
docker compose up -d                       # reads config from .env
```
- CI (`.github/workflows/docker-publish.yml`) builds + pushes the image to GHCR on push to `master`.
