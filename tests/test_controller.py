"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""

from collections.abc import Callable
import ssl

from aiohttp import ClientSession, client_exceptions, web
from aioresponses import aioresponses
import pytest
import trustme

from aiounifi import (
    AiounifiException,
    BadGateway,
    Forbidden,
    LoginRequired,
    NoPermission,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    TwoFaTokenRequired,
    Unauthorized,
)
from aiounifi.controller import Controller
from aiounifi.errors import AuthenticationRateLimitError
from aiounifi.models.api import ApiRequest, ApiRequestV2
from aiounifi.models.configuration import Configuration

from .fixtures import LOGIN_UNIFIOS_JSON_RESPONSE, SITE_RESPONSE

EMPTY_RESPONSE = {"meta": {"rc": "ok"}, "data": []}


@pytest.mark.parametrize("is_unifi_os", [True, False])
async def test_check_unifi(
    mock_aioresponse, unifi_controller, unifi_called_with, is_unifi_os
):
    """Test validating if controller is hosted on UniFi OS."""
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
    await unifi_controller.connectivity.check_unifi_os()
    assert unifi_controller.connectivity.is_unifi_os is is_unifi_os
    assert unifi_called_with("get", "", allow_redirects=False)


@pytest.mark.parametrize("is_unifi_os", [True, False])
async def test_login(
    mock_aioresponse, unifi_controller, unifi_called_with, is_unifi_os
):
    """Test logging in to controller."""
    if is_unifi_os:
        mock_aioresponse.get(
            "https://host:8443",
            content_type="text/html",
            headers={"x-csrf-token": "012"},
        )
        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=LOGIN_UNIFIOS_JSON_RESPONSE,
            headers={"x-csrf-token": "123"},
            content_type="application/json",
        )
        await unifi_controller.connectivity.login()
        assert unifi_called_with(
            "post",
            "/api/auth/login",
            json={"username": "user", "password": "pass", "rememberMe": True},
        )
    else:
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={"meta": {"rc": "ok"}, "data": []},
            content_type="application/json",
        )
        await unifi_controller.connectivity.login()
        assert unifi_called_with(
            "post",
            "/api/login",
            json={"username": "user", "password": "pass", "rememberMe": True},
        )


@pytest.mark.parametrize("is_unifi_os", [True, False])
async def test_controller_login(
    mock_aioresponse, unifi_controller, unifi_called_with, is_unifi_os
):
    """Test logging in to controller."""
    if is_unifi_os:
        mock_aioresponse.get(
            "https://host:8443",
            content_type="text/html",
            headers={"x-csrf-token": "012"},
        )
        mock_aioresponse.post(
            "https://host:8443/api/auth/login",
            payload=LOGIN_UNIFIOS_JSON_RESPONSE,
            headers={"x-csrf-token": "123", "Set-Cookie": "456"},
            content_type="application/json",
        )
        await unifi_controller.login()
        assert unifi_called_with(
            "post",
            "/api/auth/login",
            json={"username": "user", "password": "pass", "rememberMe": True},
        )
    else:
        mock_aioresponse.get(
            "https://host:8443", content_type="application/octet-stream", status=302
        )
        mock_aioresponse.post(
            "https://host:8443/api/login",
            payload={"meta": {"rc": "ok"}, "data": []},
        )
        await unifi_controller.login()
        assert unifi_called_with(
            "post",
            "/api/login",
            json={"username": "user", "password": "pass", "rememberMe": True},
        )
    assert unifi_called_with("get", "", allow_redirects=False)


async def test_relogin_success(mock_aioresponse, unifi_controller):
    """Test controller communicating with a UniFi OS controller with retries."""
    mock_aioresponse.get(
        "https://host:8443",
        body="<html>",
        headers={"x-csrf-token": "012"},
        content_type="text/html",
        status=200,
    )

    await unifi_controller.connectivity.check_unifi_os()
    assert unifi_controller.connectivity.is_unifi_os

    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        content_type="application/json",
        headers={"x-csrf-token": "123"},
        status=200,
    )

    await unifi_controller.connectivity.login()

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/sta",
        payload=EMPTY_RESPONSE,
        content_type="application/json",
        status=200,
    )
    await unifi_controller.clients.update()

    # After a login failure we retry once
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/device",
        body="<html>AUTH FAILED</html>",
        content_type="text/html",
        status=401,
    )

    mock_aioresponse.get(
        "https://host:8443",
        body="<html>",
        headers={"x-csrf-token": "012"},
        content_type="text/html",
        status=200,
    )
    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        headers={"x-csrf-token": "563"},
        content_type="application/json",
        status=200,
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/device",
        payload=EMPTY_RESPONSE,
        content_type="application/json",
        status=200,
    )

    await unifi_controller.devices.update()


