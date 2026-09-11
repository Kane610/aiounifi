"""API-key login tests for UniFi Network Integration API."""

from collections.abc import Callable

from aiohttp import ClientSession
from aioresponses import aioresponses
import pytest

from aiounifi import LoginRequired, Unauthorized
from aiounifi.controller import Controller
from aiounifi.models.configuration import Configuration


@pytest.mark.parametrize("is_unifi_os", [True, False])
async def test_login_with_api_key(
    mock_aioresponse: aioresponses,
    unifi_called_with: Callable[..., bool],
    is_unifi_os: bool,
) -> None:
    """API key login skips classic /api/login and validates GET /v1/info."""
    session = ClientSession()
    config = Configuration(session, "host", api_key="secret-key")
    controller = Controller(config)

    try:
        if is_unifi_os:
            mock_aioresponse.get(
                "https://host:8443",
                content_type="text/html",
                headers={"x-csrf-token": "012"},
            )
        else:
            mock_aioresponse.get(
                "https://host:8443",
                content_type="application/octet-stream",
                status=302,
            )
        mock_aioresponse.get(
            "https://host:8443/proxy/network/integration/v1/info",
            payload={"applicationVersion": "9.1.0"},
            content_type="application/json",
        )

        await controller.login()

        assert unifi_called_with("get", "", allow_redirects=False)
        assert not unifi_called_with("post", "/api/auth/login")
        assert not unifi_called_with("post", "/api/login")
        info_headers = None
        for req, call_list in mock_aioresponse.requests.items():
            if str(req[1].path).endswith("/v1/info"):
                info_headers = call_list[0][1]["headers"]
        assert info_headers is not None
        assert info_headers["X-API-KEY"] == "secret-key"
        assert controller.connectivity.can_retry_login is False
    finally:
        await session.close()


async def test_login_with_invalid_api_key(mock_aioresponse: aioresponses) -> None:
    """Invalid Integration API keys raise Unauthorized from GET /v1/info."""
    session = ClientSession()
    config = Configuration(session, "host", api_key="bad-key")
    controller = Controller(config)

    try:
        mock_aioresponse.get(
            "https://host:8443",
            content_type="text/html",
            headers={"x-csrf-token": "012"},
        )
        mock_aioresponse.get(
            "https://host:8443/proxy/network/integration/v1/info",
            status=401,
            payload={
                "statusCode": 401,
                "statusName": "UNAUTHORIZED",
                "code": "api.authentication.invalid-credentials",
                "message": "Invalid credentials",
                "timestamp": "2024-11-27T08:13:46.966Z",
                "requestPath": "/integration/v1/info",
                "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            },
        )

        with pytest.raises(Unauthorized, match="Invalid credentials"):
            await controller.login()
        assert not any(
            str(req[1].path).endswith("/login") for req in mock_aioresponse.requests
        )
    finally:
        await session.close()


async def test_login_requires_credentials() -> None:
    """Login without username/password or api_key raises LoginRequired."""
    session = ClientSession()
    config = Configuration(session, "host")
    controller = Controller(config)

    try:
        with pytest.raises(LoginRequired, match="api_key"):
            await controller.connectivity.login()
    finally:
        await session.close()
