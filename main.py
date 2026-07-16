"""Convenience launcher: `python main.py [--test]`.

Thin wrapper around the package entry point so the bot can be started by running a single file.
Equivalent to `python -m weather_message_bot` or the `weather-message-bot` console script.
"""

from weather_message_bot.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
