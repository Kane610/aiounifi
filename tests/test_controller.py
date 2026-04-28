"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""

from dataclasses import dataclass
import ssl

from aiohttp import ClientSession, client_exceptions, web
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


@dataclass
class _RequestStub:
    """Request-like stub validating connectivity duck-typing behavior."""

    method: str = "get"
    path: str = "/test"
    data: dict[str, object] | None = None

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Build a legacy-style API path for tests."""
        if is_unifi_os:
            return f"/proxy/network/api/s/{site}{self.path}"
        return f"/api/s/{site}{self.path}"

    def decode(self, raw: bytes) -> dict[str, object]:
        """Return a legacy-shaped response for compatibility checks."""
        return EMPTY_RESPONSE


async def test_connectivity_request_accepts_request_like_object(
    mock_aioresponse, unifi_controller: Controller
) -> None:
    """Verify connectivity works with structural request objects."""
    mock_aioresponse.get("https://host:8443/api/s/default/test", payload=EMPTY_RESPONSE)

    response = await unifi_controller.connectivity.request(_RequestStub())

    assert response == EMPTY_RESPONSE


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


@pytest.mark.parametrize(("is_unifi_os", "site_payload"), [(True, SITE_RESPONSE)])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_unifios_controller(
    mock_aioresponse,
    unifi_controller,
    unifi_called_with,
    new_ws_data_fn,
):
    """Test controller communicating with a UniFi OS controller."""
    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        headers={"x-csrf-token": "123"},
        content_type="application/json",
    )
    await unifi_controller.connectivity.login()

    await unifi_controller.clients.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/stat/sta",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.devices.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/stat/device",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.clients_all.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/rest/user",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.sites.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/self/sites",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.traffic_routes.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/v2/api/site/default/trafficroutes",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.traffic_rules.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/v2/api/site/default/trafficrules",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.vouchers.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/stat/voucher",
        headers={"x-csrf-token": "123"},
    )
    await unifi_controller.wlans.update()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/rest/wlanconf",
        headers={"x-csrf-token": "123"},
    )


async def test_unifios_controller_login_html_response(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test controller communicating with a UniFi OS controller text/html response."""
    mock_aioresponse.get(
        "https://host:8443",
        content_type="text/html",
    )
    await unifi_controller.connectivity.check_unifi_os()

    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload="Login Failed: Host starting up",
        content_type="text/html",
    )
    with pytest.raises(RequestError):
        await unifi_controller.connectivity.login()


