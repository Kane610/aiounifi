"""Test port forwarding API.

pytest --cov-report term-missing --cov=aiounifi.port_forwarding tests/test_port_forwarding.py
"""

from aiounifi.controller import Controller
from aiounifi.models.port_forward import PortForwardEnableRequest, TypedPortForward

from .fixtures import PORT_FORWARDING


async def test_port_forward_enable_request(
    mock_aioresponse, unifi_controller: Controller, unifi_called_with
):
    """Test port forward enable request work."""
    mock_aioresponse.post(
        "https://host:8443/api/s/default/rest/portforward",
        payload={},
    )

    expected: TypedPortForward = PORT_FORWARDING["data"][0].copy()
    expected["enabled"] = False

    await unifi_controller.request(
        PortForwardEnableRequest.create(
            PORT_FORWARDING["data"][0].copy(),
            False,
        )
    )

    assert unifi_called_with(
        "post",
        "/api/s/default/rest/portforward",
        json=expected,
    )


async def test_port_forward(mock_aioresponse, unifi_controller: Controller):
    """Test device class on an access point."""
    port_forwarding = unifi_controller.port_forwarding
    port_forwarding.process_raw([PORT_FORWARDING["data"][0]])

    assert len(port_forwarding.values()) == 1

    port_forward = port_forwarding[PORT_FORWARDING["data"][0]["_id"]]
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
