"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.clients tests/test_clients.py
"""
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller
from aiounifi.models.message import MessageKey

from .fixtures import MESSAGE_WIRELESS_CLIENT_REMOVED, WIRED_CLIENT, WIRELESS_CLIENT

test_data = [
    (
        [{"mac": "0"}],
        {
            "access_point_mac": "",
            "association_time": 0,
            "blocked": False,
            "device_name": "",
            "essid": "",
            "firmware_version": "",
            "first_seen": 0,
            "fixed_ip": "",
            "hostname": "",
            "idle_time": 0,
            "ip": "",
            "is_guest": False,
            "is_wired": False,
            "last_seen": 0,
            "last_seen_by_access_point": 0,
            "last_seen_by_gateway": 0,
            "last_seen_by_switch": 0,
            "latest_association_time": 0,
            "mac": "0",
            "name": "",
            "oui": "",
            "powersave_enabled": None,
            "site_id": "",
            "switch_depth": None,
            "switch_mac": "",
            "switch_port": None,
            "rx_bytes": 0,
            "rx_bytes_r": 0,
            "tx_bytes": 0,
            "tx_bytes_r": 0,
            "uptime": 0,
            "uptime_by_access_point": 0,
            "uptime_by_gateway": 0,
            "uptime_by_switch": 0,
            "wired_rate_mbps": 0,
            "wired_rx_bytes": 0,
            "wired_rx_bytes_r": 0,
            "wired_tx_bytes": 0,
            "wired_tx_bytes_r": 0,
        },
    ),
    (
        [WIRELESS_CLIENT],
        {
            "access_point_mac": "80:2a:a8:00:01:02",
            "association_time": 1587753456,
            "blocked": False,
            "device_name": "Discovery device name",
            "essid": "SSID",
            "firmware_version": "",
            "first_seen": 1513271497,
            "fixed_ip": "192.168.0.1",
            "hostname": "client",
            "idle_time": 1,
            "ip": "192.168.0.1",
            "is_guest": False,
            "is_wired": False,
            "last_seen": 1587765360,
            "last_seen_by_access_point": 1587765360,
            "last_seen_by_gateway": 1587765372,
            "last_seen_by_switch": 1587763868,
            "latest_association_time": 1587765354,
            "mac": WIRELESS_CLIENT["mac"],
            "name": "Client 1",
            "oui": "Apple",
            "powersave_enabled": False,
            "site_id": "5a32aa4ee4b0412345678910",
            "switch_depth": -1,
            "switch_mac": "fc:ec:da:11:22:33",
            "switch_port": 1,
            "rx_bytes": 12867114,
            "rx_bytes_r": 326,
            "tx_bytes": 52852089,
            "tx_bytes_r": 483,
            "uptime": 11904,
            "uptime_by_access_point": 11904,
            "uptime_by_gateway": 18,
            "uptime_by_switch": 318,
            "wired_rate_mbps": 0,
            "wired_rx_bytes": 0,
            "wired_rx_bytes_r": 0,
            "wired_tx_bytes": 0,
            "wired_tx_bytes_r": 0,
        },
    ),
    (
        [WIRED_CLIENT],
        {
            "access_point_mac": "",
            "association_time": 1642487042,
            "blocked": False,
            "device_name": "Network Camera",
            "essid": "",
            "firmware_version": "",
            "first_seen": 1598100273,
            "fixed_ip": "",
            "hostname": "camera-acccde123456",
            "idle_time": 0,
            "ip": "192.168.0.2",
            "is_guest": False,
            "is_wired": True,
            "last_seen": 1642574376,
            "last_seen_by_access_point": 0,
            "last_seen_by_gateway": 1642574376,
            "last_seen_by_switch": 1642574376,
            "latest_association_time": 1642487042,
            "mac": WIRED_CLIENT["mac"],
            "name": "",
            "oui": "Manu",
            "powersave_enabled": None,
            "site_id": "5a32aa4ee4b0412345678910",
            "switch_depth": 0,
            "switch_mac": "fc:ec:da:11:22:33",
            "switch_port": 3,
            "rx_bytes": 0,
            "rx_bytes_r": 0,
            "tx_bytes": 0,
            "tx_bytes_r": 0,
            "uptime": 87334,
            "uptime_by_access_point": 0,
            "uptime_by_gateway": 1527337,
            "uptime_by_switch": 1527337,
            "wired_rate_mbps": 1000,
            "wired_rx_bytes": 0,
            "wired_rx_bytes_r": 0,
            "wired_tx_bytes": 0,
            "wired_tx_bytes_r": 0,
        },
    ),
]


@pytest.mark.parametrize(("client_payload", "reference_data"), test_data)
async def test_clients(
    unifi_controller: Controller, _mock_endpoints: None, reference_data: dict[str, Any]
) -> None:
    """Test clients class."""
    clients = unifi_controller.clients
    await clients.update()
    assert len(clients.items()) == 1

    client = next(iter(clients.values()))
    for key, value in reference_data.items():
        assert getattr(client, key) == value


@pytest.mark.parametrize(
    ("method", "mac", "command"),
    [
        ["block", "0", {"mac": "0", "cmd": "block-sta"}],
        ["unblock", "0", {"mac": "0", "cmd": "unblock-sta"}],
        ["reconnect", "0", {"mac": "0", "cmd": "kick-sta"}],
        ["remove_clients", ["0"], {"macs": ["0"], "cmd": "forget-sta"}],
    ],
)
async def test_client_commands(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[[str, str, dict[str, Any]], bool],
    method: str,
    mac: str | list[str],
    command: dict[str, str | list[str]],
) -> None:
    """Test client commands."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/stamgr", payload={})
    class_command = getattr(unifi_controller.clients, method)
    await class_command(mac)
    assert unifi_called_with("post", "/api/s/default/cmd/stamgr", json=command)


async def test_client_websocket(
    unifi_controller: Controller, _new_ws_data_fn: Callable[[dict[str, Any]], None]
) -> None:
    """Test controller managing clients."""
    unsub = unifi_controller.clients.subscribe(mock_callback := Mock())
    assert len(unifi_controller.clients._subscribers["*"]) == 1
    assert mock_callback.call_count == 0

    # Add client from websocket
    _new_ws_data_fn(
        {
            "meta": {"message": MessageKey.CLIENT.value},
            "data": [WIRELESS_CLIENT],
        }
    )
    assert len(unifi_controller.clients.items()) == 1
    assert mock_callback.call_count == 1

    # Remove callback
    unsub()
    assert len(unifi_controller.clients._subscribers["*"]) == 0


@pytest.mark.parametrize("client_payload", [[WIRELESS_CLIENT]])
async def test_message_client_removed(
    unifi_controller: Controller,
    _mock_endpoints: None,
    _new_ws_data_fn: Callable[[dict[str, Any]], None],
) -> None:
    """Test controller communicating client has been removed."""
    await unifi_controller.initialize()
    assert len(unifi_controller.clients.items()) == 1

    _new_ws_data_fn(MESSAGE_WIRELESS_CLIENT_REMOVED)
    assert len(unifi_controller.clients.items()) == 0
