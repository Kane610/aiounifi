"""Test controller.

pytest --cov-report term-missing --cov=aiounifi.controller tests/test_controller.py
"""

from unittest.mock import Mock, patch

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
from aiounifi.models.message import MessageKey
from aiounifi.websocket import WebsocketSignal, WebsocketState

from .fixtures import (
    MESSAGE_WIRELESS_CLIENT_REMOVED,
    SITE_RESPONSE,
    SWITCH_16_PORT_POE,
    WIRELESS_CLIENT,
    WLANS,
)


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
async def test_controller(unifi_controller, unifi_called_with, _mock_endpoints):
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

    assert not unifi_controller.websocket

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()
        assert unifi_controller.websocket.url == "wss://host:8443/wss/s/default/events"

    assert unifi_controller.websocket.state == WebsocketState.STARTING

    unifi_controller.stop_websocket()
    assert unifi_controller.websocket.state == WebsocketState.STOPPED


@pytest.mark.parametrize(("is_unifi_os", "site_payload"), [(True, SITE_RESPONSE)])
async def test_unifios_controller(
    mock_aioresponse, unifi_controller, unifi_called_with, _mock_endpoints
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

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()
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
async def test_handle_unsupported_events(unifi_controller, unsupported_message):
    """Test controller properly ignores unsupported events."""
    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    unifi_controller.ws_state_callback.reset_mock()
    unifi_controller.websocket._data = {"meta": {"message": unsupported_message}}
    unifi_controller.session_handler(WebsocketSignal.DATA)
    unifi_controller.ws_state_callback.assert_not_called()

    assert len(unifi_controller.clients.items()) == 0


async def test_clients(unifi_controller, _mock_endpoints):
    """Test controller managing clients."""
    await unifi_controller.initialize()
    assert len(unifi_controller.clients.items()) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    # Add client from websocket
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.CLIENT.value},
        "data": [WIRELESS_CLIENT],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.clients.items()) == 1

    # Verify expected callback signalling
    client = unifi_controller.clients[WIRELESS_CLIENT["mac"]]

    # Verify APIItems.__getitem__
    client_mac = next(iter(unifi_controller.clients))
    assert client_mac == client.mac

    # Register callback
    clients = unifi_controller.clients
    mock_callback = Mock()
    unsub = clients.subscribe(mock_callback)
    assert len(clients._subscribers["*"]) == 1

    # Retrieve websocket data
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.CLIENT.value},
        "data": [WIRELESS_CLIENT],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)

    assert mock_callback.call_count == 1

    # Remove callback
    unsub()
    assert len(clients._subscribers["*"]) == 0


@pytest.mark.parametrize("client_payload", [[WIRELESS_CLIENT]])
async def test_message_client_removed(unifi_controller, _mock_endpoints):
    """Test controller communicating client has been removed."""
    await unifi_controller.initialize()
    assert len(unifi_controller.clients.items()) == 1

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    unifi_controller.websocket._data = MESSAGE_WIRELESS_CLIENT_REMOVED
    unifi_controller.session_handler(WebsocketSignal.DATA)

    assert len(unifi_controller.clients.items()) == 0


async def test_devices(unifi_controller, _mock_endpoints):
    """Test controller managing devices."""
    await unifi_controller.initialize()
    assert len(unifi_controller.devices.items()) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    # Add client from websocket
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.DEVICE.value},
        "data": [SWITCH_16_PORT_POE],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.devices.items()) == 1

    # Verify expected callback signalling
    device = unifi_controller.devices[SWITCH_16_PORT_POE["mac"]]

    # Verify APIItems.__getitem__
    device_mac = next(iter(unifi_controller.devices))
    assert device_mac == device.mac

    # Register callback
    devices = unifi_controller.devices
    mock_callback = Mock()
    unsub = devices.subscribe(mock_callback)
    assert len(devices._subscribers["*"]) == 3

    # Retrieve websocket data
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.DEVICE.value},
        "data": [SWITCH_16_PORT_POE],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)

    assert mock_callback.call_count == 1

    # Remove callback
    unsub()
    assert len(devices._subscribers["*"]) == 2


