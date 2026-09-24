"""Test firewall policies API.

pytest --cov-report term-missing --cov=aiounifi.firewall_policy tests/test_firewall_policies.py
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from aiounifi.models.firewall_policy import (
    FirewallPolicy,
    FirewallPolicyScheduleMode,
    FirewallPolicyUpdateRequest,
    is_schedule_active,
)

from .fixtures import FIREWALL_POLICIES, FIREWALL_POLICIES_SCHEDULE_SHAPES


@pytest.mark.parametrize("firewall_policy_payload", [FIREWALL_POLICIES])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_firewall_policies(unifi_controller, unifi_called_with):
    """Test that we get the expected firewall policies."""
    firewall_policies = unifi_controller.firewall_policies
    await firewall_policies.update()
    assert unifi_called_with("get", "/v2/api/site/default/firewall-policies")
    assert len(firewall_policies.values()) == 1

    policy = firewall_policies["678ceb9fe3849d293243405c"]
    assert policy.id == "678ceb9fe3849d293243405c"
    assert policy.action == "ALLOW"
    assert policy.connection_state_type == "ALL"
    assert policy.connection_states == []
    assert policy.create_allow_respond is True
    assert policy.description == ""
    assert policy.destination == {
        "match_opposite_ports": False,
        "matching_target": "ANY",
        "port_matching_type": "ANY",
        "zone_id": "678ccc26e3849d2932432e26",
    }
    assert policy.enabled is True
    assert policy.icmp_typename == "ANY"
    assert policy.icmp_v6_typename == "ANY"
    assert policy.index == 10000
    assert policy.ip_version == "BOTH"
    assert policy.logging is False
    assert policy.match_ip_sec is False
    assert policy.match_opposite_protocol is False
    assert policy.name == "Allow internal to IoT"
    assert policy.predefined is False
    assert policy.protocol == "all"
    assert policy.schedule == {
        "mode": "EVERY_DAY",
        "repeat_on_days": [],
        "time_all_day": False,
        "time_range_end": "12:00",
        "time_range_start": "09:00",
    }
    assert policy.source == {
        "match_opposite_ports": False,
        "matching_target": "ANY",
        "port_matching_type": "ANY",
        "zone_id": "678c63bc2d97692f08adcdfa",
    }


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_no_firewall_policies(unifi_controller, unifi_called_with):
    """Test that no firewall policies also work."""
    firewall_policies = unifi_controller.firewall_policies
    await firewall_policies.update()
    assert unifi_called_with(
        "get", "/proxy/network/v2/api/site/default/firewall-policies"
    )
    assert len(firewall_policies.values()) == 0


@pytest.mark.parametrize("is_unifi_os", [True])
async def test_firewall_policy_update_request(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test that firewall policy can be updated."""
    policy = FIREWALL_POLICIES[0]
    policy_id = policy["_id"]

    mock_aioresponse.put(
        f"https://host:8443/proxy/network/v2/api/site/default/firewall-policies/{policy_id}",
        payload={},
    )

    await unifi_controller.request(FirewallPolicyUpdateRequest.create(policy))

    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/firewall-policies/{policy_id}",
        json=policy,
    )


@pytest.mark.parametrize("firewall_policy_payload", [FIREWALL_POLICIES_SCHEDULE_SHAPES])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_firewall_policy_schedule_shapes(unifi_controller):
    """Schedules carry only the keys their mode needs."""
    firewall_policies = unifi_controller.firewall_policies
    await firewall_policies.update()

    always = firewall_policies["a1a1a1a1a1a1a1a1a1a1a1a1"]
    assert always.schedule == {"mode": "ALWAYS"}
    assert always.schedule_mode is FirewallPolicyScheduleMode.ALWAYS

    one_time = firewall_policies["b2b2b2b2b2b2b2b2b2b2b2b2"]
    assert one_time.schedule_mode is FirewallPolicyScheduleMode.ONE_TIME_ONLY
    assert one_time.schedule["date"] == "2026-09-22"

    custom = firewall_policies["c3c3c3c3c3c3c3c3c3c3c3c3"]
    assert custom.schedule_mode is FirewallPolicyScheduleMode.CUSTOM
    assert custom.schedule["time_all_day"] is True

    weekly = firewall_policies["d4d4d4d4d4d4d4d4d4d4d4d4"]
    assert weekly.schedule_mode is FirewallPolicyScheduleMode.EVERY_WEEK

    custom_timed = firewall_policies["e5e5e5e5e5e5e5e5e5e5e5e5"]
    assert custom_timed.schedule_mode is FirewallPolicyScheduleMode.CUSTOM
    assert custom_timed.schedule["time_range_start"] == "20:00"

    every_day = FIREWALL_POLICIES[0]["schedule"]["mode"]
    assert FirewallPolicyScheduleMode(every_day) is FirewallPolicyScheduleMode.EVERY_DAY


