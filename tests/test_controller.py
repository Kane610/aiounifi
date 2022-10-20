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
from aiounifi.interfaces.messages import (
    DATA_CLIENT,
    DATA_CLIENT_REMOVED,
    DATA_DEVICE,
    DATA_DPI_APP,
    DATA_DPI_APP_REMOVED,
    DATA_DPI_GROUP,
    DATA_DPI_GROUP_REMOVED,
    DATA_EVENT,
)
from aiounifi.models.api import SOURCE_DATA, SOURCE_EVENT
from aiounifi.models.event import EventKey
from aiounifi.models.message import MessageKey
from aiounifi.websocket import WebsocketSignal, WebsocketState

from .fixtures import (
    EVENT_SWITCH_16_CONNECTED,
    EVENT_WIRELESS_CLIENT_CONNECTED,
    MESSAGE_WIRELESS_CLIENT_REMOVED,
    SWITCH_16_PORT_POE,
    WIRELESS_CLIENT,
    WLANS,
)


async def test_controller(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test controller communicating with a non UniFiOS UniFi controller."""

    mock_aioresponse.get(
        "https://host:8443",
        content_type="application/octet-stream",
        status=302,
    )
    await unifi_controller.check_unifi_os()
    assert not unifi_controller.is_unifi_os
    assert unifi_called_with("get", "", allow_redirects=False)

    mock_aioresponse.post("https://host:8443/api/login", payload="")
    await unifi_controller.login()
    assert unifi_called_with(
        "post",
        "/api/login",
        json={"username": "user", "password": "pass", "remember": True},
    )

    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/device", payload=EMPTY_RESPONSE
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload=WLAN_UNIFIOS_RESPONSE,
    )
    await unifi_controller.initialize()

    assert unifi_called_with(
        "get",
        "/api/s/default/stat/sta",
    )
    assert unifi_called_with(
        "get",
        "/api/s/default/stat/device",
    )
    assert unifi_called_with(
        "get",
        "/api/s/default/rest/user",
    )
    assert unifi_called_with(
        "get",
        "/api/s/default/rest/wlanconf",
    )

    mock_aioresponse.get(
        "https://host:8443/api/self/sites",
        payload=SITE_UNIFIOS_RESPONSE,
    )
    await unifi_controller.sites()
    assert unifi_called_with(
        "get",
        "/api/s/default/rest/wlanconf",
    )

    mock_aioresponse.get(
        "https://host:8443/api/s/default/self",
        payload=SELF_RESPONSE,
    )
    await unifi_controller.site_description()
    assert unifi_called_with("get", "/api/s/default/self")

    assert not unifi_controller.websocket

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()
        assert unifi_controller.websocket.url == "wss://host:8443/wss/s/default/events"

    assert unifi_controller.websocket.state == WebsocketState.STARTING

    unifi_controller.stop_websocket()
    assert unifi_controller.websocket.state == WebsocketState.STOPPED


async def test_unifios_controller(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test controller communicating with a UniFi OS controller."""
    mock_aioresponse.get(
        "https://host:8443",
        content_type="text/html",
        headers={"x-csrf-token": "012"},
    )
    await unifi_controller.check_unifi_os()
    assert unifi_controller.is_unifi_os
    assert unifi_called_with(
        "get",
        "",
        allow_redirects=False,
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

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/sta",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/rest/user",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/stat/device",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/rest/dpiapp",
        payload=EMPTY_RESPONSE,
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/rest/wlanconf",
        payload=WLAN_UNIFIOS_RESPONSE,
    )
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
        "/proxy/network/api/s/default/rest/wlanconf",
        headers={"x-csrf-token": "123"},
    )

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/self/sites",
        payload=SITE_UNIFIOS_RESPONSE,
    )
    await unifi_controller.sites()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/rest/wlanconf",
        headers={"x-csrf-token": "123"},
    )

    mock_aioresponse.get(
        "https://host:8443/proxy/network/api/s/default/self",
        payload=SELF_RESPONSE,
    )
    await unifi_controller.site_description()
    assert unifi_called_with(
        "get",
        "/proxy/network/api/s/default/self",
        headers={"x-csrf-token": "123"},
    )

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()
        assert (
            unifi_controller.websocket.url
            == "wss://host:8443/proxy/network/wss/s/default/events"
        )


