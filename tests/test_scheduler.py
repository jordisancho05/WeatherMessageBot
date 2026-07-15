"""Tests for the local->UTC conversion used to register the daily job."""

from datetime import date

import pytz

from weather_message_bot import scheduler


def test_to_utc_madrid_summer_is_utc_plus_2():
    tz = pytz.timezone("Europe/Madrid")
    assert scheduler.to_utc("07:00", tz, on_date=date(2026, 7, 15)) == "05:00"


def test_to_utc_madrid_winter_is_utc_plus_1():
    tz = pytz.timezone("Europe/Madrid")
    assert scheduler.to_utc("07:00", tz, on_date=date(2026, 1, 15)) == "06:00"


def test_to_utc_identity_for_utc_zone():
    tz = pytz.timezone("UTC")
    assert scheduler.to_utc("07:00", tz, on_date=date(2026, 7, 15)) == "07:00"
