"""Test traffic routes API for updateing as well as disabling and enabling traffic routes.

pytest --cov-report term-missing --cov=aiounifi.traffic_route tests/test_traffic_routes.py
"""
import pytest

from aiounifi.models.traffic_route import TrafficRouteSaveRequest

from .fixtures import TRAFFIC_RULES, WIRELESS_CLIENT


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_route_enable_request(
    mock_aioresponse, unifi_controller, unifi_called_with, enable
):
    """Test that traffic route can be enabled and disabled."""
    traffic_route_enabled = TRAFFIC_RULES[0]
    traffic_route_enabled_id = traffic_route_enabled["_id"]
    traffic_route_disabled = TRAFFIC_RULES[1]
    traffic_route_disabled_id = traffic_route_disabled["_id"]

    traffic_route_id = traffic_route_disabled_id if enable else traffic_route_enabled_id
    traffic_route = traffic_route_disabled if enable else traffic_route_enabled
    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default"
        + f"/trafficroutes/{traffic_route_id}",
        payload={},
    )

    await unifi_controller.request(
        TrafficRouteSaveRequest.create(traffic_route, enable)
    )

    traffic_route["enabled"] = enable
    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/trafficroutes/{traffic_route_id}",
        json=traffic_route,
    )


@pytest.mark.parametrize("traffic_route_payload", [TRAFFIC_RULES])
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_route_save(
    mock_aioresponse, unifi_controller, _mock_endpoints, enable
):
    """Test save method can enable and disable a traffic route."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()

    traffic_route_id = TRAFFIC_RULES[0 if not enable else 1]["_id"]

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default"
        + f"/trafficroutes/{traffic_route_id}",
        payload={},
    )
    await traffic_routes.save(traffic_routes[traffic_route_id], enable)
    assert traffic_routes[traffic_route_id].enabled is enable


@pytest.mark.parametrize("traffic_route_payload", [TRAFFIC_RULES])
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_traffic_route_enable_disable(
    mock_aioresponse, unifi_controller, _mock_endpoints, enable
):
    """Test individual methods for enabled and disabled."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()

    traffic_route_id = TRAFFIC_RULES[0 if not enable else 1]["_id"]
    traffic_route_call = traffic_routes.disable if not enable else traffic_routes.enable

    mock_aioresponse.put(
        "https://host:8443/proxy/network/v2/api/site/default"
        + f"/trafficroutes/{traffic_route_id}",
        payload={},
    )
    await traffic_route_call(traffic_routes[traffic_route_id])
    assert traffic_routes[traffic_route_id].enabled is enable


@pytest.mark.parametrize("is_unifi_os", [True])
async def test_no_traffic_routes(unifi_controller, _mock_endpoints, unifi_called_with):
    """Test that no traffic routes also work."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()
    assert unifi_called_with("get", "/proxy/network/v2/api/site/default/trafficroutes")
    assert len(traffic_routes.values()) == 0


@pytest.mark.parametrize("traffic_route_payload", [TRAFFIC_RULES])
async def test_traffic_routes(unifi_controller, _mock_endpoints, unifi_called_with):
    """Test that we get the expected traffic route."""
    traffic_routes = unifi_controller.traffic_routes
    await traffic_routes.update()
    assert unifi_called_with("get", "/v2/api/site/default/trafficroutes")
    assert len(traffic_routes.values()) == 2

    traffic_route = traffic_routes["6452cd9b859d5b11aa002ea1"]
    assert traffic_route.id == "6452cd9b859d5b11aa002ea1"
    assert traffic_route.description == "Test 1"
    assert traffic_route.enabled is False
    assert traffic_route.action == "BLOCK"
    assert traffic_route.matching_target == "INTERNET"
    assert traffic_route.target_devices == [
        {"client_mac": WIRELESS_CLIENT["mac"], "type": "CLIENT"}
    ]
