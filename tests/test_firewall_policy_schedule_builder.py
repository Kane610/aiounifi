"""Test reading and building firewall policy schedules."""

from datetime import date, time
from typing import Any

import pytest

from aiounifi.models.firewall_policy import (
    FirewallPolicy,
    FirewallPolicyScheduleError,
    FirewallPolicyScheduleMode,
    FirewallPolicyScheduleSettings,
    ScheduleDatesOutOfOrderError,
    ScheduleSettingUnusedError,
    ScheduleWithoutDaysError,
    build_schedule,
)

from .fixtures import FIREWALL_POLICIES

TODAY = date(2026, 1, 16)
EVERY_WEEKDAY = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

EVERY_DAY = {
    "mode": "EVERY_DAY",
    "time_range_start": "21:00",
    "time_range_end": "08:00",
}
ONE_TIME = {
    "mode": "ONE_TIME_ONLY",
    "date": "2026-01-10",
    "time_range_start": "21:30",
    "time_range_end": "08:30",
}
WEEKLY = {
    "mode": "EVERY_WEEK",
    "repeat_on_days": ["wed", "mon"],
    "time_all_day": False,
    "time_range_start": "15:00",
    "time_range_end": "17:00",
}
WEEKLY_ALL_DAY = {"mode": "EVERY_WEEK", "repeat_on_days": ["fri"], "time_all_day": True}
CUSTOM = {
    "mode": "CUSTOM",
    "date_start": "2026-01-05",
    "date_end": "2026-01-30",
    "repeat_on_days": ["fri", "mon"],
    "time_all_day": False,
    "time_range_start": "20:00",
    "time_range_end": "06:00",
}
STALE_TIMES = {"time_range_start": "21:00", "time_range_end": "08:00"}


@pytest.mark.parametrize(
    ("mode", "time_window", "days", "start_date", "end_date"),
    [
        (FirewallPolicyScheduleMode.ALWAYS, False, False, False, False),
        (FirewallPolicyScheduleMode.UNKNOWN, False, False, False, False),
        (FirewallPolicyScheduleMode.EVERY_DAY, True, False, False, False),
        (FirewallPolicyScheduleMode.EVERY_WEEK, True, True, False, False),
        (FirewallPolicyScheduleMode.ONE_TIME_ONLY, True, False, True, False),
        (FirewallPolicyScheduleMode.CUSTOM, True, True, True, True),
    ],
)
def test_schedule_mode_settings(
    mode: FirewallPolicyScheduleMode,
    time_window: bool,
    days: bool,
    start_date: bool,
    end_date: bool,
) -> None:
    """Each mode reports which settings it uses."""
    assert mode.has_time_window is time_window
    assert mode.has_days is days
    assert mode.has_start_date is start_date
    assert mode.has_end_date is end_date


@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        (
            EVERY_DAY,
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.EVERY_DAY,
                start_time=time(21, 0),
                end_time=time(8, 0),
            ),
        ),
        (
            ONE_TIME,
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.ONE_TIME_ONLY,
                start_time=time(21, 30),
                end_time=time(8, 30),
                start_date=date(2026, 1, 10),
            ),
        ),
        (
            CUSTOM,
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.CUSTOM,
                start_time=time(20, 0),
                end_time=time(6, 0),
                start_date=date(2026, 1, 5),
                end_date=date(2026, 1, 30),
                all_day=False,
                days=("mon", "fri"),
            ),
        ),
        # Keys the mode doesn't use are left over from earlier modes.
        (
            {"mode": "ALWAYS", **STALE_TIMES, "date": "2026-01-10"},
            FirewallPolicyScheduleSettings(mode=FirewallPolicyScheduleMode.ALWAYS),
        ),
        (
            {**WEEKLY_ALL_DAY, **STALE_TIMES},
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.EVERY_WEEK, all_day=True, days=("fri",)
            ),
        ),
        (
            {**EVERY_DAY, "time_all_day": True, "repeat_on_days": ["mon"]},
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.EVERY_DAY,
                start_time=time(21, 0),
                end_time=time(8, 0),
            ),
        ),
        # Missing and malformed values read as None, unknown days are dropped.
        (
            {"mode": "CUSTOM", "date_start": "2026-13-01", "time_range_end": 2130},
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.CUSTOM, all_day=False, days=()
            ),
        ),
        (
            {**WEEKLY, "repeat_on_days": ["MON", "sun", "tue", "someday"]},
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.EVERY_WEEK,
                start_time=time(15, 0),
                end_time=time(17, 0),
                all_day=False,
                days=("tue", "sun"),
            ),
        ),
        (
            {**WEEKLY, "repeat_on_days": "mon", "time_range_start": "9"},
            FirewallPolicyScheduleSettings(
                mode=FirewallPolicyScheduleMode.EVERY_WEEK,
                end_time=time(17, 0),
                all_day=False,
                days=(),
            ),
        ),
        (
            {"mode": "SUNRISE", **STALE_TIMES},
            FirewallPolicyScheduleSettings(mode=FirewallPolicyScheduleMode.UNKNOWN),
        ),
        ({}, FirewallPolicyScheduleSettings(mode=FirewallPolicyScheduleMode.UNKNOWN)),
    ],
)
def test_schedule_settings(
    schedule: dict[str, Any], expected: FirewallPolicyScheduleSettings
) -> None:
    """Only the settings a schedule's mode uses are read."""
    assert FirewallPolicyScheduleSettings.from_schedule(schedule) == expected


