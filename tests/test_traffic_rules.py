"""Test traffic rules API for disabling and enabling traffic rules.

pytest --cov-report term-missing --cov=aiounifi.traffic_rule tests/test_traffic_rules.py
"""

import pytest

from aiounifi.interfaces.traffic_rules import TrafficRules
from aiounifi.models.traffic_rule import TrafficRuleEnableRequest

from .fixtures import TRAFFIC_RULES, WIRELESS_CLIENT


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_rule_enable_request(
    mock_aioresponse, unifi_controller, unifi_called_with, enable
):
    """Test that traffic rule can be enabled and disabled through TrafficRuleEnableRequest."""
    traffic_rule_enabled = TRAFFIC_RULES[0]
    traffic_rule_enabled_id = traffic_rule_enabled["_id"]
    traffic_rule_disabled = TRAFFIC_RULES[1]
    traffic_rule_disabled_id = traffic_rule_disabled["_id"]

    traffic_rule_id = traffic_rule_disabled_id if enable else traffic_rule_enabled_id
    traffic_rule = traffic_rule_disabled if enable else traffic_rule_enabled
    mock_aioresponse.put(
        f"https://host:8443/proxy/network/v2/api/site/default/trafficrules/{traffic_rule_id}",
        payload={},
    )

    await unifi_controller.request(
        TrafficRuleEnableRequest.create(traffic_rule, enable)
    )

    traffic_rule["enabled"] = enable
    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/trafficrules/{traffic_rule_id}",
        json=traffic_rule,
    )

@pytest.mark.parametrize("traffic_rule_payload", [TRAFFIC_RULES])
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_rule_toggle(
        mock_aioresponse, unifi_controller, _mock_endpoints, unifi_called_with, enable
):
    """Test that traffic rule can be enabled and disabled through the individual methods ."""
    traffic_rules = unifi_controller.traffic_rules
    await traffic_rules.update()

    traffic_rule_enabled_id = TRAFFIC_RULES[0]["_id"]
    traffic_rule_disabled_id = TRAFFIC_RULES[1]["_id"]
    traffic_rule_enabled = traffic_rules[traffic_rule_enabled_id]
    traffic_rule_disabled = traffic_rules[traffic_rule_disabled_id]

    if enable:
        mock_aioresponse.put(
            f"https://host:8443/proxy/network/v2/api/site/default/trafficrules/{traffic_rule_disabled_id}",
            payload={},
        )
        await traffic_rules.toggle(traffic_rule_disabled, enable)
        traffic_rule = traffic_rules.get(traffic_rule_disabled_id)
        assert traffic_rule.enabled == True
    else:
        mock_aioresponse.put(
            f"https://host:8443/proxy/network/v2/api/site/default/trafficrules/{traffic_rule_enabled_id}",
            payload={},
        )
        await traffic_rules.toggle(traffic_rule_enabled, enable)
        traffic_rule = traffic_rules.get(traffic_rule_enabled_id)
        assert traffic_rule.enabled == False

@pytest.mark.parametrize("traffic_rule_payload", [TRAFFIC_RULES])
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_rule_enable_disable(
        mock_aioresponse, unifi_controller, _mock_endpoints, unifi_called_with, enable
):
    """Test that traffic rule can be enabled and disabled through the individual methods ."""
    traffic_rules = unifi_controller.traffic_rules
    await traffic_rules.update()
    traffic_rule_enabled_id = TRAFFIC_RULES[0]["_id"]
    traffic_rule_disabled_id = TRAFFIC_RULES[1]["_id"]

    traffic_rule_enabled = traffic_rules[traffic_rule_enabled_id]
    traffic_rule_disabled = traffic_rules[traffic_rule_disabled_id]

    if enable:
        mock_aioresponse.put(
            f"https://host:8443/proxy/network/v2/api/site/default/trafficrules/{traffic_rule_disabled_id}",
            payload={},
        )
        await traffic_rules.enable(traffic_rule_disabled)
        traffic_rule = traffic_rules.get(traffic_rule_disabled_id)
        assert traffic_rule.enabled == True
    else:
        mock_aioresponse.put(
            f"https://host:8443/proxy/network/v2/api/site/default/trafficrules/{traffic_rule_enabled_id}",
            payload={},
        )
        await traffic_rules.disable(traffic_rule_enabled)
        traffic_rule = traffic_rules.get(traffic_rule_enabled_id)
        assert traffic_rule.enabled == False

@pytest.mark.parametrize("is_unifi_os", [True])
async def test_no_traffic_rules(
    mock_aioresponse, unifi_controller, _mock_endpoints, unifi_called_with
):
    """Test that no traffic rules also work."""
    traffic_rules = unifi_controller.traffic_rules
    await traffic_rules.update()
    assert unifi_called_with("get", "/proxy/network/v2/api/site/default/trafficrules")
    assert len(traffic_rules.values()) == 0


@pytest.mark.parametrize("traffic_rule_payload", [TRAFFIC_RULES])
async def test_traffic_rules(
    mock_aioresponse, unifi_controller, _mock_endpoints, unifi_called_with
):
    """Test that we get the expected traffic rule."""
    traffic_rules = unifi_controller.traffic_rules
    await traffic_rules.update()
    assert unifi_called_with("get", "/v2/api/site/default/trafficrules")
    assert len(traffic_rules.values()) == 2

    traffic_rule = traffic_rules["6452cd9b859d5b11aa002ea1"]
    assert traffic_rule.id == "6452cd9b859d5b11aa002ea1"
    assert traffic_rule.description == "Test 1"
    assert traffic_rule.enabled is False
    assert traffic_rule.action == "BLOCK"
    assert traffic_rule.matching_target == "INTERNET"
    assert traffic_rule.target_devices == [
        {"client_mac": WIRELESS_CLIENT["mac"], "type": "CLIENT"}
    ]
