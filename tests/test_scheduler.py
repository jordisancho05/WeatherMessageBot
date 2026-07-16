"""Tests for daily-job registration (timezone-aware, machine-independent)."""

from datetime import time

import pytz
import schedule

from weather_message_bot import scheduler
from weather_message_bot.config import Settings


def test_registers_one_job_at_the_configured_local_time_and_zone():
    """The job is registered at the local wall-clock time in the configured zone.

    This does not depend on the host clock: `schedule` stores the literal time and the timezone,
    so it fires at 03:42 Europe/Madrid whether the machine runs in Madrid or UTC (Docker).
    """
    schedule.clear()
    settings = Settings(
        telegram_token="t",
        weather_api_key="k",
        chat_id="123",
        time_send_message="03:42",
        timezone="Europe/Madrid",
    )
    tz = pytz.timezone("Europe/Madrid")

    scheduler.schedule_daily_message(settings, tz, block=False)

    assert len(schedule.jobs) == 1
    job = schedule.jobs[0]
    assert job.at_time == time(3, 42)
    assert job.at_time_zone.zone == "Europe/Madrid"
    schedule.clear()
