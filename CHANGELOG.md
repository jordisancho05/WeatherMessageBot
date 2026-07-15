# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-15

### Added
- `src/`-layout package `weather_message_bot` with a `python -m weather_message_bot` /
  `weather-message-bot` entry point.
- `pyproject.toml` with pinned runtime deps, a `dev` extra (pytest, pytest-asyncio, aioresponses,
  ruff, bump-my-version), ruff and pytest configuration, and SemVer versioning.
- pytest suite covering config, weather client, message formatting, Telegram sender, scheduler,
  entry point and version (no network / no real Telegram).
- This changelog and single-sourced `__version__`.

### Changed
- Split the single-file `weather_bot.py` into `config`, `weather`, `formatting`, `telegram_sender`,
  `scheduler` and `__main__` modules (behavior preserved).
- New package code logs via the `logging` module instead of `print`.
- Docker image now installs the package and runs `python -m weather_message_bot`.

### Removed
- `weather_bot.py` (replaced by the package).
- `requirements.txt` (dependencies now live in `pyproject.toml`).

[Unreleased]: https://github.com/jordisancho05/WeatherMessageBot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jordisancho05/WeatherMessageBot/releases/tag/v0.1.0
