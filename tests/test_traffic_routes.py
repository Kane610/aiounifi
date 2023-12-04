"""Test traffic routes API for disabling and enabling traffic routes.

pytest --cov-report term-missing --cov=aiounifi.traffic_route tests/test_traffic_routes.py
"""
from copy import deepcopy

import pytest

from aiounifi.models.traffic_route import (
    Domain,
    IPAddress,
    MatchingTarget,
    TrafficRouteSaveRequest,
)

from .fixtures import TRAFFIC_ROUTES, WIRELESS_CLIENT


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_route_enable_request(
    mock_aioresponse, unifi_controller, unifi_called_with, enable
):
    """Test that traffic route can be enabled and disabled."""
    # Use a copy so we don't modify our fixture (this should probably be a real fixture)
    traffic_routes = deepcopy(TRAFFIC_ROUTES)

    traffic_route_enabled = traffic_routes[0]
    traffic_route_enabled_id = traffic_route_enabled["_id"]
    assert traffic_route_enabled["enabled"] is True

    traffic_route_disabled = traffic_routes[1]
    traffic_route_disabled_id = traffic_route_disabled["_id"]
    assert traffic_route_disabled["enabled"] is False

    traffic_route_id = traffic_route_disabled_id if enable else traffic_route_enabled_id
    traffic_route = traffic_route_disabled if enable else traffic_route_enabled
    # Make sure initial state is what's expected
    assert traffic_route["enabled"] is not enable

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default"
        + f"/trafficroutes/{traffic_route_id}",
        payload={},
    )

    await unifi_controller.request(
        TrafficRouteSaveRequest.create(traffic_route, enable)
    )

    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/trafficroutes/{traffic_route_id}",
        json=traffic_route | {"enabled": enable},
    )


@pytest.mark.parametrize("traffic_route_payload", [TRAFFIC_ROUTES])
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("traffic_route_id", [route["_id"] for route in TRAFFIC_ROUTES])
@pytest.mark.parametrize("enable", [True, False, None])
async def test_traffic_route_save(
    mock_aioresponse,
    unifi_controller,
    unifi_called_with,
    _mock_endpoints,
    enable,
    traffic_route_id,
):
    """Test save method can enable and disable a traffic route."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()

    traffic_route = traffic_routes[traffic_route_id]

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default"
        + f"/trafficroutes/{traffic_route_id}",
        payload={},
    )
    await traffic_routes.save(traffic_route, enable)
    if enable is not None:
        # If setting enabled, verify it was set
        assert unifi_called_with(
            "put",
            f"/proxy/network/v2/api/site/default/trafficroutes/{traffic_route_id}",
            json=traffic_route.raw | {"enabled": enable},
        )
    else:
        # Otherwise, verify it was not set
        assert unifi_called_with(
            "put",
            f"/proxy/network/v2/api/site/default/trafficroutes/{traffic_route_id}",
            json=traffic_route.raw,
        )


@pytest.mark.parametrize("traffic_route_payload", [TRAFFIC_ROUTES])
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("traffic_route_id", [route["_id"] for route in TRAFFIC_ROUTES])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_route_enable_disable(
    mock_aioresponse,
    _mock_endpoints,
    unifi_called_with,
    unifi_controller,
    enable,
    traffic_route_id,
):
    """Test individual methods for enabled and disabled."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()

    traffic_route = traffic_routes[traffic_route_id]
    traffic_route_call = traffic_routes.disable if not enable else traffic_routes.enable

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default"
        + f"/trafficroutes/{traffic_route_id}",
        payload={},
    )
    await traffic_route_call(traffic_routes[traffic_route_id])
    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/trafficroutes/{traffic_route_id}",
        json=traffic_route.raw | {"enabled": enable},
    )


@pytest.mark.parametrize("is_unifi_os", [True])
async def test_no_traffic_routes(unifi_controller, _mock_endpoints, unifi_called_with):
    """Test that no traffic routes also work."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()
    assert unifi_called_with("get", "/proxy/network/v2/api/site/default/trafficroutes")
    assert len(traffic_routes.values()) == 0


@pytest.mark.parametrize("traffic_route_payload", [TRAFFIC_ROUTES])
async def test_traffic_routes(unifi_controller, _mock_endpoints, unifi_called_with):
    """Test that we get the expected traffic route."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()
    assert unifi_called_with("get", "/v2/api/site/default/trafficroutes")
    assert len(traffic_routes.values()) == 3

    traffic_route = traffic_routes["6468ecd4c1dd1932ad2f801c"]
    assert traffic_route.id == "6468ecd4c1dd1932ad2f801c"
    assert traffic_route.description == "Test domain rule"
    assert traffic_route.domains == [
        Domain(domain="example.com", port_ranges=[], ports=[]),
    ]
    assert traffic_route.enabled is True
    assert traffic_route.ip_addresses == []
    assert traffic_route.ip_ranges == []
    assert traffic_route.matching_target == MatchingTarget.DOMAIN
    assert traffic_route.network_id == "5a32aa4ee4b047ede36a85a8"
    assert traffic_route.next_hop == ""
    assert traffic_route.regions == []
    assert traffic_route.target_devices == [
        {"network_id": WIRELESS_CLIENT["network_id"], "type": "NETWORK"},
    ]

    traffic_route = traffic_routes["655565af1e1c2754a39388a4"]
    assert traffic_route.id == "655565af1e1c2754a39388a4"
    assert traffic_route.description == "Test all internet rule"
    assert traffic_route.domains == []
    assert traffic_route.enabled is False
    assert traffic_route.ip_addresses == []
    assert traffic_route.ip_ranges == []
    assert traffic_route.matching_target == MatchingTarget.INTERNET
    assert traffic_route.network_id == "5a32aa4ee4b047ede36a85a8"
    assert traffic_route.next_hop == ""
    assert traffic_route.regions == []
    assert traffic_route.target_devices == [
        {"network_id": WIRELESS_CLIENT["network_id"], "type": "NETWORK"},
    ]

    traffic_route = traffic_routes["655566f91e1c2754a393892c"]
    assert traffic_route.id == "655566f91e1c2754a393892c"
    assert traffic_route.description == "Test IP rule"
    assert traffic_route.domains == []
    assert traffic_route.enabled is False
    assert traffic_route.ip_addresses == [
        IPAddress(ip_or_subnet="1.1.1.1", ip_version="v4", port_ranges=[], ports=[]),
    ]
    assert traffic_route.ip_ranges == []
    assert traffic_route.matching_target == MatchingTarget.IP
    assert traffic_route.network_id == "5a32aa4ee4b047ede36a85a8"
    assert traffic_route.next_hop == ""
    assert traffic_route.regions == []
    assert traffic_route.target_devices == [
        {"network_id": WIRELESS_CLIENT["network_id"], "type": "NETWORK"},
    ]
