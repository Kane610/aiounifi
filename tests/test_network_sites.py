"""Test Network API site information endpoint."""

import re

import aiohttp
import pytest
from yarl import URL

from aiounifi import NetworkClient
from aiounifi.errors import ResponseError, Unauthorized
from aiounifi.models.configuration import Configuration


@pytest.fixture(name="network_client")
async def network_client_fixture() -> NetworkClient:
    """Build network client for tests."""
    session = aiohttp.ClientSession()
    config = Configuration(
        session,
        "host",
        username="user",
        password="pass",
        network_api_key="secret-key",
    )
    client = NetworkClient(config)
    yield client
    await session.close()


async def test_network_sites_list_success(mock_aioresponse, network_client) -> None:
    """Verify network sites list returns parsed site models."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={
            "offset": 0,
            "limit": 2,
            "count": 2,
            "totalCount": 4,
            "data": [
                {
                    "id": "site-a",
                    "internalReference": "ref-a",
                    "name": "Alpha",
                },
                {
                    "id": "site-b",
                    "internalReference": "ref-b",
                    "name": "Beta",
                },
            ],
        },
    )

    sites = await network_client.sites.list_page(offset=0, limit=2)

    assert len(sites) == 2
    assert sites[0].site_id == "site-a"
    assert sites[0].internal_reference == "ref-a"
    assert sites[0].name == "Alpha"

    request = next(iter(mock_aioresponse.requests))
    assert request[0] == "get"
    assert isinstance(request[1], URL)
    assert request[1].path == "/v1/sites"


async def test_network_sites_list_filter(mock_aioresponse, network_client) -> None:
    """Verify filter parameter is accepted for one page request."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={
            "offset": 10,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [{"id": "site-z", "internalReference": "ref-z", "name": "Zulu"}],
        },
    )

    sites = await network_client.sites.list_page(
        offset=10, limit=1, filter_value="name=='Zulu'"
    )

    assert len(sites) == 1
    assert sites[0].name == "Zulu"


async def test_network_sites_unauthorized(mock_aioresponse, network_client) -> None:
    """Verify unauthorized response is mapped to Unauthorized."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        status=401,
    )

    with pytest.raises(Unauthorized):
        await network_client.sites.list()


async def test_network_sites_missing_data(mock_aioresponse, network_client) -> None:
    """Verify missing data envelope is rejected."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={"offset": 0, "limit": 1},
    )

    with pytest.raises(ResponseError):
        await network_client.sites.list()


async def test_network_sites_list_uses_default_page(
    mock_aioresponse, network_client
) -> None:
    """Verify list delegates to the default first page call."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "id": "site-default",
                    "internalReference": "ref-default",
                    "name": "Default",
                }
            ],
        },
    )

    sites = await network_client.sites.list()

    assert len(sites) == 1
    assert sites[0].name == "Default"