async def test_unifios_controller_relogin_success(mock_aioresponse, unifi_controller):
    """Test controller communicating with a UniFi OS controller with retries."""
    mock_aioresponse.get(
        "https://host:8443",
        body="<html>",
        headers={"x-csrf-token": "012"},
        content_type="text/html",
        status=200,
    )

    await unifi_controller.check_unifi_os()
    assert unifi_controller.is_unifi_os

    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        content_type="text/json",
        headers={"x-csrf-token": "123"},
        status=200,
    )

    await unifi_controller.login()

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
    assert unifi_controller.last_response.status == 200


async def test_unifios_controller_relogin_fails(mock_aioresponse, unifi_controller):
    """Test controller communicating with a UniFi OS controller with retries."""
    mock_aioresponse.get(
        "https://host:8443",
        body="<html>",
        headers={"x-csrf-token": "012"},
        content_type="text/html",
        status=200,
    )

    await unifi_controller.check_unifi_os()
    assert unifi_controller.is_unifi_os
    assert len(mock_aioresponse.requests) == 1

    mock_aioresponse.post(
        "https://host:8443/api/auth/login",
        payload=LOGIN_UNIFIOS_JSON_RESPONSE,
        headers={"x-csrf-token": "123"},
        content_type="text/json",
        status=200,
    )

    await unifi_controller.login()

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


async def test_no_data(mock_aioresponse, unifi_controller):
    """Test controller initialize."""
    with pytest.raises(AssertionError):
        unifi_controller.session_handler(WebsocketSignal.DATA)
    with pytest.raises(AssertionError):
        unifi_controller.session_handler(WebsocketSignal.CONNECTION_STATE)

    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )

    await unifi_controller.initialize()

    assert len(unifi_controller.clients._items) == 0
    assert len(unifi_controller.clients_all._items) == 0
    assert len(unifi_controller.devices._items) == 0
    assert len(unifi_controller.wlans._items) == 0

    assert 1 not in unifi_controller.clients
    assert not unifi_controller.clients.get(1)

    message = {"meta": {"message": "blabla"}}
    assert unifi_controller.messages.handler(message) == {}

    assert not unifi_controller.stop_websocket()


async def test_client(mock_aioresponse, unifi_controller):
    """Test controller adding client on initialize."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload=[WIRELESS_CLIENT],
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()
    assert len(unifi_controller.clients._items) == 1


async def test_clients(mock_aioresponse, unifi_controller):
    """Test controller managing clients."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()
    assert len(unifi_controller.clients._items) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    # Add client from websocket
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.CLIENT.value},
        "data": [WIRELESS_CLIENT],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.clients._items) == 1

    # Verify expected callback signalling
    client = unifi_controller.clients[WIRELESS_CLIENT["mac"]]
    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_CLIENT: {client.mac}}
    )

    # Verify APIItems.__getitem__
    client_mac = next(iter(unifi_controller.clients))
    assert client_mac == client.mac

    assert client.update() is None

    # Register callback
    mock_callback = Mock()
    client.register_callback(mock_callback)
    assert len(client._callbacks) == 1

    # Retrieve websocket data
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.CLIENT.value},
        "data": [WIRELESS_CLIENT],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_CLIENT: set()}
    )
    assert client.last_updated == SOURCE_DATA
    assert mock_callback.call_count == 1

    # Retrieve websocket event
    unifi_controller.websocket._data = EVENT_WIRELESS_CLIENT_CONNECTED
    unifi_controller.session_handler(WebsocketSignal.DATA)

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_EVENT: {client.event}}
    )
    assert client.event.key == EventKey.WIRELESS_CLIENT_CONNECTED
    assert client.last_updated == SOURCE_EVENT
    assert mock_callback.call_count == 2

    # Remove callback
    client.remove_callback(mock_callback)
    assert len(client._callbacks) == 0


