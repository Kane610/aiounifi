"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""


from aiohttp import client_exceptions
import pytest

from aiounifi import (
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
from aiounifi.websocket import WebsocketSignal, WebsocketState

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
            content_type="text/json",
        )
        await unifi_controller.connectivity.login()
        assert unifi_called_with(
            "post",
            "/api/auth/login",
            json={"username": "user", "password": "pass", "remember": True},
        )
    else:
        mock_aioresponse.post("https://host:8443/api/login", payload="")
        await unifi_controller.connectivity.login()
        assert unifi_called_with(
            "post",
            "/api/login",
            json={"username": "user", "password": "pass", "remember": True},
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
            headers={"x-csrf-token": "123"},
            content_type="text/json",
        )
        await unifi_controller.login()
        assert unifi_called_with(
            "post",
            "/api/auth/login",
            json={"username": "user", "password": "pass", "remember": True},
        )
    else:
        mock_aioresponse.get(
            "https://host:8443", content_type="application/octet-stream", status=302
        )
        mock_aioresponse.post("https://host:8443/api/login", payload="")
        await unifi_controller.login()
        assert unifi_called_with(
            "post",
            "/api/login",
            json={"username": "user", "password": "pass", "remember": True},
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
        content_type="text/json",
        headers={"x-csrf-token": "123"},
        status=200,
    )

    await unifi_controller.connectivity.login()

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/sta",
        payload=EMPTY_RESPONSE,
        content_type="text/json",
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
        content_type="text/json",
        status=200,
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/device",
        payload=EMPTY_RESPONSE,
        content_type="text/json",
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
        content_type="text/json",
        status=200,
    )

    await unifi_controller.connectivity.login()

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/sta",
        payload=EMPTY_RESPONSE,
        content_type="text/json",
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
        content_type="text/json",
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
async def test_controller(
    unifi_controller, unifi_called_with, _mock_endpoints, _new_ws_data_fn
):
    """Test controller communicating with a non UniFiOS UniFi controller."""
    await unifi_controller.initialize()

    assert unifi_called_with("get", "/api/s/default/stat/sta")
    assert unifi_called_with("get", "/api/s/default/rest/user")
    assert unifi_called_with("get", "/api/s/default/stat/device")
    assert unifi_called_with("get", "/api/s/default/rest/dpiapp")
    assert unifi_called_with("get", "/api/s/default/rest/dpigroup")
    assert unifi_called_with("get", "/api/s/default/rest/portforward")
    assert unifi_called_with("get", "/api/self/sites")
    assert unifi_called_with("get", "/api/s/default/stat/sysinfo")
    assert unifi_called_with("get", "/api/s/default/rest/wlanconf")

    assert len(unifi_controller.clients.items()) == 0
    assert len(unifi_controller.clients_all.items()) == 0
    assert len(unifi_controller.devices.items()) == 0
    assert len(unifi_controller.outlets.items()) == 0
    assert len(unifi_controller.ports.items()) == 0
    assert len(unifi_controller.dpi_apps.items()) == 0
    assert len(unifi_controller.dpi_groups.items()) == 0
    assert len(unifi_controller.port_forwarding.items()) == 0
    assert len(unifi_controller.sites.items()) == 1
    assert len(unifi_controller.system_information.items()) == 0
    assert len(unifi_controller.wlans.items()) == 0

    assert unifi_controller.websocket.url == "wss://host:8443/wss/s/default/events"
    assert unifi_controller.websocket.state == WebsocketState.STARTING

    unifi_controller.stop_websocket()
    assert unifi_controller.websocket.state == WebsocketState.STOPPED


@pytest.mark.parametrize(("is_unifi_os", "site_payload"), [(True, SITE_RESPONSE)])
async def test_unifios_controller(
    mock_aioresponse,
    unifi_controller,
    unifi_called_with,
    _mock_endpoints,
    _new_ws_data_fn,
):
    """Test controller communicating with a UniFi OS controller."""
    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        headers={"x-csrf-token": "123"},
        content_type="text/json",
    )
    await unifi_controller.connectivity.login()
    await unifi_controller.initialize()

    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/stat/sta",
        headers={"x-csrf-token": "123"},
    )
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/stat/device",
        headers={"x-csrf-token": "123"},
    )
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/rest/user",
        headers={"x-csrf-token": "123"},
    )
    assert unifi_called_with(
        "get",
        "/proxy/network/api/self/sites",
        headers={"x-csrf-token": "123"},
    )
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/rest/wlanconf",
        headers={"x-csrf-token": "123"},
    )
    assert (
        unifi_controller.websocket.url
        == "wss://host:8443/proxy/network/wss/s/default/events"
    )


async def test_no_websocket_callback(unifi_controller):
    """Test asserts of no websocket callback."""
    with pytest.raises(AssertionError):
        unifi_controller.session_handler(WebsocketSignal.DATA)
    with pytest.raises(AssertionError):
        unifi_controller.session_handler(WebsocketSignal.CONNECTION_STATE)

    assert not unifi_controller.stop_websocket()


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
        content_type="text/json",
    )
    await unifi_controller.connectivity.login()
    assert unifi_called_with(
        "post",
        "/api/auth/login",
        json={"username": "user", "password": "pass", "remember": True},
    )


test_data = [
    ({"status": 401}, LoginRequired),
    ({"status": 403}, Forbidden),
    ({"status": 404}, ResponseError),
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


@pytest.mark.parametrize(
    "unsupported_message", ["device:update", "unifi-device:sync", "unsupported"]
)
async def test_handle_unsupported_events(
    unifi_controller, unsupported_message, _new_ws_data_fn
):
    """Test controller properly ignores unsupported events."""

    unifi_controller.ws_state_callback.reset_mock()
    _new_ws_data_fn({"meta": {"message": unsupported_message}})
    unifi_controller.ws_state_callback.assert_not_called()

    assert len(unifi_controller.clients.items()) == 0
