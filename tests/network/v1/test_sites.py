"""Test Network API site information endpoint."""

import re

import pytest

from aiounifi.errors import RequestError, ResponseError, Unauthorized
from aiounifi.network.v1.models.api import ApiRequest
from aiounifi.network.v1.models.site import Site

from .helpers import assert_request_called_with


async def test_network_sites_list_success(mock_aioresponse, network_client) -> None:
    """Verify network sites list returns parsed site models."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
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
    assert_request_called_with(
        mock_aioresponse,
        "get",
        "/proxy/network/integration/v1/sites",
        params={"offset": 0, "limit": 2},
    )


async def test_network_sites_list_filter(mock_aioresponse, network_client) -> None:
    """Verify filter parameter is accepted for one page request."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
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
    assert_request_called_with(
        mock_aioresponse,
        "get",
        "/proxy/network/integration/v1/sites",
        params={"offset": 10, "limit": 1, "filter": "name=='Zulu'"},
    )


async def test_network_sites_unauthorized(mock_aioresponse, network_client) -> None:
    """Verify unauthorized response is mapped to Unauthorized."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
        status=401,
    )

    with pytest.raises(Unauthorized):
        await network_client.sites.list()


async def test_network_sites_structured_unauthorized_message(
    mock_aioresponse, network_client
) -> None:
    """Verify structured API error fields are included in raised messages."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
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
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
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
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
        status=499,
    )

    with pytest.raises(ResponseError, match="received 499"):
        await network_client.sites.list()


async def test_network_sites_missing_data(mock_aioresponse, network_client) -> None:
    """Verify missing response envelope fields are rejected."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
        payload={"offset": 0, "limit": 1, "count": 1, "totalCount": 1},
    )

    with pytest.raises(ResponseError):
        await network_client.sites.list()


async def test_network_sites_missing_required_metadata(
    mock_aioresponse, network_client
) -> None:
    """Verify missing required metadata fields are rejected."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
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
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
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
    assert_request_called_with(
        mock_aioresponse,
        "get",
        "/proxy/network/integration/v1/sites",
        params={"offset": 0, "limit": 25},
    )


def test_network_sites_resolve_site_uuid_returns_none_without_sites(
    network_client,
) -> None:
    """Verify site UUID resolution returns None when no site list is provided."""
    assert network_client.sites.resolve_site_uuid("default") is None


def test_network_sites_resolve_site_uuid_prefers_internal_reference(
    network_client,
) -> None:
    """Verify site UUID resolution prefers internal_reference over name."""
    sites = [
        Site({"id": "site-a", "internalReference": "default", "name": "Alpha"}),
        Site({"id": "site-b", "internalReference": "other", "name": "default"}),
    ]

    assert network_client.sites.resolve_site_uuid("default", sites) == "site-a"


def test_network_sites_resolve_site_uuid_matches_name_and_id(
    network_client,
) -> None:
    """Verify site UUID resolution falls back to matching by name and site ID."""
    sites = [
        Site({"id": "site-a", "internalReference": "ref-a", "name": "Alpha"}),
        Site({"id": "site-b", "internalReference": "ref-b", "name": "Beta"}),
    ]

    assert network_client.sites.resolve_site_uuid("Beta", sites) == "site-b"
    assert network_client.sites.resolve_site_uuid("site-a", sites) == "site-a"
    assert network_client.sites.resolve_site_uuid("missing", sites) is None


def test_network_api_request_decode_rejects_non_object() -> None:
    """Verify network API decode rejects JSON payloads that are not objects."""
    request = ApiRequest(method="get", path="/v1/sites")

    with pytest.raises(ResponseError, match="not an object"):
        request.decode(b"[]")


async def test_network_assign_site_prefers_primary_resolver(network_client) -> None:
    """Verify assign_site uses primary resolver before v1 fallback."""

    class PrimarySitesStub:
        """Primary site resolver stub."""

        def resolve_site_uuid(self, site: str) -> str | None:
            return "legacy-uuid" if site == "default" else None

    class ControllerStub:
        """Controller stub exposing legacy sites resolver."""

        def __init__(self, existing_controller) -> None:
            self.sites = PrimarySitesStub()
            self.connectivity = existing_controller.connectivity

    network_client.controller = ControllerStub(network_client.controller)

    resolved = await network_client.assign_site("default")

    assert resolved == "legacy-uuid"
    assert network_client.site_id == "legacy-uuid"


async def test_network_assign_site_prefers_configured_site_uuid(
    network_client,
) -> None:
    """Verify configured site_uuid is preferred over resolver paths."""
    network_client.controller.connectivity.config.site_uuid = "configured-uuid"

    resolved = await network_client.assign_site("default")

    assert resolved == "configured-uuid"
    assert network_client.site_id == "configured-uuid"


async def test_network_assign_site_whitespace_configured_uuid_is_used_as_is(
    network_client,
) -> None:
    """Verify configured site_uuid is used as-is without trimming."""
    network_client.controller.connectivity.config.site_uuid = "   "

    resolved = await network_client.assign_site("default")

    assert resolved == "   "
    assert network_client.site_id == "   "


async def test_network_assign_site_uses_cached_v1_sites(network_client) -> None:
    """Verify assign_site resolves from v1 cached sites before doing API calls."""
    network_client.sites.process_item(
        {
            "id": "site-cached",
            "internalReference": "default",
            "name": "Default",
        }
    )

    resolved = await network_client.assign_site("default")

    assert resolved == "site-cached"
    assert network_client.site_id == "site-cached"


async def test_network_assign_site_fetches_v1_sites_when_needed(
    mock_aioresponse, network_client
) -> None:
    """Verify assign_site fetches v1 sites when resolver caches are empty."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "id": "site-fetched",
                    "internalReference": "default",
                    "name": "Default",
                }
            ],
        },
    )

    resolved = await network_client.assign_site("default")

    assert resolved == "site-fetched"
    assert network_client.site_id == "site-fetched"


async def test_network_assign_site_raises_when_unresolved(
    mock_aioresponse, network_client
) -> None:
    """Verify assign_site raises RequestError when UUID cannot be resolved."""
    mock_aioresponse.get(
        re.compile(r"^https://host:8443/proxy/network/integration/v1/sites(?:\?.*)?$"),
        payload={
            "offset": 0,
            "limit": 25,
            "count": 1,
            "totalCount": 1,
            "data": [],
        },
    )

    with pytest.raises(RequestError, match="Could not resolve Network API site UUID"):
        await network_client.assign_site("missing-site")
