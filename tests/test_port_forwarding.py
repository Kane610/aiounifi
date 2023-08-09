"""Test port forwarding API.

pytest --cov-report term-missing --cov=aiounifi.port_forwarding tests/test_port_forwarding.py
"""

from aiounifi.controller import Controller

from .fixtures import PORT_FORWARDING


async def test_device_access_point(mock_aioresponse, unifi_controller: Controller):
    """Test device class on an access point."""
    port_forwarding = unifi_controller.port_forwarding
    port_forwarding.process_raw([PORT_FORWARDING["data"][0]])

    assert len(port_forwarding.values()) == 1
