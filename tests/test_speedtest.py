"""Test speedtest API."""

from collections.abc import Callable

from aioresponses import aioresponses
from aiounifi.controller import Controller
from aiounifi.models.speedtest import SpeedtestStatusRequest, SpeedtestTriggerRequest
import pytest


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
                "time": 100,
                "status": "completed",
                "download_mbps": 500,
                "upload_mbps": 100,
                "latency_ms": 10,
            },
            {
                "id": "2",
                "time": 150,
                "status": "failed",
                "download_mbps": 0,
                "upload_mbps": 0,
                "latency_ms": 0,
            },
        ],
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()

    assert len(unifi_controller.speedtest.values()) == 2
    status = unifi_controller.speedtest["2"]
    assert status.timestamp == 150
    assert status.status == "failed"
    assert status.download == 0
    assert status.upload == 0
    assert status.ping == 0


@pytest.mark.asyncio
async def test_speedtest_handler_update_implicit_status(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test speedtest update returns Completed when no explicit status is provided."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest",
        payload=[
            {
                "id": "1",
                "time": 200,
                "download_mbps": 1000,
                "upload_mbps": 500,
                "latency_ms": 20,
            }
        ],
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()

    assert len(unifi_controller.speedtest.values()) == 1
    status = unifi_controller.speedtest["1"]
    assert status.status == "Completed"
    assert status.download == 1000


@pytest.mark.asyncio
async def test_speedtest_handler_update_implicit_unknown(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test speedtest update returns unknown when no speeds exist either."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest",
        payload=[{"id": "1", "time": 200}],
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()

    status = unifi_controller.speedtest["1"]
    assert status.status == "unknown"


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


@pytest.mark.asyncio
async def test_speedtest_handler_update_nested(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test speedtest update with nested data structure."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest",
        payload=[
            {
                "data": [
                    {
                        "id": "1",
                        "time": 300,
                        "status": "completed",
                        "download_mbps": 800,
                        "upload_mbps": 400,
                        "latency_ms": 15,
                    }
                ]
            }
        ],
    )
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.update()

    assert len(unifi_controller.speedtest.values()) == 1
    status = unifi_controller.speedtest["1"]
    assert status.timestamp == 300
    assert status.download == 800
