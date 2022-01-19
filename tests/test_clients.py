"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.clients tests/test_clients.py
"""

import pytest

from aiounifi.clients import Clients

from .fixtures import WIRED_CLIENT, WIRELESS_CLIENT
from .test_controller import verify_call


async def test_no_clients(mock_aioresponse, unifi_controller):
    """Test that no clients also work."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/sta",
        payload={},
    )

    clients = Clients([], unifi_controller.request)
    await clients.update()

    assert verify_call(
        mock_aioresponse, "get", "https://host:8443/api/s/default/stat/sta"
    )
    assert len(clients.values()) == 0


test_data = [
    (
        {"mac": "0"},
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
            "sw_depth": None,
            "sw_mac": "",
            "sw_port": None,
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
        WIRELESS_CLIENT,
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
            "sw_depth": -1,
            "sw_mac": "fc:ec:da:11:22:33",
            "sw_port": 1,
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
        WIRED_CLIENT,
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
            "sw_depth": 0,
            "sw_mac": "fc:ec:da:11:22:33",
            "sw_port": 3,
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


@pytest.mark.parametrize("raw_data, reference_data", test_data)
async def test_clients(mock_aioresponse, unifi_controller, raw_data, reference_data):
    """Test clients class."""

    clients = Clients([raw_data], unifi_controller.request)

    assert len(clients.items()) == 1

    client = clients[raw_data["mac"]]
    for key, value in reference_data.items():
        assert getattr(client, key) == value

    mock_aioresponse.post(
        "https://host:8443/api/s/default/cmd/stamgr", payload={}, repeat=True
    )
    await clients.async_block(mac=client.mac)
    assert verify_call(
        mock_aioresponse,
        "post",
        "https://host:8443/api/s/default/cmd/stamgr",
        json={"mac": client.mac, "cmd": "block-sta"},
    )

    await clients.async_unblock(mac=client.mac)
    assert verify_call(
        mock_aioresponse,
        "post",
        "https://host:8443/api/s/default/cmd/stamgr",
        json={"mac": client.mac, "cmd": "unblock-sta"},
    )

    await clients.async_reconnect(mac=client.mac)
    assert verify_call(
        mock_aioresponse,
        "post",
        "https://host:8443/api/s/default/cmd/stamgr",
        json={"mac": client.mac, "cmd": "kick-sta"},
    )

    await clients.remove_clients(macs=[client.mac])
    assert verify_call(
        mock_aioresponse,
        "post",
        "https://host:8443/api/s/default/cmd/stamgr",
        json={"macs": [client.mac], "cmd": "forget-sta"},
    )