async def test_dpi_apps(unifi_controller, _mock_endpoints):
    """Test controller managing devices."""
    await unifi_controller.initialize()
    assert len(unifi_controller.dpi_apps.values()) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    mock_app_callback = Mock()
    unifi_controller.dpi_apps.subscribe(mock_app_callback)

    # Add DPI app from websocket
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpiapp:add"},
        "data": [
            {
                "apps": [524292],
                "blocked": False,
                "cats": [],
                "enabled": False,
                "log": False,
                "site_id": "5f3edd27ba4cc806a19f2d9c",
                "_id": "61783e89c1773a18c0c61f00",
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.dpi_apps.values()) == 1
    assert "61783e89c1773a18c0c61f00" in unifi_controller.dpi_apps

    mock_app_callback.assert_called()
    mock_app_callback.reset_mock()

    # DPI group is enabled with app from websocket
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpiapp:sync"},
        "data": [
            {
                "_id": "61783e89c1773a18c0c61f00",
                "apps": [524292],
                "blocked": False,
                "cats": [],
                "enabled": True,
                "log": False,
                "site_id": "5f3edd27ba4cc806a19f2d9c",
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    dpi_app = unifi_controller.dpi_apps["61783e89c1773a18c0c61f00"]
    assert dpi_app.enabled

    mock_app_callback.assert_called()
    mock_app_callback.reset_mock()

    # Signal removal of app from apps
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpiapp:delete"},
        "data": [
            {
                "_id": "61783e89c1773a18c0c61f00",
                "apps": [524292],
                "blocked": False,
                "cats": [],
                "enabled": True,
                "log": False,
                "site_id": "5f3edd27ba4cc806a19f2d9c",
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.dpi_apps.values()) == 0
    assert "61783e89c1773a18c0c61f00" not in unifi_controller.dpi_apps
    mock_app_callback.assert_called()


async def test_dpi_groups(unifi_controller, _mock_endpoints):
    """Test controller managing devices."""
    await unifi_controller.initialize()
    assert len(unifi_controller.dpi_groups.values()) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    mock_group_callback = Mock()
    unifi_controller.dpi_groups.subscribe(mock_group_callback)

    # Add DPI group from websocket
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpigroup:add"},
        "data": [
            {
                "name": "dpi group",
                "site_id": "5f3edd27ba4cc806a19f2d9c",
                "_id": "61783dbdc1773a18c0c61ef6",
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.dpi_groups.values()) == 1
    assert "61783dbdc1773a18c0c61ef6" in unifi_controller.dpi_groups

    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    # Update DPI group with app from websocket
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpigroup:sync"},
        "data": [
            {
                "_id": "61783dbdc1773a18c0c61ef6",
                "name": "dpi group",
                "site_id": "5f3edd27ba4cc806a19f2d9c",
                "dpiapp_ids": ["61783e89c1773a18c0c61f00"],
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    dpi_group = unifi_controller.dpi_groups["61783dbdc1773a18c0c61ef6"]
    assert "61783e89c1773a18c0c61f00" in dpi_group.dpiapp_ids

    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    # Signal for group to remove app
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpigroup:sync"},
        "data": [
            {
                "_id": "61783dbdc1773a18c0c61ef6",
                "name": "dpi group",
                "site_id": "5f3edd27ba4cc806a19f2d9c",
                "dpiapp_ids": [],
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)

    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    # Remove group from UniFI controller group from websocket
    unifi_controller.websocket._data = {
        "meta": {"rc": "ok", "message": "dpigroup:delete"},
        "data": [
            {
                "_id": "61783dbdc1773a18c0c61ef6",
                "name": "dpi group",
                "site_id": "5f3edd27ba4cc806a19f2d9c",
                "dpiapp_ids": [],
            }
        ],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    mock_group_callback.assert_called()
    assert len(unifi_controller.dpi_groups.values()) == 0
    assert "61783dbdc1773a18c0c61ef6" not in unifi_controller.dpi_groups


EMPTY_RESPONSE = {"meta": {"rc": "ok"}, "data": []}

LOGIN_UNIFIOS_JSON_RESPONSE = {
    "unique_id": "868d288b-a642-4209-a768-8425498fa928",
    "username": "Testing1",
    "first_name": "Testing",
    "last_name": "Testing",
    "full_name": "Testing Testing",
    "email": "",
    "email_status": "UNVERIFIED",
    "phone": "",
    "avatar": "",
    "avatar_relative_path": "",
    "status": "ACTIVE",
    "sso_account": "",
    "sso_uuid": "",
    "sso_username": "",
    "create_time": 1585163886,
    "local_account_exist": True,
    "uid_sso_id": "",
    "uid_sso_account": "",
    "password_revision": 1585163886,
    "extras": None,
    "nfc_token": "",
    "nfc_display_id": "",
    "update_time": 1585167486,
    "groups": [],
    "roles": [
        {
            "unique_id": "ddf31242-c4f1-4dbc-b362-d0b220cae124",
            "name": "Super Administrator",
            "system_role": True,
            "system_key": "super_administrator",
            "level": 2,
        }
    ],
    "permissions": {
        "access.management": ["admin"],
        "led.management": ["admin"],
        "network.management": ["admin"],
        "protect.management": ["admin"],
        "system.management.location": ["admin"],
        "system.management.user": ["admin"],
        "talk.management": ["admin"],
    },
    "scopes": [
        "view:user_timezone",
        "view:user",
        "view:systemlog",
        "view:settings",
        "view:role",
        "view:permission:viewer",
        "view:permission:admin",
        "view:notification",
        "view:location_policy",
        "view:location_device",
        "view:location_activity",
        "view:location",
        "view:holiday_timezone",
        "view:holiday",
        "view:group",
        "view:door_group",
        "view:controller:talk",
        "view:controller:protect",
        "view:controller:network",
        "view:controller:led",
        "view:controller:access",
        "view:cloud_access",
        "view:app:users",
        "view:app:settings",
        "view:app:locations",
        "view:access.visitor",
        "view:access.systemlog",
        "view:access.schedule",
        "view:access.policy",
        "view:access.nfc_card",
        "view:access.device",
        "view:access.dashboard",
        "update:access.device",
        "systemlog:user",
        "systemlog:system",
        "systemlog:location",
        "systemlog:access",
        "notify:user",
        "notify:location",
        "notify:access",
        "manage:controller:talk",
        "manage:controller:protect",
        "manage:controller:network",
        "manage:controller:led",
        "manage:controller:access",
        "edit:user_timezone",
        "edit:user",
        "edit:systemlog",
        "edit:settings",
        "edit:role",
        "edit:permission:viewer",
        "edit:permission:admin",
        "edit:notification",
        "edit:location_policy",
        "edit:location_device",
        "edit:location_activity",
        "edit:location",
        "edit:holiday_timezone",
        "edit:holiday",
        "edit:group",
        "edit:feedback",
        "edit:door_group",
        "edit:access.visitor",
        "edit:access.schedule",
        "edit:access.policy",
        "edit:access.nfc_card",
        "edit:access.device",
        "delete:access.device",
        "assign:role",
        "adopt:access.device",
    ],
    "cloud_access_granted": False,
    "id": "868d288b-a642-4209-a768-8425498fa928",
    "isOwner": False,
    "isSuperAdmin": True,
}

WLAN_UNIFIOS_RESPONSE = {"meta": {"rc": "ok"}, "data": WLANS}