async def test_message_client_removed(mock_aioresponse, unifi_controller):
    """Test controller communicating client has been removed."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload=[WIRELESS_CLIENT],
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()
    assert len(unifi_controller.clients._items) == 1

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    unifi_controller.websocket._data = MESSAGE_WIRELESS_CLIENT_REMOVED
    unifi_controller.session_handler(WebsocketSignal.DATA)
    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_CLIENT_REMOVED: {WIRELESS_CLIENT["mac"]}}
    )

    assert len(unifi_controller.clients._items) == 0


async def test_device(mock_aioresponse, unifi_controller):
    """Test controller adding device on initialize."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/device", payload=[SWITCH_16_PORT_POE]
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()
    assert len(unifi_controller.devices._items) == 1


async def test_devices(mock_aioresponse, unifi_controller):
    """Test controller managing devices."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()
    assert len(unifi_controller.devices._items) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    # Add client from websocket
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.DEVICE.value},
        "data": [SWITCH_16_PORT_POE],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)
    assert len(unifi_controller.devices._items) == 1

    # Verify expected callback signalling
    device = unifi_controller.devices[SWITCH_16_PORT_POE["mac"]]
    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DEVICE: {device.mac}}
    )

    # Verify APIItems.__getitem__
    device_mac = next(iter(unifi_controller.devices))
    assert device_mac == device.mac

    # Verify Device.Port.__iter__
    port_1 = next(iter(device.ports))
    assert port_1 == 1

    assert device.update() is None

    # Register callback
    mock_callback = Mock()
    device.register_callback(mock_callback)
    assert len(device._callbacks) == 1

    # Retrieve websocket data
    unifi_controller.websocket._data = {
        "meta": {"message": MessageKey.DEVICE.value},
        "data": [SWITCH_16_PORT_POE],
    }
    unifi_controller.session_handler(WebsocketSignal.DATA)

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DEVICE: set()}
    )
    assert device.last_updated == SOURCE_DATA
    assert mock_callback.call_count == 1

    # Retrieve websocket event
    unifi_controller.websocket._data = EVENT_SWITCH_16_CONNECTED
    unifi_controller.session_handler(WebsocketSignal.DATA)

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_EVENT: {device.event}}
    )
    assert device.event.key == EventKey.SWITCH_CONNECTED
    assert device.last_updated == SOURCE_EVENT
    assert mock_callback.call_count == 2

    # Remove callback
    device.remove_callback(mock_callback)
    assert len(device._callbacks) == 0


async def test_dpi_apps(mock_aioresponse, unifi_controller):
    """Test controller managing devices."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()

    assert len(unifi_controller.dpi_apps.values()) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    mock_app_callback = Mock()

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
    dpi_app = unifi_controller.dpi_apps["61783e89c1773a18c0c61f00"]
    dpi_app.register_callback(mock_app_callback)

    mock_app_callback.assert_not_called()
    mock_app_callback.reset_mock()

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_APP: {"61783e89c1773a18c0c61f00"}}
    )
    unifi_controller.callback.reset_mock()

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
    assert dpi_app.enabled

    mock_app_callback.assert_called()
    mock_app_callback.reset_mock()

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_APP: set()}
    )
    unifi_controller.callback.reset_mock()

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
    mock_app_callback.assert_not_called()

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_APP_REMOVED: {"61783e89c1773a18c0c61f00"}}
    )