def test_firewall_policy_schedule_mode_unknown():
    """Unrecognised modes map to UNKNOWN instead of raising."""
    assert FirewallPolicyScheduleMode("SUNRISE") is FirewallPolicyScheduleMode.UNKNOWN


DENVER = ZoneInfo("America/Denver")


def _at(value: str) -> datetime:
    """Parse 'YYYY-MM-DD HH:MM' as a Denver wall-clock time."""
    return datetime.fromisoformat(value).replace(tzinfo=DENVER)


EVERY_DAY_OVERNIGHT = {
    "mode": "EVERY_DAY",
    "time_range_start": "21:00",
    "time_range_end": "08:00",
}
EVERY_DAY_MORNING = {
    "mode": "EVERY_DAY",
    "repeat_on_days": [],
    "time_all_day": False,
    "time_range_start": "09:00",
    "time_range_end": "12:00",
}
ONE_TIME_OVERNIGHT = {
    "mode": "ONE_TIME_ONLY",
    "date": "2026-09-22",
    "time_range_start": "21:30",
    "time_range_end": "08:30",
}
WEEKLY_AFTERNOON = {
    "mode": "EVERY_WEEK",
    "repeat_on_days": ["mon", "wed"],
    "time_all_day": False,
    "time_range_start": "15:00",
    "time_range_end": "17:00",
}
WEEKLY_OVERNIGHT = {
    "mode": "EVERY_WEEK",
    "repeat_on_days": ["fri"],
    "time_all_day": False,
    "time_range_start": "22:00",
    "time_range_end": "02:00",
}
CUSTOM_OVERNIGHT = {
    "mode": "CUSTOM",
    "date_start": "2026-09-01",
    "date_end": "2026-12-18",
    "repeat_on_days": ["mon", "fri"],
    "time_all_day": False,
    "time_range_start": "20:00",
    "time_range_end": "06:00",
}
CUSTOM_ALL_DAY = {
    "mode": "CUSTOM",
    "date_start": "2026-08-21",
    "date_end": "2026-08-22",
    "repeat_on_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "time_all_day": True,
}


@pytest.mark.parametrize(
    ("schedule", "now", "expected"),
    [
        ({"mode": "ALWAYS"}, "2026-09-23 03:00", True),
        # Daytime window: start inclusive, end exclusive.
        (EVERY_DAY_MORNING, "2026-09-23 08:59", False),
        (EVERY_DAY_MORNING, "2026-09-23 09:00", True),
        (EVERY_DAY_MORNING, "2026-09-23 11:59", True),
        (EVERY_DAY_MORNING, "2026-09-23 12:00", False),
        # Overnight window: both sides of midnight.
        (EVERY_DAY_OVERNIGHT, "2026-09-23 20:59", False),
        (EVERY_DAY_OVERNIGHT, "2026-09-23 21:00", True),
        (EVERY_DAY_OVERNIGHT, "2026-09-23 23:59", True),
        (EVERY_DAY_OVERNIGHT, "2026-09-24 00:00", True),
        (EVERY_DAY_OVERNIGHT, "2026-09-24 07:59", True),
        (EVERY_DAY_OVERNIGHT, "2026-09-24 08:00", False),
        (EVERY_DAY_OVERNIGHT, "2026-09-24 12:00", False),
        # One time: only the window that starts on the date.
        (ONE_TIME_OVERNIGHT, "2026-09-20 22:00", False),
        (ONE_TIME_OVERNIGHT, "2026-09-22 21:29", False),
        (ONE_TIME_OVERNIGHT, "2026-09-22 21:30", True),
        (ONE_TIME_OVERNIGHT, "2026-09-23 00:03", True),
        (ONE_TIME_OVERNIGHT, "2026-09-23 08:29", True),
        (ONE_TIME_OVERNIGHT, "2026-09-23 08:30", False),
        (ONE_TIME_OVERNIGHT, "2026-09-23 22:00", False),
        # Every week: 2026-09-21 is a Monday, 2026-09-22 a Tuesday.
        (WEEKLY_AFTERNOON, "2026-09-21 15:00", True),
        (WEEKLY_AFTERNOON, "2026-09-22 15:00", False),
        (WEEKLY_AFTERNOON, "2026-09-23 16:59", True),
        # Overnight weekly window started on Friday 2026-09-25.
        (WEEKLY_OVERNIGHT, "2026-09-26 01:30", True),
        (WEEKLY_OVERNIGHT, "2026-09-27 01:30", False),
        # Custom: days and date range both apply.
        (CUSTOM_ALL_DAY, "2026-08-20 23:59", False),
        (CUSTOM_ALL_DAY, "2026-08-21 00:00", True),
        (CUSTOM_ALL_DAY, "2026-08-22 23:59", True),
        (CUSTOM_ALL_DAY, "2026-08-23 00:00", False),
        # Custom with times: Friday 2026-09-25 20:00 runs into Saturday.
        (CUSTOM_OVERNIGHT, "2026-09-25 19:59", False),
        (CUSTOM_OVERNIGHT, "2026-09-25 20:00", True),
        (CUSTOM_OVERNIGHT, "2026-09-26 05:59", True),
        (CUSTOM_OVERNIGHT, "2026-09-26 20:00", False),
        # The window starting on the last date still runs past it.
        (CUSTOM_OVERNIGHT, "2026-12-19 05:00", True),
        (CUSTOM_OVERNIGHT, "2026-12-21 21:00", False),
        # Seconds are ignored: minute resolution.
        (EVERY_DAY_MORNING, "2026-09-23 11:59:59", True),
    ],
)
def test_is_schedule_active(schedule, now, expected):
    """Schedules are evaluated against the UDM's wall clock."""
    assert is_schedule_active(schedule, _at(now)) is expected


