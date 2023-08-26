"""Setup common test helpers."""

from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

import aiohttp
from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller
from aiounifi.models.configuration import Configuration
from aiounifi.websocket import WebsocketSignal


@pytest.fixture(name="mock_aioresponse")
def aioresponse_fixture() -> aioresponses:
    """AIOHTTP fixture."""
    with aioresponses() as mock:
        yield mock


@pytest.fixture(name="is_unifi_os")
def is_unifi_os_fixture() -> bool:
    """If use UniFi OS response."""
    return False


@pytest.fixture
def unifi_called_with(mock_aioresponse) -> Callable[[str, str, dict[str, Any]], bool]:
    """Verify UniFi call was made with the expected parameters."""

    def verify_call(method: str, path: str, **kwargs: dict[str, Any]) -> bool:
        """Verify expected data was provided with a request to aioresponse."""
        for req, call_list in mock_aioresponse.requests.items():
            if method != req[0]:
                continue

            if not req[1].path.endswith(path):
                continue

            for call in call_list:
                successful_match = True

                for key, value in kwargs.items():
                    if key not in call[1] or call[1][key] != value:
                        successful_match = False

                for key, value in call[1].items():
                    if key == "allow_redirects":
                        continue
                    if value and key not in kwargs:
                        successful_match = False

                if successful_match:
                    return True

        return False

    return verify_call


@pytest.fixture(name="unifi_controller")
async def unifi_controller_fixture(is_unifi_os: bool) -> Controller:
    """Provide a test-ready UniFi controller."""
    session = aiohttp.ClientSession()
    config = Configuration(session, "host", username="user", password="pass")
    controller = Controller(config)
    controller.connectivity.is_unifi_os = is_unifi_os
    controller.ws_state_callback = Mock()
    yield controller
    await session.close()


@pytest.fixture(name="_new_ws_data_fn")
async def mock_wsclient(
    unifi_controller: Controller,
) -> Callable[[dict[str, Any]], None]:
    """No real websocket allowed."""
    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

        def new_ws_data_fn(data: dict[str, Any]) -> None:
            """Add and signal new websocket data."""
            assert unifi_controller.websocket
            unifi_controller.websocket._data = data  # pylint: disable=protected-access
            unifi_controller.session_handler(WebsocketSignal.DATA)

        return new_ws_data_fn


@pytest.fixture(name="_mock_endpoints")
def endpoint_fixture(
    mock_aioresponse: aioresponses,
    is_unifi_os: bool,
    client_payload: list[dict[str, Any]],
    clients_all_payload: list[dict[str, Any]],
    device_payload: list[dict[str, Any]],
    dpi_app_payload: list[dict[str, Any]],
    dpi_group_payload: list[dict[str, Any]],
    port_forward_payload: list[dict[str, Any]],
    site_payload: list[dict[str, Any]],
    system_information_payload: list[dict[str, Any]],
    wlan_payload: list[dict[str, Any]],
) -> None:
    """Use fixtures to mock all endpoints."""

    def mock_get_request(
        path: str, unifi_path: str, payload: list[dict[str, Any]]
    ) -> None:
        """Register HTTP response mock."""
        url = unifi_path if is_unifi_os else path
        data = {"meta": {"rc": "OK"}, "data": payload}
        mock_aioresponse.get(f"https://host:8443{url}", payload=data)

    mock_get_request(
        "/api/s/default/stat/sta",
        "/proxy/network/api/s/default/stat/sta",
        client_payload,
    )
    mock_get_request(
        "/api/s/default/rest/user",
        "/proxy/network/api/s/default/rest/user",
        clients_all_payload,
    )
    mock_get_request(
        "/api/s/default/stat/device",
        "/proxy/network/api/s/default/stat/device",
        device_payload,
    )
    mock_get_request(
        "/api/s/default/rest/dpiapp",
        "/proxy/network/api/s/default/rest/dpiapp",
        dpi_app_payload,
    )
    mock_get_request(
        "/api/s/default/rest/dpigroup",
        "/proxy/network/api/s/default/rest/dpigroup",
        dpi_group_payload,
    )
    mock_get_request(
        "/api/s/default/rest/portforward",
        "/proxy/network/api/s/default/rest/portforward",
        port_forward_payload,
    )
    mock_get_request(
        "/api/self/sites",
        "/proxy/network/api/self/sites",
        site_payload,
    )
    mock_get_request(
        "/api/s/default/stat/sysinfo",
        "/proxy/network/api/s/default/stat/sysinfo",
        system_information_payload,
    )
    mock_get_request(
        "/api/s/default/rest/wlanconf",
        "/proxy/network/api/s/default/rest/wlanconf",
        wlan_payload,
    )


@pytest.fixture(name="response_payload")
def response_data_fixture() -> dict[str, Any]:
    """Response data."""
    return {"meta": {"rc": "ok"}, "data": []}


@pytest.fixture(name="client_payload")
def client_data_fixture() -> list[dict[str, Any]]:
    """Client data."""
    return []


@pytest.fixture(name="clients_all_payload")
def clients_all_data_fixture() -> list[dict[str, Any]]:
    """Clients all data."""
    return []


@pytest.fixture(name="device_payload")
def device_data_fixture() -> list[dict[str, Any]]:
    """Device data."""
    return []


@pytest.fixture(name="dpi_app_payload")
def dpi_app_data_fixture() -> list[dict[str, Any]]:
    """DPI app data."""
    return []


@pytest.fixture(name="dpi_group_payload")
def dpi_group_data_fixture() -> list[dict[str, Any]]:
    """DPI group data."""
    return []


@pytest.fixture(name="port_forward_payload")
def port_forward_data_fixture() -> list[dict[str, Any]]:
    """Port forward data."""
    return []


@pytest.fixture(name="site_payload")
def site_data_fixture() -> list[dict[str, Any]]:
    """Site data."""
    return []


@pytest.fixture(name="system_information_payload")
def system_information_data_fixture() -> list[dict[str, Any]]:
    """System information data."""
    return []


@pytest.fixture(name="wlan_payload")
def wlan_data_fixture() -> list[dict[str, Any]]:
    """WLAN data."""
    return []