async def test_dpi_groups(mock_aioresponse, unifi_controller):
    """Test controller managing devices."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/user",
        payload={},
    )
    mock_aioresponse.get("https://host:8443/api/s/default/stat/device", payload={})
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup",
        payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/wlanconf",
        payload={},
    )
    await unifi_controller.initialize()

    assert len(unifi_controller.dpi_groups.values()) == 0

    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    mock_group_callback = Mock()

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
    dpi_group = unifi_controller.dpi_groups["61783dbdc1773a18c0c61ef6"]
    dpi_group.register_callback(mock_group_callback)

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_GROUP: {"61783dbdc1773a18c0c61ef6"}}
    )
    unifi_controller.callback.reset_mock()

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
    assert "61783e89c1773a18c0c61f00" in dpi_group.dpiapp_ids

    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_GROUP: set()}
    )
    unifi_controller.callback.reset_mock()

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

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_GROUP: set()}
    )
    unifi_controller.callback.reset_mock()

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
    mock_group_callback.assert_not_called()
    assert len(unifi_controller.dpi_groups.values()) == 0
    assert "61783dbdc1773a18c0c61ef6" not in unifi_controller.dpi_groups

    unifi_controller.callback.assert_called_with(
        WebsocketSignal.DATA, {DATA_DPI_GROUP_REMOVED: {"61783dbdc1773a18c0c61ef6"}}
    )


async def test_unifios_controller_no_csrf_token(
    mock_aioresponse, unifi_controller, unifi_called_with
):
    """Test controller communicating with a UniFi OS controller without csrf token."""
    mock_aioresponse.get(
        "https://host:8443",
        content_type="text/html",
    )
    await unifi_controller.check_unifi_os()
    assert unifi_controller.is_unifi_os
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
    await unifi_controller.login()
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


@pytest.mark.parametrize("unwanted_behavior, expected_exception", test_data)
async def test_controller_raise_expected_exception(
    mock_aioresponse, unifi_controller, unwanted_behavior, expected_exception
):
    """Verify request raise login required on a 401."""
    mock_aioresponse.post("https://host:8443/api/login", **unwanted_behavior)
    with pytest.raises(expected_exception):
        await unifi_controller.login()


@pytest.mark.parametrize(
    "unsupported_message", ["device:update", "unifi-device:sync", "unsupported"]
)
async def test_handle_unsupported_events(unifi_controller, unsupported_message):
    """Test controller properly ignores unsupported events."""
    with patch("aiounifi.websocket.WSClient.running"):
        unifi_controller.start_websocket()

    unifi_controller.callback.reset_mock()
    unifi_controller.websocket._data = {"meta": {"message": unsupported_message}}
    unifi_controller.session_handler(WebsocketSignal.DATA)
    unifi_controller.callback.assert_not_called()

    assert len(unifi_controller.clients._items) == 0


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

SITE_UNIFIOS_RESPONSE = {
    "meta": {"rc": "ok"},
    "data": [
        {
            "_id": "5e231c10931eb902acf25112",
            "name": "default",
            "desc": "Default",
            "attr_hidden_id": "default",
            "attr_no_delete": True,
            "role": "admin",
        }
    ],
}

SELF_RESPONSE = {
    "meta": {"rc": "ok"},
    "data": [
        {
            "name": "hass",
            "site_id": "5a32aa4ee4b047ede12345678",
            "site_name": "default",
            "site_role": "admin",
            "site_permissions": [],
            "super_site_permissions": [],
            "last_site_id": "5a32aa4ee4b047ede12345678",
            "requires_new_password": False,
            "is_super": False,
            "device_id": "8ed4f0ae-4447-43a4-907d-46bb24bce1bd",
            "admin_id": "5b8c123456b04eb40c39e709",
            "email_alert_enabled": False,
            "email_alert_grouping_enabled": False,
            "email_alert_grouping_delay": 60,
            "push_alert_enabled": True,
            "is_professional_installer": False,
            "html_email_enabled": True,
            "ui_settings": {},
        }
    ],
}
