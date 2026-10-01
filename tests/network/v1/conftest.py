"""Fixtures for the Network API v1 tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import re
from typing import Any

import aiohttp
import pytest

from aiounifi.controller import Controller
from aiounifi.models.configuration import Configuration
from aiounifi.network.v1.api_client import ApiClient

BASE_URL = "https://host:8443/proxy/network/integration"
SITE_ID = "88f7af54-98f8-306a-a1c7-c9349722b1f6"


def url_pattern(path: str) -> re.Pattern[str]:
    """Match a v1 path with any query string."""
    return re.compile(rf"^{re.escape(BASE_URL)}{re.escape(path)}(?:\?.*)?$")


def requests_to(mock_aioresponse: Any, method: str, path: str) -> list[Any]:
    """Return the recorded calls to one endpoint, whatever their query string."""
    calls: list[Any] = []
    for (request_method, url), request_calls in mock_aioresponse.requests.items():
        if request_method == method.lower() and url.path.endswith(path):
            calls.extend(request_calls)
    return calls


def envelope(items: list[dict[str, Any]], **overrides: int) -> dict[str, Any]:
    """Build a list envelope the way the console does."""
    payload: dict[str, Any] = {
        "offset": 0,
        "limit": 25,
        "count": len(items),
        "totalCount": len(items),
        "data": items,
    }
    payload.update(overrides)
    return payload


@pytest.fixture(name="api_key")
def api_key_fixture() -> str | None:
    """Return the API key handed to the configuration."""
    return "secret-key"


@pytest.fixture(name="config")
async def config_fixture(api_key: str | None) -> AsyncGenerator[Configuration]:
    """Return a configuration with an API key and no legacy credentials."""
    session = aiohttp.ClientSession()
    yield Configuration(session, "host", api_key=api_key)
    await session.close()


@pytest.fixture(name="network_client")
def network_client_fixture(config: Configuration) -> ApiClient:
    """Return a v1 client without a site assigned."""
    return ApiClient(config)


@pytest.fixture(name="network_client_with_site")
async def network_client_with_site_fixture(
    mock_aioresponse, network_client: ApiClient
) -> ApiClient:
    """Return a v1 client with the default site assigned."""
    mock_aioresponse.get(
        url_pattern("/v1/sites"),
        payload=envelope(
            [{"id": SITE_ID, "internalReference": "default", "name": "Default"}]
        ),
    )
    await network_client.assign_site("default")
    return network_client


@pytest.fixture(name="controller")
def controller_fixture(config: Configuration) -> Controller:
    """Return a legacy controller sharing the configuration."""
    return Controller(config)
