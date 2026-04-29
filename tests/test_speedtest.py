"""Test speedtest API."""

from collections.abc import Callable

from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller
from aiounifi.models.speedtest import SpeedtestStatusRequest, SpeedtestTriggerRequest


@pytest.mark.asyncio
async def test_speedtest_status_request(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test speedtest status."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest", payload=[]
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.request(SpeedtestStatusRequest.create())
    assert unifi_called_with("get", "/v2/api/site/default/speedtest")


@pytest.mark.asyncio
async def test_speedtest_trigger_request(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test speedtest trigger."""
    mock_aioresponse.post(
        "https://host:8443/proxy/network/api/s/default/cmd/devmgr/speedtest", payload={}
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.request(SpeedtestTriggerRequest.create())
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr/speedtest")


@pytest.mark.asyncio
async def test_speedtest_handler_update(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test speedtest update."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest",
        payload=[
            {
                "id": "1",
                "interface_name": "eth2",
                "time": 100,
                "download_mbps": 500,
                "upload_mbps": 100,
                "latency_ms": 10,
            },
            {
                "id": "2",
                "interface_name": "eth1",
                "time": 150,
                "download_mbps": 0,
                "upload_mbps": 0,
                "latency_ms": 0,
            },
            {
                "id": "3",
                "interface_name": "eth2",
                "time": 200,
                "download_mbps": 800,
                "upload_mbps": 200,
                "latency_ms": 15,
            },
        ],
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()

    assert len(unifi_controller.speedtest.values()) == 2

    status_eth2 = unifi_controller.speedtest["eth2"]
    assert status_eth2.timestamp == 200
    assert status_eth2.download == 800
    assert status_eth2.upload == 200
    assert status_eth2.ping == 15

    status_eth1 = unifi_controller.speedtest["eth1"]
    assert status_eth1.timestamp == 150
    assert status_eth1.download == 0
    assert status_eth1.upload == 0
    assert status_eth1.ping == 0


@pytest.mark.asyncio
async def test_speedtest_handler_update_unknown(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test speedtest values return unknown when no speeds exist."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest",
        payload=[{"id": "1", "time": 200}],
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()

    status = unifi_controller.speedtest["default"]
    assert status.upload == 0.0
    assert status.download == 0.0


@pytest.mark.asyncio
async def test_speedtest_handler_update_empty(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test speedtest update empty data."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest", payload=[]
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()
    assert len(unifi_controller.speedtest.values()) == 0


@pytest.mark.asyncio
async def test_speedtest_handler_trigger(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test speedtest trigger function."""
    mock_aioresponse.post(
        "https://host:8443/proxy/network/api/s/default/cmd/devmgr/speedtest", payload={}
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.trigger()
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr/speedtest")
