"""Test port forwarding API."""
import pytest

from aiounifi.controller import Controller
from aiounifi.models.port_forward import PortForwardEnableRequest, TypedPortForward

from .fixtures import PORT_FORWARDING


@pytest.mark.parametrize("port_forward_payload", [PORT_FORWARDING["data"]])
async def test_port_forward(
    mock_aioresponse, unifi_controller: Controller, _mock_endpoints, unifi_called_with
):
    """Test port forwarding interface and model."""
    port_forwarding = unifi_controller.port_forwarding
    await port_forwarding.update()
    assert len(port_forwarding.values()) == 1

    port_forward = next(iter(port_forwarding.values()))
    assert port_forward.id == "5a32aa4ee4b0412345678911"
    assert port_forward.destination_port == "12345"
    assert port_forward.enabled is True
    assert port_forward.forward_port == "23456"
    assert port_forward.forward_ip == "10.0.0.2"
    assert port_forward.name == "New port forward"
    assert port_forward.port_forward_interface == "wan"
    assert port_forward.protocol == "tcp_udp"
    assert port_forward.site_id == "5a32aa4ee4b0412345678910"
    assert port_forward.source == "any"

    # Port forward enable request

    pf_id = PORT_FORWARDING["data"][0]["_id"]
    mock_aioresponse.put(
        f"https://host:8443/api/s/default/rest/portforward/{pf_id}",
        payload={},
    )

    expected: TypedPortForward = PORT_FORWARDING["data"][0].copy()
    expected["enabled"] = False

    await unifi_controller.request(PortForwardEnableRequest.create(port_forward, False))

    assert unifi_called_with(
        "put",
        f"/api/s/default/rest/portforward/{pf_id}",
        json=expected,
    )
    assert port_forward.raw != expected
