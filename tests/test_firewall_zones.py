"""Test firewall zones API.

pytest --cov-report term-missing --cov=aiounifi.firewall_zone tests/test_firewall_zones.py
"""

import pytest

from aiounifi.models.firewall_zone import FirewallZoneUpdateRequest

from .fixtures import FIREWALL_ZONES


@pytest.mark.parametrize("firewall_zone_payload", [FIREWALL_ZONES])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_firewall_zones(unifi_controller, unifi_called_with):
    """Test that we get the expected firewall zones."""
    firewall_zones = unifi_controller.firewall_zones
    await firewall_zones.update()
    assert unifi_called_with("get", "/v2/api/site/default/firewall/zone")
    assert len(firewall_zones.values()) == 2

    zone = firewall_zones["678ccc26e3849d2932432e26"]
    assert zone.id == "678ccc26e3849d2932432e26"
    assert zone.name == "LAN"
    assert zone.attr_no_edit is True
    assert zone.default_zone is True
    assert zone.network_ids == ["678ccc26e3849d2932432e20"]
    assert zone.zone_key == "lan"


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_no_firewall_zones(unifi_controller, unifi_called_with):
    """Test that no firewall zones also work."""
    firewall_zones = unifi_controller.firewall_zones
    await firewall_zones.update()
    assert unifi_called_with("get", "/proxy/network/v2/api/site/default/firewall/zone")
    assert len(firewall_zones.values()) == 0


@pytest.mark.parametrize("is_unifi_os", [True])
async def test_firewall_zone_update_request(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test that firewall zone can be updated."""
    zone = FIREWALL_ZONES[0]
    zone_id = zone["_id"]

    mock_aioresponse.put(
        f"https://host:8443/proxy/network/v2/api/site/default/firewall/zone/{zone_id}",
        payload={},
    )

    await unifi_controller.request(FirewallZoneUpdateRequest.create(zone))

    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/firewall/zone/{zone_id}",
        json=zone,
    )
