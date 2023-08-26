"""Test traffic rules API for disabling and enabling traffic rules.

pytest --cov-report term-missing --cov=aiounifi.traffic_rule tests/test_traffic_rules.py
"""

import pytest

from aiounifi.models.traffic_rule import (
    TrafficRuleEnableRequest,
    TrafficRuleListRequest,
)

from .fixtures import TRAFFIC_RULES, WIRELESS_CLIENT

@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_rule_enable(
    mock_aioresponse, unifi_controller, unifi_called_with, enable
):
    """Test that wlan can be enabled and disabled."""
    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default/trafficrules/6452cd9b859d5b11aa002ea1", payload={}
    )

    traffic_rule = TRAFFIC_RULES[0]

    await unifi_controller.request(TrafficRuleEnableRequest.create(traffic_rule, enable))

    traffic_rule["enabled"] = enable
    assert unifi_called_with(
        "put",
        "/proxy/network/v2/api/site/default/trafficrules/6452cd9b859d5b11aa002ea1",
        json=traffic_rule,
    )

async def test_no_traffic_rules(
    mock_aioresponse, unifi_controller, _mock_traffic_rule_endpoint, unifi_called_with
):
    """Test that no traffic rules also work."""
    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default/trafficrules",
        payload={},
        repeat=True,
    )
    traffic_rules = unifi_controller.traffic_rules
    await traffic_rules.update()

    assert unifi_called_with("get", "/proxy/network/v2/api/site/default/trafficrules")
    assert len(traffic_rules.values()) == 0

@pytest.mark.parametrize("traffic_rule_payload", [TRAFFIC_RULES])
async def test_traffic_rules(
    mock_aioresponse, unifi_controller, _mock_traffic_rule_endpoint, unifi_called_with
):
    """Test that different types of ports work."""
    traffic_rules = unifi_controller.traffic_rules
    await traffic_rules.update()
    assert len(traffic_rules.values()) == 2

    traffic_rule = traffic_rules["6452cd9b859d5b11aa002ea1"]
    assert traffic_rule.id == "6452cd9b859d5b11aa002ea1"
    assert traffic_rule.description == "Test 1"
    assert traffic_rule.enabled is False
    assert traffic_rule.action == "BLOCK"
    assert traffic_rule.matching_target == "INTERNET"
    assert traffic_rule.target_devices == [
                {
                    "client_mac": WIRELESS_CLIENT["mac"],
                    "type": "CLIENT"
                }
            ]

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default/trafficrules/6452cd9b859d5b11aa002ea1",
        payload={},
        repeat=True,
    )

    traffic_rule_raw = traffic_rule.raw

    traffic_rule_raw["enabled"] = True
    await traffic_rules.enable(traffic_rule)
    assert unifi_called_with(
        "put",
        "/proxy/network/v2/api/site/default/trafficrules/6452cd9b859d5b11aa002ea1",
        json=traffic_rule_raw,
    )

    traffic_rule_raw["enabled"] = False
    await traffic_rules.disable(traffic_rule)
    assert unifi_called_with(
        "put",
        "/proxy/network/v2/api/site/default/trafficrules/6452cd9b859d5b11aa002ea1",
        json=traffic_rule_raw,
    )