@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        ({"mode": "ALWAYS"}, False),
        ({"mode": "SUNRISE"}, False),
        (EVERY_DAY, True),
        (ONE_TIME, True),
        (WEEKLY, True),
        (WEEKLY_ALL_DAY, False),
    ],
)
def test_schedule_settings_time_window(
    schedule: dict[str, Any], expected: bool
) -> None:
    """A time window applies unless the mode has none or it runs all day."""
    settings = FirewallPolicyScheduleSettings.from_schedule(schedule)
    assert settings.has_time_window is expected


def test_firewall_policy_schedule_settings() -> None:
    """A policy reads its schedule's settings, and a missing schedule as unknown."""
    policy = FirewallPolicy({**FIREWALL_POLICIES[0], "schedule": ONE_TIME})
    assert policy.schedule_settings.start_date == date(2026, 1, 10)

    raw = dict(FIREWALL_POLICIES[0])
    raw.pop("schedule", None)
    assert (
        FirewallPolicy(raw).schedule_settings.mode is FirewallPolicyScheduleMode.UNKNOWN
    )


@pytest.mark.parametrize(
    ("current", "changes", "expected"),
    [
        # Mode changes build a clean schedule and keep the current times.
        (EVERY_DAY, {"mode": FirewallPolicyScheduleMode.ALWAYS}, {"mode": "ALWAYS"}),
        (
            EVERY_DAY,
            {"mode": FirewallPolicyScheduleMode.ONE_TIME_ONLY},
            {
                "mode": "ONE_TIME_ONLY",
                "date": "2026-01-16",
                "time_range_start": "21:00",
                "time_range_end": "08:00",
            },
        ),
        # One time keys don't leak into Every day.
        (
            ONE_TIME,
            {"mode": FirewallPolicyScheduleMode.EVERY_DAY},
            {
                "mode": "EVERY_DAY",
                "time_range_start": "21:30",
                "time_range_end": "08:30",
            },
        ),
        # Without times, the UniFi UI's defaults are used.
        (
            {"mode": "ALWAYS"},
            {"mode": FirewallPolicyScheduleMode.EVERY_DAY},
            {
                "mode": "EVERY_DAY",
                "time_range_start": "09:00",
                "time_range_end": "12:00",
            },
        ),
        # So are they when the stored times are left over from an earlier mode.
        (
            {"mode": "ALWAYS", **STALE_TIMES},
            {"mode": FirewallPolicyScheduleMode.EVERY_DAY},
            {
                "mode": "EVERY_DAY",
                "time_range_start": "09:00",
                "time_range_end": "12:00",
            },
        ),
        (
            {**WEEKLY_ALL_DAY, **STALE_TIMES},
            {"mode": FirewallPolicyScheduleMode.ONE_TIME_ONLY},
            {
                "mode": "ONE_TIME_ONLY",
                "date": "2026-01-16",
                "time_range_start": "09:00",
                "time_range_end": "12:00",
            },
        ),
        # Custom from another mode runs every day, from today to tomorrow.
        (
            EVERY_DAY,
            {"mode": FirewallPolicyScheduleMode.CUSTOM},
            {
                "mode": "CUSTOM",
                "date_start": "2026-01-16",
                "date_end": "2026-01-17",
                "repeat_on_days": EVERY_WEEKDAY,
                "time_all_day": False,
                "time_range_start": "21:00",
                "time_range_end": "08:00",
            },
        ),
        # A One time date isn't carried into Custom.
        (
            ONE_TIME,
            {"mode": FirewallPolicyScheduleMode.CUSTOM},
            {
                "mode": "CUSTOM",
                "date_start": "2026-01-16",
                "date_end": "2026-01-17",
                "repeat_on_days": EVERY_WEEKDAY,
                "time_all_day": False,
                "time_range_start": "21:30",
                "time_range_end": "08:30",
            },
        ),
        # Value changes keep the mode and everything else it uses.
        (
            EVERY_DAY,
            {"start_time": time(22, 15, 45)},
            {
                "mode": "EVERY_DAY",
                "time_range_start": "22:15",
                "time_range_end": "08:00",
            },
        ),
        (
            ONE_TIME,
            {"start_date": date(2026, 2, 1)},
            {
                "mode": "ONE_TIME_ONLY",
                "date": "2026-02-01",
                "time_range_start": "21:30",
                "time_range_end": "08:30",
            },
        ),
        (
            ONE_TIME,
            {"end_time": time(7, 0)},
            {
                "mode": "ONE_TIME_ONLY",
                "date": "2026-01-10",
                "time_range_start": "21:30",
                "time_range_end": "07:00",
            },
        ),
        # Days are sent Monday first, whatever order the controller used.
        (
            WEEKLY,
            {"end_time": time(18, 0)},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["mon", "wed"],
                "time_all_day": False,
                "time_range_start": "15:00",
                "time_range_end": "18:00",
            },
        ),
        (
            CUSTOM,
            {"end_date": date(2026, 2, 28)},
            {
                "mode": "CUSTOM",
                "date_start": "2026-01-05",
                "date_end": "2026-02-28",
                "repeat_on_days": ["mon", "fri"],
                "time_all_day": False,
                "time_range_start": "20:00",
                "time_range_end": "06:00",
            },
        ),
        # Choosing One time again dates it today; choosing Custom again doesn't.
        (
            ONE_TIME,
            {"mode": FirewallPolicyScheduleMode.ONE_TIME_ONLY},
            {
                "mode": "ONE_TIME_ONLY",
                "date": "2026-01-16",
                "time_range_start": "21:30",
                "time_range_end": "08:30",
            },
        ),
        (
            CUSTOM,
            {"mode": FirewallPolicyScheduleMode.CUSTOM},
            {
                "mode": "CUSTOM",
                "date_start": "2026-01-05",
                "date_end": "2026-01-30",
                "repeat_on_days": ["mon", "fri"],
                "time_all_day": False,
                "time_range_start": "20:00",
                "time_range_end": "06:00",
            },
        ),
        # A value change keeps the days as they are, even when none are chosen.
        (
            {**WEEKLY, "repeat_on_days": []},
            {"end_time": time(18, 0)},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": [],
                "time_all_day": False,
                "time_range_start": "15:00",
                "time_range_end": "18:00",
            },
        ),
        # Changing between the modes with days keeps the days and all day.
        (
            WEEKLY_ALL_DAY,
            {"mode": FirewallPolicyScheduleMode.CUSTOM},
            {
                "mode": "CUSTOM",
                "date_start": "2026-01-16",
                "date_end": "2026-01-17",
                "repeat_on_days": ["fri"],
                "time_all_day": True,
            },
        ),
        (
            CUSTOM,
            {"mode": FirewallPolicyScheduleMode.EVERY_WEEK},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["mon", "fri"],
                "time_all_day": False,
                "time_range_start": "20:00",
                "time_range_end": "06:00",
            },
        ),
        # Days are replaced and sent Monday first; unknown days are dropped.
        (
            WEEKLY,
            {"days": {"fri", "mon", "someday"}},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["mon", "fri"],
                "time_all_day": False,
                "time_range_start": "15:00",
                "time_range_end": "17:00",
            },
        ),
        (
            {**WEEKLY, "repeat_on_days": ["MON", "wed", "someday"]},
            {"end_time": time(18, 0)},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["wed"],
                "time_all_day": False,
                "time_range_start": "15:00",
                "time_range_end": "18:00",
            },
        ),
        # All day on drops the times; off doesn't bring back stored ones.
        (
            WEEKLY,
            {"all_day": True},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["mon", "wed"],
                "time_all_day": True,
            },
        ),
        (
            {**WEEKLY_ALL_DAY, **STALE_TIMES},
            {"all_day": False},
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["fri"],
                "time_all_day": False,
                "time_range_start": "09:00",
                "time_range_end": "12:00",
            },
        ),
        # A mode change and new values can be made together.
        (
            EVERY_DAY,
            {
                "mode": FirewallPolicyScheduleMode.EVERY_WEEK,
                "days": ["sat", "sun"],
                "start_time": time(10, 0),
            },
            {
                "mode": "EVERY_WEEK",
                "repeat_on_days": ["sat", "sun"],
                "time_all_day": False,
                "time_range_start": "10:00",
                "time_range_end": "08:00",
            },
        ),
        # Malformed stored values aren't sent back: they fall back to the
        # defaults a missing value would get.
        (
            {**EVERY_DAY, "time_range_start": None},
            {"end_time": time(7, 0)},
            {
                "mode": "EVERY_DAY",
                "time_range_start": "09:00",
                "time_range_end": "07:00",
            },
        ),
        (
            {**EVERY_DAY, "time_range_end": "25:00"},
            {"start_time": time(22, 0)},
            {
                "mode": "EVERY_DAY",
                "time_range_start": "22:00",
                "time_range_end": "12:00",
            },
        ),
        (
            {**ONE_TIME, "date": "2026-13-01"},
            {"end_time": time(7, 0)},
            {
                "mode": "ONE_TIME_ONLY",
                "date": "2026-01-16",
                "time_range_start": "21:30",
                "time_range_end": "07:00",
            },
        ),
        (
            {**CUSTOM, "date_end": "garbage"},
            {"start_date": date(2026, 1, 6)},
            {
                "mode": "CUSTOM",
                "date_start": "2026-01-06",
                "date_end": "2026-01-17",
                "repeat_on_days": ["mon", "fri"],
                "time_all_day": False,
                "time_range_start": "20:00",
                "time_range_end": "06:00",
            },
        ),
        # Keys left over from earlier modes are dropped.
        (
            {**WEEKLY_ALL_DAY, "date": "2026-01-01", **STALE_TIMES},
            {},
            {"mode": "EVERY_WEEK", "repeat_on_days": ["fri"], "time_all_day": True},
        ),
        ({"mode": "SUNRISE", **STALE_TIMES}, {}, {"mode": "unknown"}),
    ],
)
def test_build_schedule(
    current: dict[str, Any], changes: dict[str, Any], expected: dict[str, Any]
) -> None:
    """A built schedule has exactly the keys its mode uses."""
    assert build_schedule(current, TODAY, **changes) == expected