async def test_relogin_fails(mock_aioresponse, unifi_controller):
    """Test controller communicating with a UniFi OS controller with retries."""
    mock_aioresponse.get(
        "https://host:8443",
        body="<html>",
        headers={"x-csrf-token": "012"},
        content_type="text/html",
        status=200,
    )

    await unifi_controller.connectivity.check_unifi_os()
    assert unifi_controller.connectivity.is_unifi_os
    assert len(mock_aioresponse.requests) == 1

    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        headers={"x-csrf-token": "123"},
        content_type="application/json",
        status=200,
    )

    await unifi_controller.connectivity.login()

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/sta",
        payload=EMPTY_RESPONSE,
        content_type="application/json",
        status=200,
    )
    await unifi_controller.clients.update()

    # After a login failure we retry once
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/device",
        body="<html>AUTH FAILED</html>",
        content_type="text/html",
        status=401,
    )
    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        headers={"x-csrf-token": "456"},
        content_type="application/json",
        status=401,
    )

    with pytest.raises(LoginRequired):
        await unifi_controller.devices.update()

    # After a login failure and retry, we do
    # not retry over and over
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/device",
        body="<html>AUTH FAILED</html>",
        content_type="text/html",
        status=401,
    )
    with pytest.raises(LoginRequired):
        await unifi_controller.devices.update()


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


@pytest.mark.parametrize("site_payload", [SITE_RESPONSE["data"]])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_controller(unifi_controller, unifi_called_with, new_ws_data_fn):
    """Test controller communicating with a non UniFiOS UniFi controller."""
    await unifi_controller.clients.update()
    assert unifi_called_with("get", "/api/s/default/stat/sta")
    assert len(unifi_controller.clients.items()) == 0

    await unifi_controller.clients_all.update()
    assert unifi_called_with("get", "/api/s/default/rest/user")
    assert len(unifi_controller.clients_all.items()) == 0

    await unifi_controller.devices.update()
    assert unifi_called_with("get", "/api/s/default/stat/device")
    assert len(unifi_controller.devices.items()) == 0
    assert len(unifi_controller.outlets.items()) == 0
    assert len(unifi_controller.ports.items()) == 0

    await unifi_controller.dpi_apps.update()
    assert unifi_called_with("get", "/api/s/default/rest/dpiapp")
    assert len(unifi_controller.dpi_apps.items()) == 0

    await unifi_controller.dpi_groups.update()
    assert unifi_called_with("get", "/api/s/default/rest/dpigroup")
    assert len(unifi_controller.dpi_groups.items()) == 0

    await unifi_controller.port_forwarding.update()
    assert unifi_called_with("get", "/api/s/default/rest/portforward")
    assert len(unifi_controller.port_forwarding.items()) == 0

    await unifi_controller.sites.update()
    assert unifi_called_with("get", "/api/self/sites")
    assert len(unifi_controller.sites.items()) == 1

    await unifi_controller.system_information.update()
    assert unifi_called_with("get", "/api/s/default/stat/sysinfo")
    assert len(unifi_controller.system_information.items()) == 0

    await unifi_controller.traffic_routes.update()
    assert unifi_called_with("get", "/v2/api/site/default/trafficroutes")
    assert len(unifi_controller.traffic_routes.items()) == 0

    await unifi_controller.traffic_rules.update()
    assert unifi_called_with("get", "/v2/api/site/default/trafficrules")
    assert len(unifi_controller.traffic_rules.items()) == 0

    await unifi_controller.vouchers.update()
    assert unifi_called_with("get", "/api/s/default/stat/voucher")
    assert len(unifi_controller.vouchers.items()) == 0

    await unifi_controller.wlans.update()
    assert unifi_called_with("get", "/api/s/default/rest/wlanconf")
    assert len(unifi_controller.wlans.items()) == 0
