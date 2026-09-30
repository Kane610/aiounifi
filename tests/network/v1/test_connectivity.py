"""Test the transport of the Network API v1."""

import logging

import aiohttp
import pytest

from aiounifi.errors import (
    AuthenticationRateLimitError,
    BadGateway,
    EndpointNotFound,
    Forbidden,
    NetworkApiError,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    Unauthorized,
)
from aiounifi.models.configuration import Configuration
from aiounifi.network.v1.api_client import ApiClient
from aiounifi.network.v1.connectivity import Connectivity
from aiounifi.network.v1.errors import V1NotFound, V1Unauthorized
from aiounifi.network.v1.models.api import ApiRequest

from .conftest import BASE_URL, requests_to, url_pattern

INFO = ApiRequest(method="get", path="/v1/info")


def structured_error(status: int, name: str, code: str) -> dict[str, str | int]:
    """Build the console's error envelope."""
    return {
        "statusCode": status,
        "statusName": name,
        "code": code,
        "message": "Something went wrong",
        "timestamp": "2026-09-24T20:07:45.754603972Z",
        "requestPath": "/integration/v1/info",
        "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }


async def test_sends_api_key_header_and_no_cookies_or_login(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """The key travels as X-API-KEY and nothing else is needed."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/info", payload={"applicationVersion": "10.6.106"}
    )

    info = await network_client.get_info()

    assert info["applicationVersion"] == "10.6.106"
    (call,) = requests_to(mock_aioresponse, "get", "/v1/info")
    headers = call.kwargs["headers"]
    assert headers["X-API-KEY"] == "secret-key"
    assert headers["Accept"] == "application/json"
    assert "Content-Type" not in headers
    assert call.kwargs["data"] is None


@pytest.mark.parametrize("api_key", [None, "", "   "])
async def test_missing_api_key_fails_before_any_request(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """No key, no request."""
    with pytest.raises(RequestError, match="api_key is required"):
        await network_client.get_info()
    assert not mock_aioresponse.requests


async def test_key_is_stripped(config: Configuration, mock_aioresponse) -> None:
    """Whitespace around a pasted key is forgiven."""
    config.api_key = "  secret-key \n"
    mock_aioresponse.get(f"{BASE_URL}/v1/info", payload={"applicationVersion": "1"})

    await ApiClient(config).get_info()

    (call,) = requests_to(mock_aioresponse, "get", "/v1/info")
    assert call.kwargs["headers"]["X-API-KEY"] == "secret-key"


async def test_post_sends_json_body(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """A request with data is sent as JSON."""
    mock_aioresponse.post(f"{BASE_URL}/v1/info", body=b"")

    response = await network_client.request(
        ApiRequest(method="post", path="/v1/info", data={"action": "RESTART"})
    )

    assert response == {"data": []}
    (call,) = requests_to(mock_aioresponse, "post", "/v1/info")
    assert call.kwargs["data"] == b'{"action":"RESTART"}'
    assert call.kwargs["headers"]["Content-Type"] == "application/json"


async def test_rejected_key_uses_the_unstructured_401(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """A bad key gets a body that is not the error envelope; the status decides."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/info",
        status=401,
        payload={"error": {"code": 401, "message": "Unauthorized"}},
    )

    with pytest.raises(Unauthorized) as err:
        await network_client.get_info()

    assert isinstance(err.value, V1Unauthorized)
    assert isinstance(err.value, NetworkApiError)
    assert err.value.status_code == 401
    assert err.value.code == ""


async def test_structured_error_fields_are_carried(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """The envelope ends up on the exception."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/info",
        status=404,
        payload=structured_error(404, "NOT_FOUND", "api.resource-not-found"),
    )

    with pytest.raises(EndpointNotFound, match="api.resource-not-found") as err:
        await network_client.get_info()

    assert isinstance(err.value, V1NotFound)
    assert err.value.status_code == 404
    assert err.value.status_name == "NOT_FOUND"
    assert err.value.code == "api.resource-not-found"
    assert err.value.detail == "Something went wrong"
    assert err.value.timestamp == "2026-09-24T20:07:45.754603972Z"
    assert err.value.request_path == "/integration/v1/info"
    assert err.value.request_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"


@pytest.mark.parametrize(
    ("status", "payload", "expected"),
    [
        (
            400,
            structured_error(
                400, "UNAUTHORIZED", "api.authentication.missing-credentials"
            ),
            Unauthorized,
        ),
        (
            400,
            structured_error(
                400, "UNAUTHORIZED", "api.authentication.invalid-credentials"
            ),
            Unauthorized,
        ),
        (
            429,
            structured_error(
                429, "TOO_MANY_REQUESTS", "api.authentication.failed-limit-reached"
            ),
            AuthenticationRateLimitError,
        ),
        (400, structured_error(400, "FORBIDDEN", "api.something.else"), Forbidden),
        (400, structured_error(400, "BAD_GATEWAY", "api.something.else"), BadGateway),
        (
            400,
            structured_error(400, "SERVICE_UNAVAILABLE", "api.something.else"),
            ServiceUnavailable,
        ),
        (
            400,
            structured_error(400, "BAD_REQUEST", "api.request.unknown-type-id"),
            ResponseError,
        ),
        (403, None, Forbidden),
        (404, None, EndpointNotFound),
        (502, None, BadGateway),
        (503, None, ServiceUnavailable),
        (499, None, ResponseError),
        (500, {"unrelated": True}, ResponseError),
    ],
)
async def test_error_resolution_order(
    mock_aioresponse,
    network_client: ApiClient,
    status: int,
    payload: dict[str, object] | None,
    expected: type[Exception],
) -> None:
    """Code beats status name beats HTTP status beats the fallback."""
    if payload is None:
        mock_aioresponse.get(f"{BASE_URL}/v1/info", status=status, body=b"nope")
    else:
        mock_aioresponse.get(f"{BASE_URL}/v1/info", status=status, payload=payload)

    with pytest.raises(expected):
        await network_client.get_info()


async def test_transport_error_becomes_request_error(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """A connection failure is a RequestError, like the legacy API."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/info", exception=aiohttp.ClientConnectionError("boom")
    )

    with pytest.raises(RequestError, match="Error requesting data"):
        await network_client.get_info()


async def test_non_json_success_body(
    mock_aioresponse, network_client: ApiClient, caplog: pytest.LogCaptureFixture
) -> None:
    """A login page in place of JSON is a ResponseError."""
    mock_aioresponse.get(f"{BASE_URL}/v1/info", body=b"<html>login</html>")

    with (
        caplog.at_level(logging.DEBUG, logger="aiounifi.network.v1.connectivity"),
        pytest.raises(ResponseError, match="non-JSON"),
    ):
        await network_client.get_info()

    assert "<html>login</html>" in caplog.text


async def test_non_object_json_is_rejected(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """A bare list is not a shape the API uses."""
    mock_aioresponse.get(f"{BASE_URL}/v1/info", payload=[1, 2, 3])

    with pytest.raises(ResponseError, match="Unexpected"):
        await network_client.get_info()


def test_base_url(config: Configuration) -> None:
    """The Integration API sits behind the UniFi OS proxy."""
    assert Connectivity(config).base_url == BASE_URL


def test_request_path_must_be_versioned() -> None:
    """Paths outside /v1/ are refused at construction."""
    with pytest.raises(ValueError, match="/v1/"):
        ApiRequest(method="get", path="/api/s/default/stat/sta")


def test_url_pattern_helper() -> None:
    """The test helper matches with and without a query string."""
    assert url_pattern("/v1/sites").match(f"{BASE_URL}/v1/sites")
    assert url_pattern("/v1/sites").match(f"{BASE_URL}/v1/sites?offset=0")
    assert not url_pattern("/v1/sites").match(f"{BASE_URL}/v1/sites/abc")
