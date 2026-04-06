"""Test Network API site information endpoint."""

from collections.abc import AsyncGenerator
import re

import aiohttp
import pytest
from yarl import URL

from aiounifi import NetworkClient
from aiounifi.errors import ResponseError, Unauthorized
from aiounifi.models.configuration import Configuration


@pytest.fixture(name="network_client")
async def network_client_fixture() -> AsyncGenerator[NetworkClient]:
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


async def test_network_sites_structured_unauthorized_message(
    mock_aioresponse, network_client
) -> None:
    """Verify structured API error fields are included in raised messages."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        status=401,
        payload={
            "statusCode": 401,
            "statusName": "UNAUTHORIZED",
            "code": "api.authentication.missing-credentials",
            "message": "Missing credentials",
            "timestamp": "2024-11-27T08:13:46.966Z",
            "requestPath": "/integration/v1/sites/123",
            "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )

    with pytest.raises(
        Unauthorized, match="api.authentication.missing-credentials"
    ) as err:
        await network_client.sites.list()

    assert getattr(err.value, "status_code") == 401
    assert getattr(err.value, "status_name") == "UNAUTHORIZED"
    assert getattr(err.value, "code") == "api.authentication.missing-credentials"
    assert getattr(err.value, "detail") == "Missing credentials"
    assert getattr(err.value, "request_path") == "/integration/v1/sites/123"
    assert getattr(err.value, "request_id") == "3fa85f64-5717-4562-b3fc-2c963f66afa6"


async def test_network_sites_semantic_error_overrides_http_status(
    mock_aioresponse, network_client
) -> None:
    """Verify structured error semantics can select a more specific exception."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        status=400,
        payload={
            "statusCode": 400,
            "statusName": "UNAUTHORIZED",
            "code": "api.authentication.missing-credentials",
            "message": "Missing credentials",
            "timestamp": "2024-11-27T08:13:46.966Z",
            "requestPath": "/integration/v1/sites/123",
            "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )

    with pytest.raises(Unauthorized):
        await network_client.sites.list()


async def test_network_sites_unknown_error_status(
    mock_aioresponse, network_client
) -> None:
    """Verify non-standard HTTP statuses still raise a normal aiounifi error."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        status=499,
    )

    with pytest.raises(ResponseError, match="received 499"):
        await network_client.sites.list()


async def test_network_sites_missing_data(mock_aioresponse, network_client) -> None:
    """Verify missing response envelope fields are rejected."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={"offset": 0, "limit": 1, "count": 1, "totalCount": 1},
    )

    with pytest.raises(ResponseError):
        await network_client.sites.list()


async def test_network_sites_missing_required_metadata(
    mock_aioresponse, network_client
) -> None:
    """Verify missing required metadata fields are rejected."""
    mock_aioresponse.get(
        re.compile(r"^https://api\.ui\.com/v1/sites(?:\?.*)?$"),
        payload={
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "id": "site-a",
                    "internalReference": "ref-a",
                    "name": "Alpha",
                }
            ],
        },
    )

    with pytest.raises(ResponseError, match="offset"):
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
