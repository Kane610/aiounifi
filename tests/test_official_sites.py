"""Test official API site information endpoint."""

import re

import aiohttp
import pytest
from yarl import URL

from aiounifi import OfficialClient
from aiounifi.errors import ResponseError, Unauthorized
from aiounifi.models.configuration import Configuration


@pytest.fixture(name="official_client")
async def official_client_fixture() -> OfficialClient:
    """Build official client for tests."""
    session = aiohttp.ClientSession()
    config = Configuration(
        session,
        "host",
        username="user",
        password="pass",
        official_api_key="secret-key",
    )
    client = OfficialClient(config)
    yield client
    await session.close()


async def test_official_sites_list_success(mock_aioresponse, official_client) -> None:
    """Verify official sites list returns page metadata and parsed sites."""
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

    page = await official_client.sites.list(offset=0, limit=2)

    assert page.offset == 0
    assert page.limit == 2
    assert page.count == 2
    assert page.total_count == 4
    assert len(page.sites) == 2
    assert page.sites[0].site_id == "site-a"
    assert page.sites[0].internal_reference == "ref-a"
    assert page.sites[0].name == "Alpha"

    request = next(iter(mock_aioresponse.requests))
    assert request[0] == "get"
    assert isinstance(request[1], URL)
    assert request[1].path == "/v1/sites"


async def test_official_sites_list_filter(mock_aioresponse, official_client) -> None:
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

    page = await official_client.sites.list(
        offset=10, limit=1, filter_value="name=='Zulu'"
    )

    assert page.offset == 10
    assert page.sites[0].name == "Zulu"


async def test_official_sites_unauthorized(mock_aioresponse, official_client) -> None:
    """Verify unauthorized response is mapped to Unauthorized."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        status=401,
    )

    with pytest.raises(Unauthorized):
        await official_client.sites.list()


async def test_official_sites_missing_data(mock_aioresponse, official_client) -> None:
    """Verify missing data envelope is rejected."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={"offset": 0, "limit": 1},
    )

    with pytest.raises(ResponseError):
        await official_client.sites.list()
