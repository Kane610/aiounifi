"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.clients tests/test_clients.py
"""

from asyncio import Future
from asynctest import MagicMock

from aiounifi.clients import Clients

from fixtures import WIRELESS_CLIENT


async def test_no_clients():
    """Test that no clients also work."""
    mock_requests = MagicMock(return_value=Future())
    mock_requests.return_value.set_result("")
    clients = Clients([], mock_requests)
    await clients.update()

    mock_requests.assert_called_once
    assert len(clients.values()) == 0


async def test_clients():
    """Test clients class."""
    mock_requests = MagicMock(return_value=Future())
    mock_requests.return_value.set_result("")
    clients = Clients([WIRELESS_CLIENT], mock_requests)

    assert len(clients.values()) == 1

    client = clients[WIRELESS_CLIENT["mac"]]
    assert client.blocked is False
    assert client.essid == "SSID"
    assert client.hostname == "client"
    assert client.ip == "10.0.0.1"
    assert client.is_guest is False
    assert client.is_wired is False
    assert client.last_seen == 1587765360
    assert client.mac == WIRELESS_CLIENT["mac"]
    assert client.name == "Client 1"
    assert client.oui == "Apple"
    assert client.site_id == "5a32aa4ee4b0412345678910"
    assert client.sw_depth == -1
    assert client.sw_mac == "fc:ec:da:11:22:33"
    assert client.sw_port == 1
    assert client.rx_bytes == 12867114
    assert client.tx_bytes == 52852089
    assert client.uptime == 11904
    assert client.wired_rx_bytes == 0
    assert client.wired_tx_bytes == 0
    assert (
        client.__repr__() == f"<Client Client 1: 00:00:00:00:00:01 {WIRELESS_CLIENT}>"
    )

    await clients.async_block(WIRELESS_CLIENT["mac"])
    mock_requests.assert_called_with(
        "post", "/cmd/stamgr", json={"mac": WIRELESS_CLIENT["mac"], "cmd": "block-sta"}
    )

    await clients.async_unblock(WIRELESS_CLIENT["mac"])
    mock_requests.assert_called_with(
        "post",
        "/cmd/stamgr",
        json={"mac": WIRELESS_CLIENT["mac"], "cmd": "unblock-sta"},
    )
