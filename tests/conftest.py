"""Setup common test helpers."""

from unittest.mock import Mock, patch

import aiohttp
from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller


@pytest.fixture(name="mock_aioresponse")
def aioresponse_fixture():
    """AIOHTTP fixture."""
    with aioresponses() as m:
        yield m


@pytest.fixture(name="is_unifi_os")
def is_unifi_os_fixture() -> bool:
    """If use UniFi OS response."""
    return False


@pytest.fixture
def unifi_called_with(mock_aioresponse):
    """Verify UniFi call was made with the expected parameters."""

    def verify_call(method: str, path: str, **kwargs: dict) -> bool:
        """Verify expected data was provided with a request to aioresponse."""
        for req, call_list in mock_aioresponse.requests.items():
            if method != req[0]:
                continue

            if not req[1].path.endswith(path):
                continue

            for call in call_list:
                successful_match = True

                for key in kwargs:
                    if key not in call[1] or call[1][key] != kwargs[key]:
                        successful_match = False

                for key, value in call[1].items():
                    if key == "allow_redirects":
                        continue
                    if value and key not in kwargs:
                        successful_match = False

                if successful_match:
                    return True

        return False

    yield verify_call


@pytest.fixture(name="unifi_controller")
async def unifi_controller_fixture(is_unifi_os: bool) -> Controller:
    """Provide a test-ready UniFi controller."""
    session = aiohttp.ClientSession()
    controller = Controller("host", session, username="user", password="pass")
    controller.is_unifi_os = is_unifi_os
    controller.ws_state_callback = Mock()
    yield controller
    await session.close()


@pytest.fixture()
def mock_wsclient():
    """No real websocket allowed."""
    with patch("aiounifi.controller.WSClient") as mock:
        yield mock
