"""The package version is single-sourced in pyproject.toml."""

import pathlib
import tomllib

import weather_message_bot


def test_version_matches_pyproject():
    pyproject = tomllib.loads(
        pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
    )
    assert weather_message_bot.__version__ == pyproject["project"]["version"]
