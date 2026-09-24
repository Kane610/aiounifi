"""Test firewall policies API.

pytest --cov-report term-missing --cov=aiounifi.firewall_policy tests/test_firewall_policies.py
"""

import pytest

from aiounifi.models.firewall_policy import (
    FirewallPolicyScheduleMode,
    FirewallPolicyUpdateRequest,
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
