"""Setup common test helpers."""

from unittest.mock import Mock

import aiohttp
from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


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
                    if value and key not in kwargs:
                        successful_match = False

                if successful_match:
                    return True

        return False

    yield verify_call


@pytest.fixture
async def unifi_controller() -> Controller:
    """Return UniFi controller.

    Clean up sessions automatically at the end of each test.
    """
    session = aiohttp.ClientSession()
    controller = Controller(
        "host", session, username="user", password="pass", callback=Mock()
    )
    yield controller
    await session.close()