@pytest.mark.parametrize(
    "schedule",
    [
        {"mode": "SUNRISE"},
        {
            "mode": "ONE_TIME_ONLY",
            "time_range_start": "21:00",
            "time_range_end": "08:00",
        },
        {"mode": "EVERY_DAY", "time_range_start": "21:00"},
        {"mode": "EVERY_WEEK", "time_range_start": "15:00", "time_range_end": "17:00"},
        {"mode": "CUSTOM", "repeat_on_days": ["mon"], "time_all_day": True},
    ],
)
def test_is_schedule_active_incomplete(schedule):
    """Unknown modes and schedules missing a required key give None."""
    assert is_schedule_active(schedule, _at("2026-09-21 15:30")) is None


@pytest.mark.parametrize(
    "schedule",
    [
        {"mode": "EVERY_DAY", "time_range_start": "24:00", "time_range_end": "08:00"},
        {"mode": "EVERY_DAY", "time_range_start": "9", "time_range_end": "08:00"},
        {
            "mode": "ONE_TIME_ONLY",
            "date": "2026-13-01",
            "time_range_start": "21:00",
            "time_range_end": "08:00",
        },
    ],
)
def test_is_schedule_active_malformed_values(schedule):
    """Malformed controller values give None rather than raising."""
    assert is_schedule_active(schedule, _at("2026-09-21 22:00")) is None


def test_is_schedule_active_rejects_naive_datetime():
    """A naive datetime is a caller bug: raise instead of guessing."""
    with pytest.raises(ValueError, match="timezone-aware"):
        is_schedule_active({"mode": "ALWAYS"}, datetime(2026, 9, 23, 3, 0))


def test_is_schedule_active_across_fall_back():
    """DST fall-back (2026-11-01 in Denver) doesn't break an overnight window."""
    first_130 = datetime(2026, 11, 1, 1, 30, tzinfo=DENVER, fold=0)
    second_130 = datetime(2026, 11, 1, 1, 30, tzinfo=DENVER, fold=1)
    assert is_schedule_active(EVERY_DAY_OVERNIGHT, first_130) is True
    assert is_schedule_active(EVERY_DAY_OVERNIGHT, second_130) is True
    assert is_schedule_active(EVERY_DAY_OVERNIGHT, _at("2026-11-01 08:00")) is False


def test_firewall_policy_is_active():
    """A disabled policy is never active; an enabled one follows its schedule."""
    raw = {**FIREWALL_POLICIES[0], "schedule": EVERY_DAY_MORNING}
    assert FirewallPolicy(raw).is_active(_at("2026-09-23 10:00")) is True
    assert FirewallPolicy(raw).is_active(_at("2026-09-23 13:00")) is False
    disabled = FirewallPolicy({**raw, "enabled": False})
    assert disabled.is_active(_at("2026-09-23 10:00")) is False
    unknown = FirewallPolicy({**raw, "schedule": {"mode": "SUNRISE"}})
    assert unknown.is_active(_at("2026-09-23 10:00")) is None