async def test_unifios_controller_no_csrf_token(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test controller communicating with a UniFi OS controller without csrf token."""
    mock_aioresponse.get(
        "https://host:8443",
        content_type="text/html",
    )
    await unifi_controller.connectivity.check_unifi_os()
    assert unifi_controller.connectivity.is_unifi_os
    assert unifi_called_with(
        "get",
        "",
        allow_redirects=False,
    )

    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        content_type="application/json",
    )
    await unifi_controller.connectivity.login()
    assert unifi_called_with(
        "post",
        "/api/auth/login",
        json={"username": "user", "password": "pass", "rememberMe": True},
    )


test_data = [
    ({"status": 401}, LoginRequired),
    ({"status": 403}, Forbidden),
    ({"status": 404}, ResponseError),
    ({"status": 429}, ResponseError),
    ({"status": 502}, BadGateway),
    ({"status": 503}, ServiceUnavailable),
    ({"exception": client_exceptions.ClientError}, RequestError),
    (
        {"payload": {"meta": {"msg": "api.err.LoginRequired", "rc": "error"}}},
        LoginRequired,
    ),
    (
        {"payload": {"meta": {"msg": "api.err.Invalid", "rc": "error"}}},
        Unauthorized,
    ),
    (
        {"payload": {"meta": {"msg": "api.err.NoPermission", "rc": "error"}}},
        NoPermission,
    ),
    (
        {"payload": {"meta": {"msg": "api.err.Ubic2faTokenRequired", "rc": "error"}}},
        TwoFaTokenRequired,
    ),
]


@pytest.mark.parametrize(("unwanted_behavior", "expected_exception"), test_data)
async def test_controller_raise_expected_exception(
    mock_aioresponse, unifi_controller, unwanted_behavior, expected_exception
):
    """Verify request raise login required on a 401."""
    mock_aioresponse.post("https://host:8443/api/login", **unwanted_behavior)
    with pytest.raises(expected_exception):
        await unifi_controller.connectivity.login()


async def test_controller_authentication_rate_limit_error(
    mock_aioresponse, unifi_controller
):
    """Test that 429 AUTHENTICATION_FAILED_LIMIT_REACHED raises AuthenticationRateLimitError."""
    mock_aioresponse.post(
        "https://host:8443/api/login",
        status=429,
        payload={
            "message": "You've reached the login attempt limit",
            "code": "AUTHENTICATION_FAILED_LIMIT_REACHED",
        },
    )
    with pytest.raises(AuthenticationRateLimitError):
        await unifi_controller.connectivity.login()


api_request_data = [
    (
        ApiRequest,
        "/api/s/default",
        {"payload": {"meta": {"msg": "api.err.LoginRequired", "rc": "error"}}},
        LoginRequired,
    ),
    (
        ApiRequest,
        "/api/s/default",
        {"payload": {"meta": {"msg": "api.err.Invalid", "rc": "error"}}},
        Unauthorized,
    ),
    (
        ApiRequest,
        "/api/s/default",
        {"payload": {"meta": {"msg": "api.err.NoPermission", "rc": "error"}}},
        NoPermission,
    ),
    (
        ApiRequest,
        "/api/s/default",
        {"payload": {"meta": {"msg": "api.err.Ubic2faTokenRequired", "rc": "error"}}},
        TwoFaTokenRequired,
    ),
    (
        ApiRequest,
        "/api/s/default",
        {"payload": {"meta": {"msg": "api.err.OtherError", "rc": "error"}}},
        AiounifiException,
    ),
    (
        ApiRequestV2,
        "/v2/api/site/default",
        {"payload": {"errorCode": 1, "message": "api.err.LoginRequired"}},
        LoginRequired,
    ),
    (
        ApiRequestV2,
        "/v2/api/site/default",
        {"payload": {"errorCode": 2, "message": "api.err.Invalid"}},
        Unauthorized,
    ),
    (
        ApiRequestV2,
        "/v2/api/site/default",
        {"payload": {"errorCode": 3, "message": "api.err.NoPermission"}},
        NoPermission,
    ),
    (
        ApiRequestV2,
        "/v2/api/site/default",
        {"payload": {"errorCode": 4, "message": "api.err.Ubic2faTokenRequired"}},
        TwoFaTokenRequired,
    ),
    (
        ApiRequestV2,
        "/v2/api/site/default",
        {"payload": {"errorCode": 5, "message": "api.err.OtherError"}},
        AiounifiException,
    ),
]


@pytest.mark.parametrize(("api_request", "path", "input", "expected"), api_request_data)
async def test_api_request_error_handling(
    mock_aioresponse,
    unifi_controller: Controller,
    api_request,
    path,
    input,
    expected,
):
    """Verify request raise login required on a 401."""
    mock_aioresponse.get(f"https://host:8443{path}/test", **input)
    with pytest.raises(expected):
        await unifi_controller.connectivity.request(api_request("get", "/test"))


@pytest.mark.parametrize(("unwanted_behavior", "expected_exception"), test_data)
async def test_api_request_generic_error_handling(
    mock_aioresponse,
    unifi_controller: Controller,
    unwanted_behavior,
    expected_exception,
):
    """Verify request raise login required on a 401."""
    mock_aioresponse.get("https://host:8443/api/s/default/test", **unwanted_behavior)
    with pytest.raises(expected_exception):
        await unifi_controller.connectivity.request(ApiRequest("get", "/test"))


@pytest.mark.parametrize(
    "unsupported_message", ["device:update", "unifi-device:sync", "unsupported"]
)
async def test_handle_unsupported_events(
    unifi_controller, unsupported_message, new_ws_data_fn
):
    """Test controller properly ignores unsupported events."""
    unifi_controller.ws_state_callback.reset_mock()
    new_ws_data_fn({"meta": {"message": unsupported_message}})
    unifi_controller.ws_state_callback.assert_not_called()

    assert len(unifi_controller.clients.items()) == 0


async def test_websocket(aiohttp_server) -> None:
    """Test positive websocket."""

    tls_certificate_authority = trustme.CA()
    tls_certificate = tls_certificate_authority.issue_server_cert(
        "localhost", "127.0.0.1", "::1"
    )
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    tls_certificate.configure_cert(ssl_context)

    async def handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        await ws.send_json({"meta": {"message": "device:update"}})
        await ws.send_json(
            {
                "meta": {"rc": "ok", "message": "dpigroup:add"},
                "data": [
                    {
                        "name": "dpi group",
                        "site_id": "5f3edd27ba4cc806a19f2d9c",
                        "_id": "61783dbdc1773a18c0c61ef6",
                    }
                ],
            }
        )

        await ws.close()
        return ws

    app = web.Application()
    app.router.add_get("/wss/s/default/events", handler)
    await aiohttp_server(app, port=8443, ssl=ssl_context)

    config = Configuration(
        ClientSession(), "0.0.0.0", username="user", password="pass", ssl_context=False
    )
    controller = Controller(config)
    await controller.start_websocket()

    assert len(controller.dpi_groups.items()) == 1


async def test_login_malformed_json(mock_aioresponse, unifi_controller):
    """Test login with malformed JSON response raises RequestError."""
    mock_aioresponse.post(
        "https://host:8443/api/login",
        body="not json",
        content_type="application/json",
    )
    with pytest.raises(RequestError):
        await unifi_controller.connectivity.login()


async def test_login_missing_csrf_and_cookie(mock_aioresponse, unifi_controller):
    """Test login with missing csrf and cookie headers does not break."""
    mock_aioresponse.post(
        "https://host:8443/api/login",
        payload={"meta": {"rc": "ok"}, "data": []},
        content_type="application/json",
    )
    await unifi_controller.connectivity.login()
    # Headers should not be set
    assert "x-csrf-token" not in unifi_controller.connectivity.headers
    assert "Cookie" not in unifi_controller.connectivity.headers


async def test_login_2fa_failure(mock_aioresponse, unifi_controller):
    """Test login with repeated 2FA failure raises correct error."""
    # First response triggers 2FA
    mock_aioresponse.post(
        "https://host:8443/api/login",
        payload={"meta": {"rc": "error", "msg": "api.err.Ubic2faTokenRequired"}},
        content_type="application/json",
    )
    # Second response is also error
    mock_aioresponse.post(
        "https://host:8443/api/login",
        payload={"meta": {"rc": "error", "msg": "api.err.Ubic2faTokenRequired"}},
        content_type="application/json",
    )
    with pytest.raises(TwoFaTokenRequired):
        await unifi_controller.connectivity.login()


async def test_login_2fa_success_after_error(mock_aioresponse, unifi_controller):
    """Test login with correct 2FA after initial error succeeds and sets headers."""
    # Ensure totp_secret is set for 2FA retry
    unifi_controller.connectivity.config.totp_secret = "JBSWY3DPEHPK3PXP"
    # First response triggers 2FA
    mock_aioresponse.post(
        "https://host:8443/api/login",
        payload={"meta": {"rc": "error", "msg": "api.err.Ubic2faTokenRequired"}},
        content_type="application/json",
    )
    # Second response is success
    mock_aioresponse.post(
        "https://host:8443/api/login",
        payload={"meta": {"rc": "ok"}, "data": []},
        content_type="application/json",
        headers={"x-csrf-token": "token", "Set-Cookie": "cookie"},
    )
    await unifi_controller.connectivity.login()
    assert unifi_controller.connectivity.headers["x-csrf-token"] == "token"
    assert unifi_controller.connectivity.headers["Cookie"] == "cookie"


async def test_login_sso_mfa_missing_totp_secret(mock_aioresponse, unifi_controller):
    """Test login with SSO MFA but missing totp_secret raises RequestError."""
    unifi_controller.connectivity.config.totp_secret = None
    mock_aioresponse.post(
        "https://host:8443/api/login",
        status=499,
        payload={},
        content_type="application/json",
    )
    with pytest.raises(RequestError):
        await unifi_controller.connectivity.login()