@pytest.mark.parametrize(
    ("current", "changes", "error"),
    [
        # Settings the new schedule doesn't use.
        (EVERY_DAY, {"days": ["mon"]}, ScheduleSettingUnusedError),
        (EVERY_DAY, {"all_day": True}, ScheduleSettingUnusedError),
        (EVERY_DAY, {"start_date": TODAY}, ScheduleSettingUnusedError),
        (ONE_TIME, {"end_date": TODAY}, ScheduleSettingUnusedError),
        ({"mode": "ALWAYS"}, {"start_time": time(9)}, ScheduleSettingUnusedError),
        (WEEKLY_ALL_DAY, {"end_time": time(9)}, ScheduleSettingUnusedError),
        (WEEKLY, {"all_day": True, "start_time": time(9)}, ScheduleSettingUnusedError),
        (
            EVERY_DAY,
            {"mode": FirewallPolicyScheduleMode.ALWAYS, "start_time": time(9)},
            ScheduleSettingUnusedError,
        ),
        # A schedule needs a day.
        (WEEKLY, {"days": []}, ScheduleWithoutDaysError),
        (WEEKLY, {"days": ["someday"]}, ScheduleWithoutDaysError),
        # A Custom schedule must end after the day it starts.
        (CUSTOM, {"end_date": date(2026, 1, 5)}, ScheduleDatesOutOfOrderError),
        (CUSTOM, {"start_date": date(2026, 2, 1)}, ScheduleDatesOutOfOrderError),
        # Checked after a malformed stored date falls back to its default.
        (
            {**CUSTOM, "date_end": "garbage"},
            {"start_date": date(2026, 2, 1)},
            ScheduleDatesOutOfOrderError,
        ),
        (
            {**CUSTOM, "date_start": None, "date_end": "2026-01-10"},
            {"end_time": time(7)},
            ScheduleDatesOutOfOrderError,
        ),
    ],
)
def test_build_schedule_rejects(
    current: dict[str, Any],
    changes: dict[str, Any],
    error: type[FirewallPolicyScheduleError],
) -> None:
    """Changes the schedule can't hold, or the UDM would reject, raise."""
    with pytest.raises(error):
        build_schedule(current, TODAY, **changes)
    # They aren't request errors, so callers can tell them apart.
    assert issubclass(error, ValueError)
