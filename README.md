# WeatherMessageBot

This Telegram bot automatically sends you a message every day (7:00 AM by default) with up-to-date weather information, including temperature, weather conditions and the chance of rain.

## Features

- ✅ Automatic daily messages at a configurable time
- 🌡️ Complete current weather information
- 🌧️ Daily chance of rain
- ☂️ Recommendations based on the weather conditions
- 🔧 Test mode to verify that everything works

## Prerequisites

### 1. Create a Telegram Bot
1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Use the `/newbot` command and follow the instructions
3. Save the token it gives you

### 2. Get your Chat ID

**Option 1: Using the Telegram API directly**
1. Start a conversation with your bot by sending it any message
2. Open your browser and visit:
    ```
    https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
    ```
    (Replace `<YOUR_TOKEN>` with your bot's token)
3. Look for the `"id"` field inside `"chat"` in the JSON response
4. That number is your Chat ID

**Option 2: Using an existing bot**
1. Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will give you your Chat ID (a number that may start with a digit or a hyphen)

### 3. Get an OpenWeatherMap API Key
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Create a free account
3. Get your API key from the dashboard

## Installation

1. **Clone or download the project**

2. **Install the package** (dependencies come from `pyproject.toml`)
   ```bash
   pip install .
   ```
   For development (editable install + test/lint tools):
   ```bash
   pip install -e ".[dev]"
   ```

3. **Configure the bot**

   Create a `.env` file based on `.env.example`:
   ```bash
   copy .env.example .env
   ```

   Then edit the `.env` file with your real data:
   ```env
   TELEGRAM_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   WEATHER_API_KEY=your_openweathermap_api_key
   CHAT_ID=123456789
   CITY=Madrid,ES
   TIME_SEND_MESSAGE=07:00
   TIMEZONE=Europe/Madrid
   ```

   **Where:**
   - `TELEGRAM_TOKEN`: Your Telegram bot token
   - `WEATHER_API_KEY`: Your OpenWeatherMap API key
   - `CHAT_ID`: Your Telegram chat ID
   - `CITY`: City for the forecast (format: "City,CountryCode")
   - `TIME_SEND_MESSAGE`: Time at which you want to receive the message (format: HH:MM)
   - `TIMEZONE`: Time zone of your city

## Usage

### Run the Bot
```bash
python main.py
```
Equivalent alternatives: `python -m weather_message_bot` or the installed console script
`weather-message-bot`.

The bot will start and wait until the configured time to send the first message, then keep sending daily messages.

### Test Mode
To check that everything works correctly:
```bash
python main.py --test
```

This sends a message immediately to verify the configuration.

## Running with Docker

The project includes a `DockerFile` and a `docker-compose.yaml` so you can run the bot in a container.

1. **Build the image**
   ```bash
   docker build -f DockerFile -t weather-telegram-bot:latest .
   ```

2. **Configure your credentials** in a `.env` file; `docker-compose.yaml` reads them via `${VAR}` substitution.

3. **Start the bot**
   ```bash
   docker compose up -d
   ```

The container is set to `restart: unless-stopped`, so it will keep running and restart automatically unless you stop it.

## Example Message

```
🌤️ Good morning! Here's today's weather

📍 Madrid
🌡️ Temperature: 22.5°C (feels like 24.1°C)
☀️ Conditions: Clear Sky
💧 Humidity: 65%
🌧️ Chance of rain: 15%

☀️ Recommendation: No rain expected today, enjoy!

⏰ Sent automatically at 07:00 (Europe/Madrid)
```

## Customization

### Change the message time
Set `TIME_SEND_MESSAGE` in your `.env` file (format: `HH:MM`).

### Change the message format
Edit the `format_weather_message()` function in `src/weather_message_bot/formatting.py`.

### Add more cities
You can create multiple configurations or modify the code to support several cities.

## Development

```bash
pip install -e ".[dev]"   # editable install + dev tools
pytest                     # run the test suite (no network / no real Telegram)
ruff check .               # lint
```

Project layout: the code lives in `src/weather_message_bot/` (`config`, `weather`, `formatting`,
`telegram_sender`, `scheduler`, `__main__`); tests live in `tests/`.

## Versioning

The project follows [Semantic Versioning](https://semver.org/); the version is single-sourced in
`pyproject.toml` and changes are tracked in [`CHANGELOG.md`](CHANGELOG.md). To release:

```bash
bump-my-version bump patch   # or: minor / major
git push --follow-tags
```

## Troubleshooting

### Error: "Environment variables not configured"
- Make sure you have created the `.env` file
- Check that all variables are set correctly
- The `.env` file must be in the folder you launch the bot from (the project root)

### Error: "Invalid token"
- Check that the bot token is correct
- Make sure the bot is active on Telegram

### Error: "Chat not found"
- Check that the Chat ID is correct
- Make sure you started a conversation with the bot first

### Error: "Invalid API key"
- Check your OpenWeatherMap API key
- Make sure the account is activated

## Dependencies

- `python-telegram-bot`: To interact with the Telegram API
- `aiohttp`: To make asynchronous HTTP requests
- `schedule`: To schedule daily tasks
- `python-dotenv`: To load environment variables from a `.env` file
- `pytz`: To handle the time in your time zone

## License

This project is free to use. You can modify and distribute it as you need.
