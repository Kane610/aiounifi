"""Unit tests for Network Integration API connectivity."""

from __future__ import annotations

from typing import Any

import aiohttp
from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller
from aiounifi.errors import RequestError, ResponseError, Unauthorized
from aiounifi.models.configuration import Configuration
from aiounifi.network.v1.connectivity import API_KEY_HEADER, Connectivity
from aiounifi.network.v1.models.api import ApiRequest
from aiounifi.network.v1.models.info import InfoRequest

from .helpers import request_kwargs

SITES_URL = "https://host:8443/proxy/network/integration/v1/sites"
INFO_URL = "https://host:8443/proxy/network/integration/v1/info"

SITES_PAYLOAD: dict[str, Any] = {
    "offset": 0,
    "limit": 25,
    "count": 1,
    "totalCount": 1,
    "data": [
        {
            "id": "8a1b2c3d-4e5f-6789-abcd-ef0123456789",
            "internalReference": "default",
            "name": "Default",
        }
    ],
}


async def test_network_request_requires_api_key(
    unifi_controller: Controller,
) -> None:
    """Verify requests fail fast when no API key is configured."""
    unifi_controller.connectivity.config.api_key = ""
    connectivity = Connectivity(unifi_controller.connectivity.config)

    with pytest.raises(RequestError, match="api_key is required"):
        await connectivity.request(ApiRequest(method="get", path="/v1/sites"))


async def test_network_request_rejects_blank_api_key(
    network_config: Configuration,
) -> None:
    """Verify requests fail fast when the API key is blank after stripping."""
    network_config.api_key = " "
    connectivity = Connectivity(network_config)

    with pytest.raises(RequestError, match="api_key is required"):
        await connectivity.request(ApiRequest(method="get", path="/v1/sites"))


async def test_network_request_sends_json_body(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
) -> None:
    """Verify write requests send JSON and a content type."""
    mock_aioresponse.post(
        "https://host:8443/proxy/network/integration/v1/sites",
        payload=SITES_PAYLOAD,
    )

    await network_connectivity.request(
        ApiRequest(method="post", path="/v1/sites", data={"name": "HQ"})
    )

    kwargs = request_kwargs(mock_aioresponse, "POST", "/v1/sites")
    assert kwargs["json"] == {"name": "HQ"}
    assert kwargs["headers"]["Content-Type"] == "application/json"


async def test_network_request_sends_api_key_header(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
    api_key: str,
) -> None:
    """Verify Integration API calls authenticate with X-API-KEY."""
    mock_aioresponse.get(SITES_URL, payload=SITES_PAYLOAD)

    response = await network_connectivity.request(
        ApiRequest(method="get", path="/v1/sites")
    )

    assert response["data"][0]["internalReference"] == "default"
    headers = request_kwargs(mock_aioresponse, "GET", "/v1/sites")["headers"]
    assert headers[API_KEY_HEADER] == api_key
    assert headers["Accept"] == "application/json"


async def test_info_request_sends_api_key_header(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
    api_key: str,
) -> None:
    """Verify GET /v1/info includes the API key and decodes applicationVersion."""
    mock_aioresponse.get(INFO_URL, payload={"applicationVersion": "9.1.0"})

    response = await network_connectivity.request(InfoRequest.create())

    assert response["data"][0]["applicationVersion"] == "9.1.0"
    headers = request_kwargs(mock_aioresponse, "GET", "/v1/info")["headers"]
    assert headers[API_KEY_HEADER] == api_key


async def test_network_request_raises_unauthorized(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
) -> None:
    """Verify a 401 from the Integration API raises Unauthorized."""
    mock_aioresponse.get(
        SITES_URL,
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


async def test_network_request_wraps_client_errors(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
) -> None:
    """Verify transport client errors are wrapped as RequestError."""
    mock_aioresponse.get(SITES_URL, exception=aiohttp.ClientConnectionError("boom"))

    with pytest.raises(RequestError, match="Error requesting data"):
        await network_connectivity.request(ApiRequest(method="get", path="/v1/sites"))


async def test_network_request_rejects_non_json_success(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
) -> None:
    """Verify non-JSON success bodies raise ResponseError."""
    mock_aioresponse.get(SITES_URL, status=200, body=b" ok ")

    with pytest.raises(ResponseError, match="returned a non-JSON response"):
        await network_connectivity.request(ApiRequest(method="get", path="/v1/sites"))


def test_network_build_url(network_connectivity: Connectivity) -> None:
    """Verify URL builder prefixes /proxy/network/integration."""
    assert (
        network_connectivity._build_url("/v1/sites")
        == "https://host:8443/proxy/network/integration/v1/sites"
    )


def test_api_request_rejects_non_v1_path() -> None:
    """Verify ApiRequest raises ValueError when path does not start with /v1/."""
    with pytest.raises(ValueError, match="/v1/"):
        ApiRequest(method="get", path="/integration/v1/sites")


def test_api_request_decode_requires_paginated_envelope() -> None:
    """Verify paginated decode rejects malformed payloads."""
    request = ApiRequest(method="get", path="/v1/sites")
    with pytest.raises(ResponseError, match="not an object"):
        request.decode(b"[]")
    with pytest.raises(ResponseError, match="missing required field"):
        request.decode(b'{"data": []}')


def test_info_request_decode_requires_application_version() -> None:
    """Verify info decode rejects payloads without applicationVersion."""
    with pytest.raises(ResponseError, match="info response is invalid"):
        InfoRequest.create().decode(b'{"version": "9.1.0"}')


def test_parse_error_response_ignores_invalid_payloads(
    network_connectivity: Connectivity,
) -> None:
    """Verify malformed structured error payloads are ignored."""
    assert network_connectivity._parse_error_response(b"not-json") is None
    assert network_connectivity._parse_error_response(b"[]") is None
    assert (
        network_connectivity._parse_error_response(
            b'{"statusCode":401,"statusName":"UNAUTHORIZED"}'
        )
        is None
    )


async def test_network_request_unauthorized_without_structured_body(
    mock_aioresponse: aioresponses,
    network_connectivity: Connectivity,
) -> None:
    """Verify 401 without an error envelope still raises Unauthorized."""
    mock_aioresponse.get(SITES_URL, status=401, body=b"denied")

    with pytest.raises(Unauthorized, match="received 401"):
        await network_connectivity.request(ApiRequest(method="get", path="/v1/sites"))
