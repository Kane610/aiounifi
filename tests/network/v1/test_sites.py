"""Tests for Integration API sites and application info."""

from __future__ import annotations

import re
from typing import Any

from aioresponses import aioresponses
import pytest

from aiounifi.network.v1.api_client import ApiClient
from aiounifi.network.v1.models.site import Site, SiteData, SitesRequest

from .helpers import request_kwargs

SITES_URL = "https://host:8443/proxy/network/integration/v1/sites"
INFO_URL = "https://host:8443/proxy/network/integration/v1/info"

SITE_DATA: SiteData = {
    "id": "8a1b2c3d-4e5f-6789-abcd-ef0123456789",
    "internalReference": "default",
    "name": "Default",
}

SITES_PAYLOAD: dict[str, Any] = {
    "offset": 0,
    "limit": 25,
    "count": 1,
    "totalCount": 1,
    "data": [SITE_DATA],
}


async def test_list_sites(
    mock_aioresponse: aioresponses,
    network_client: ApiClient,
    api_key: str,
) -> None:
    """Verify listing sites uses the official Integration API and API key."""
    mock_aioresponse.get(
        re.compile(rf"{re.escape(SITES_URL)}.*"), payload=SITES_PAYLOAD
    )

    sites = await network_client.sites.list()

    assert len(sites) == 1
    site = sites[0]
    assert site.site_id == SITE_DATA["id"]
    assert site.internal_reference == "default"
    assert site.name == "Default"

    headers = request_kwargs(mock_aioresponse, "GET", "/v1/sites")["headers"]
    assert headers["X-API-KEY"] == api_key
    params = request_kwargs(mock_aioresponse, "GET", "/v1/sites")["params"]
    assert params == {"offset": 0, "limit": 25}


async def test_list_sites_with_filter(
    mock_aioresponse: aioresponses,
    network_client: ApiClient,
) -> None:
    """Verify optional site filters are passed as query params."""
    mock_aioresponse.get(
        re.compile(rf"{re.escape(SITES_URL)}.*"), payload=SITES_PAYLOAD
    )

    await network_client.sites.list_page(
        offset=25, limit=50, filter_value="name.eq('HQ')"
    )

    params = request_kwargs(mock_aioresponse, "GET", "/v1/sites")["params"]
    assert params == {"offset": 25, "limit": 50, "filter": "name.eq('HQ')"}


async def test_get_info(
    mock_aioresponse: aioresponses,
    network_client: ApiClient,
    api_key: str,
) -> None:
    """Verify application info is fetched from GET /v1/info."""
    mock_aioresponse.get(INFO_URL, payload={"applicationVersion": "9.1.0"})

    info = await network_client.get_info()

    assert info.application_version == "9.1.0"
    headers = request_kwargs(mock_aioresponse, "GET", "/v1/info")["headers"]
    assert headers["X-API-KEY"] == api_key


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("default", SITE_DATA["id"]),
        ("Default", SITE_DATA["id"]),
        (SITE_DATA["id"], SITE_DATA["id"]),
        ("missing", None),
    ],
)
def test_resolve_site_uuid(
    token: str, expected: str | None, network_client: ApiClient
) -> None:
    """Verify site UUID resolution from internal reference, name, or id."""
    sites = [Site(SITE_DATA)]
    assert network_client.sites.resolve_site_uuid(token, sites) == expected


def test_sites_request_path() -> None:
    """Verify sites request targets /v1/sites."""
    request = SitesRequest.create()
    assert request.method == "get"
    assert request.path == "/v1/sites"
    assert request.params == {"offset": 0, "limit": 25}


async def test_list_sites_empty_page(
    mock_aioresponse: aioresponses,
    network_client: ApiClient,
) -> None:
    """Verify an empty Integration API page returns no sites."""
    mock_aioresponse.get(
        re.compile(rf"{re.escape(SITES_URL)}.*"),
        payload={"offset": 0, "limit": 25, "count": 0, "totalCount": 0, "data": []},
    )

    assert await network_client.sites.list() == []
