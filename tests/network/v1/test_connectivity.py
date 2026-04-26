"""Unit tests for Network API connectivity helpers."""

from dataclasses import dataclass
import logging
from typing import Any

import aiohttp
import pytest

from aiounifi.errors import RequestError, ResponseError, Unauthorized
from aiounifi.network.v1.connectivity import Connectivity
from aiounifi.network.v1.errors import (
    V1Forbidden,
    V1ResponseError,
    V1Unauthorized,
)
from aiounifi.network.v1.models.api import ApiRequest


@dataclass
class _V1RequestStub:
    """Request-like stub validating v1 connectivity duck-typing behavior."""

    method: str = "get"
    path: str = "/v1/sites"
    params: dict[str, str | int] | None = None
    data: dict[str, Any] | None = None

    def decode(self, raw: bytes) -> dict[str, Any]:
        """Return a valid v1 envelope for compatibility checks."""
        return {
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [{"_id": "site-1"}],
        }


async def test_network_request_requires_api_key(network_config) -> None:
    """Verify requests fail fast when no API key is configured."""
    network_config.api_key = None
    connectivity = Connectivity(network_config)

    with pytest.raises(RequestError, match="api_key is required"):
        await connectivity.request(ApiRequest(method="get", path="/v1/sites"))


async def test_network_request_accepts_request_like_object(
    mock_aioresponse,
    network_connectivity: Connectivity,
) -> None:
    """Verify v1 connectivity works with structural request objects."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/integration/v1/sites",
        payload={
            "offset": 0,
            "limit": 1,
            "count": 1,
            "totalCount": 1,
            "data": [{"_id": "site-1"}],
        },
    )

    response = await network_connectivity.request(_V1RequestStub())

    assert response["data"][0]["_id"] == "site-1"


async def test_network_request_rejects_blank_api_key(network_config) -> None:
    """Verify requests fail fast when the API key is blank after stripping."""
    network_config.api_key = "   "
    connectivity = Connectivity(network_config)

    with pytest.raises(RequestError, match="api_key must not be blank"):
        await connectivity.request(ApiRequest(method="get", path="/v1/sites"))


async def test_network_request_raises_structured_exception(
    mock_aioresponse,
    network_connectivity: Connectivity,
) -> None:
    """Verify failed responses are mapped through structured API errors."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/integration/v1/sites",
        status=401,
        body=(
            b'{"statusCode":401,"statusName":"UNAUTHORIZED",'
            b'"code":"api.authentication.missing-credentials",'
            b'"message":"Missing credentials",'
            b'"timestamp":"2024-11-27T08:13:46.966Z",'
            b'"requestPath":"/integration/v1/sites",'
            b'"requestId":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
        ),
    )

    with pytest.raises(Unauthorized, match="Missing credentials"):
        await network_connectivity.request(ApiRequest(method="get", path="/v1/sites"))


async def test_network_request_logs_non_json_success_response(
    mock_aioresponse,
    caplog: pytest.LogCaptureFixture,
    network_connectivity: Connectivity,
) -> None:
    """Verify non-JSON success bodies are logged and wrapped consistently."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/integration/v1/sites",
        status=200,
        body=b"<html>ok</html>",
    )

    with (
        caplog.at_level(logging.DEBUG, logger="aiounifi.network.v1.connectivity"),
        pytest.raises(ResponseError, match="returned a non-JSON response"),
    ):
        await network_connectivity.request(ApiRequest(method="get", path="/v1/sites"))

    assert "non-JSON response body" in caplog.text


async def test_network_request_wraps_client_errors(
    mock_aioresponse,
    network_connectivity: Connectivity,
) -> None:
    """Verify transport client errors are wrapped as RequestError."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/integration/v1/sites",
        exception=aiohttp.ClientConnectionError("boom"),
    )

    with pytest.raises(RequestError, match="Error requesting data"):
        await network_connectivity.request(ApiRequest(method="get", path="/v1/sites"))


def test_network_build_url(network_connectivity: Connectivity) -> None:
    """Verify URL builder prefixes /proxy/network/integration unconditionally."""
    assert (
        network_connectivity._build_url("/v1/sites")
        == "https://host:8443/proxy/network/integration/v1/sites"
    )
    assert (
        network_connectivity._build_url("/v1/sites/abc/clients")
        == "https://host:8443/proxy/network/integration/v1/sites/abc/clients"
    )


def test_api_request_rejects_non_v1_path() -> None:
    """Verify ApiRequest raises ValueError when path does not start with /v1/."""
    with pytest.raises(ValueError, match="/v1/"):
        ApiRequest(method="get", path="/integration/v1/sites")

    with pytest.raises(ValueError, match="/v1/"):
        ApiRequest(method="get", path="v1/sites")


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (b"not-json", None),
        (b"[]", None),
        (
            b'{"statusCode":401,"statusName":"UNAUTHORIZED"}',
            None,
        ),
    ],
)
def test_network_parse_error_response_invalid_payloads(
    network_connectivity: Connectivity,
    body: bytes,
    expected: None,
) -> None:
    """Verify malformed structured error payloads are ignored."""
    assert network_connectivity._parse_error_response(body) is expected


def test_network_build_exception_parses_structured_body(
    network_connectivity: Connectivity,
) -> None:
    """Verify structured error details are attached to a NetworkApiError subclass."""
    body = (
        b'{"statusCode":401,"statusName":"UNAUTHORIZED",'
        b'"code":"api.authentication.missing-credentials",'
        b'"message":"Missing credentials",'
        b'"timestamp":"2024-11-27T08:13:46.966Z",'
        b'"requestPath":"/integration/v1/sites/123",'
        b'"requestId":"3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
    )
    parsed_error = network_connectivity._parse_error_response(body)
    assert parsed_error is not None

    error = network_connectivity._build_exception(
        V1Unauthorized,
        "https://host:8443/proxy/network/integration/v1/sites",
        401,
        body,
        parsed_error,
    )

    assert error.status_code == 401
    assert error.status_name == "UNAUTHORIZED"
    assert error.code == "api.authentication.missing-credentials"
    assert error.detail == "Missing credentials"
    assert error.request_path == "/integration/v1/sites/123"
    assert error.request_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def test_network_error_message_falls_back_to_default(
    network_connectivity: Connectivity,
) -> None:
    """Verify unstructured error bodies use the default message."""
    url = "https://host:8443/proxy/network/integration/v1/sites"
    assert network_connectivity._error_message(url, 500, b"not-json", None) == (
        f"Call {url} received 500"
    )


def test_network_exception_type_resolution_order(
    network_connectivity: Connectivity,
) -> None:
    """Verify exception resolution uses code, then status name, then HTTP status."""
    assert (
        network_connectivity._exception_type(
            400,
            {
                "statusCode": 400,
                "statusName": "UNAUTHORIZED",
                "code": "api.authentication.missing-credentials",
                "message": "Missing credentials",
                "timestamp": "2024-11-27T08:13:46.966Z",
                "requestPath": "/integration/v1/sites/123",
                "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            },
        )
        is V1Unauthorized
    )
    assert (
        network_connectivity._exception_type(
            400,
            {
                "statusCode": 400,
                "statusName": "FORBIDDEN",
                "code": "unknown-code",
                "message": "Forbidden",
                "timestamp": "2024-11-27T08:13:46.966Z",
                "requestPath": "/integration/v1/sites/123",
                "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            },
        )
        is V1Forbidden
    )
    assert network_connectivity._exception_type(401, None) is V1Unauthorized
    assert network_connectivity._exception_type(418, None) is V1ResponseError
