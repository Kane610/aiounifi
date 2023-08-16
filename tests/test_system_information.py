"""Test system information API.

pytest --cov-report term-missing --cov=aiounifi.system_information tests/test_system_information.py
"""

from aiounifi.controller import Controller
from aiounifi.models.system_information import SystemInformationRequest

from .fixtures import SYSTEM_INFORMATION


async def test_sys_info_request(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test power cycle port work."""
    mock_aioresponse.get("https://host:8443/api/s/default/stat/sysinfo", payload={})
    await unifi_controller.request(SystemInformationRequest.create())
    assert unifi_called_with("get", "/api/s/default/stat/sysinfo")


async def test_system_information(
    mock_aioresponse, unifi_controller: Controller, unifi_called_with
):
    """Test port forwarding interface and model."""
    system_information = unifi_controller.system_information
    system_information.process_raw([SYSTEM_INFORMATION])

    assert len(system_information.values()) == 1

    sys_info = system_information[SYSTEM_INFORMATION["anonymous_controller_id"]]
    assert sys_info.anonymous_controller_id == "24f81231-a456-4c32-abcd-f5612345385f"
    assert sys_info.device_type == "UDMPRO"
    assert sys_info.hostname == "UDMP"
    assert sys_info.ip_address == ["1.2.3.4"]
    assert sys_info.is_cloud_console is False
    assert sys_info.name == "UDMP"
    assert sys_info.previous_version == "7.4.156"
    assert sys_info.update_available is False
    assert sys_info.uptime == 1196290
    assert sys_info.version == "7.4.162"
