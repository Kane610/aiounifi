"""Test firewall policies API.

pytest --cov-report term-missing --cov=aiounifi.firewall_policy tests/test_firewall_policies.py
"""

import pytest

from aiounifi.models.firewall_policy import FirewallPolicyUpdateRequest

from .fixtures import FIREWALL_POLICIES


@pytest.mark.parametrize("firewall_policy_payload", [FIREWALL_POLICIES])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_firewall_policies(unifi_controller, unifi_called_with):
    """Test that we get the expected firewall policies."""
    firewall_policies = unifi_controller.firewall_policies
    await firewall_policies.update()
    assert unifi_called_with("get", "/v2/api/site/default/firewall-policies")
    assert len(firewall_policies.values()) == 2

    policy = firewall_policies["678ccddae3849d2932432f46"]
    assert policy.id == "678ccddae3849d2932432f46"
    assert policy.name == "Block Internet Access"
    assert policy.enabled is False
    assert policy.action == "BLOCK"
    assert policy.predefined is False
    assert policy.description == "Test policy"
    assert policy.protocol == "all"
    assert policy.ip_version == "BOTH"
    assert policy.source["matching_target"] == "CLIENT"
    assert policy.source["client_macs"] == ["18:8b:0e:e7:4f:30"]


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
    policy = FIREWALL_POLICIES[1]
    policy_id = policy["_id"]

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default/firewall-policies/batch",
        payload={},
    )

    await unifi_controller.request(FirewallPolicyUpdateRequest.create(policy))

    assert unifi_called_with(
        "put",
        "/proxy/network/v2/api/site/default/firewall-policies/batch",
        json=[policy],
    )
