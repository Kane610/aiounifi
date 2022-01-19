"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.clients tests/test_clients.py
"""

from aiounifi.clients import Clients

from .fixtures import WIRELESS_CLIENT
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


async def test_clients(mock_aioresponse, unifi_controller):
    """Test clients class."""

    clients = Clients([WIRELESS_CLIENT], unifi_controller.request)

    assert len(clients.values()) == 1

    client = clients[WIRELESS_CLIENT["mac"]]
    assert client.access_point_mac == "80:2a:a8:00:01:02"
    assert client.association_time == 1587753456
    assert client.blocked is False
    assert client.device_name == "Discovery device name"
    assert client.essid == "SSID"
    assert client.firmware_version == ""
    assert client.first_seen == 1513271497
    assert client.fixed_ip == "192.168.0.1"
    assert client.hostname == "client"
    assert client.idle_time == 1
    assert client.ip == "192.168.0.1"
    assert client.is_guest is False
    assert client.is_wired is False
    assert client.last_seen == 1587765360
    assert client.last_seen_by_access_point == 1587765360
    assert client.last_seen_by_gateway == 1587765372
    assert client.last_seen_by_switch == 1587763868
    assert client.latest_association_time == 1587765354
    assert client.mac == WIRELESS_CLIENT["mac"]
    assert client.name == "Client 1"
    assert client.oui == "Apple"
    assert client.powersave_enabled is False
    assert client.site_id == "5a32aa4ee4b0412345678910"
    assert client.sw_depth == -1
    assert client.sw_mac == "fc:ec:da:11:22:33"
    assert client.sw_port == 1
    assert client.rx_bytes == 12867114
    assert client.rx_bytes_r == 326
    assert client.tx_bytes == 52852089
    assert client.tx_bytes_r == 483
    assert client.uptime == 11904
    assert client.uptime_by_access_point == 11904
    assert client.uptime_by_gateway == 18
    assert client.uptime_by_switch == 318
    assert client.latest_association_time == 1587765354
    assert client.wired_rate_mbps == 0
    assert client.wired_rx_bytes == 0
    assert client.wired_rx_bytes_r == 0
    assert client.wired_tx_bytes == 0
    assert client.wired_tx_bytes_r == 0
    assert (
        client.__repr__() == f"<Client Client 1: 00:00:00:00:00:01 {WIRELESS_CLIENT}>"
    )

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
