"""Test speedtest API."""

from collections.abc import Callable
from typing import Any

from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller
from aiounifi.models.speedtest import (
    SpeedtestStatusLegacyRequest,
    SpeedtestStatusRequest,
    SpeedtestTriggerLegacyRequest,
    SpeedtestTriggerRequest,
)


@pytest.mark.asyncio
async def test_speedtest_status_hardware_request(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test hardware speedtest status."""
    mock_aioresponse.get("https://host:8443/proxy/network/v2/api/site/default/speedtest", payload=[])
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.request(SpeedtestStatusRequest.create())
    assert unifi_called_with("get", "/v2/api/site/default/speedtest")


@pytest.mark.asyncio
async def test_speedtest_status_software_request(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test software speedtest status."""
    mock_aioresponse.get("https://host:8443/api/s/default/stat/health", payload={})
    unifi_controller.connectivity.is_unifi_os = False
    await unifi_controller.request(SpeedtestStatusLegacyRequest.create())
    assert unifi_called_with("get", "/api/s/default/stat/health")


@pytest.mark.asyncio
async def test_speedtest_trigger_hardware_request(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test hardware speedtest trigger."""
    mock_aioresponse.post("https://host:8443/proxy/network/api/s/default/cmd/devmgr/speedtest", payload={})
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.request(SpeedtestTriggerRequest.create())
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr/speedtest")


@pytest.mark.asyncio
async def test_speedtest_trigger_software_request(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test software speedtest trigger."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})
    unifi_controller.connectivity.is_unifi_os = False
    await unifi_controller.request(SpeedtestTriggerLegacyRequest.create())
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr", json={"cmd": "speedtest"})


@pytest.mark.asyncio
async def test_speedtest_handler_fetch_hardware(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test hardware speedtest fetch returns most recent."""
    mock_aioresponse.get(
        "https://host:8443/proxy/network/v2/api/site/default/speedtest", 
        payload=[
            {"time": 100, "status": "completed", "download_mbps": 500, "upload_mbps": 100, "latency_ms": 10},
            {"time": 150, "status": "failed", "download_mbps": 0, "upload_mbps": 0, "latency_ms": 0}
        ]
    )
    unifi_controller.connectivity.is_unifi_os = True
    status = await unifi_controller.speedtest.fetch()
    assert status is not None
    assert status.timestamp == 150
    assert status.status == "failed"
    assert status.download == 0
    assert status.upload == 0
    assert status.ping == 0


@pytest.mark.asyncio
async def test_speedtest_handler_fetch_hardware_empty(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test hardware speedtest fetch empty data."""
    mock_aioresponse.get("https://host:8443/proxy/network/v2/api/site/default/speedtest", payload=[])
    unifi_controller.connectivity.is_unifi_os = True
    status = await unifi_controller.speedtest.fetch()
    assert status is None


@pytest.mark.asyncio
async def test_speedtest_handler_fetch_software(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test software speedtest fetch returns www subsystem."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/stat/health", 
        payload={
            "data": [
                {"subsystem": "lan", "status": "ok"},
                {"subsystem": "www", "speedtest_lastrun": 200, "speedtest_status": "completed", "xput_down": 400, "xput_up": 200, "speedtest_ping": 15}
            ]
        }
    )
    unifi_controller.connectivity.is_unifi_os = False
    status = await unifi_controller.speedtest.fetch()
    assert status is not None
    assert status.timestamp == 200
    assert status.status == "completed"
    assert status.download == 400
    assert status.upload == 200
    assert status.ping == 15


@pytest.mark.asyncio
async def test_speedtest_handler_fetch_software_empty(
    mock_aioresponse: aioresponses, unifi_controller: Controller
) -> None:
    """Test software speedtest fetch missing www subsystem."""
    mock_aioresponse.get("https://host:8443/api/s/default/stat/health", payload={"data": [{"subsystem": "lan", "status": "ok"}]})
    unifi_controller.connectivity.is_unifi_os = False
    status = await unifi_controller.speedtest.fetch()
    assert status is None


@pytest.mark.asyncio
async def test_speedtest_handler_trigger_hardware(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test hardware speedtest trigger function."""
    mock_aioresponse.post("https://host:8443/proxy/network/api/s/default/cmd/devmgr/speedtest", payload={})
    unifi_controller.connectivity.is_unifi_os = True
    await unifi_controller.speedtest.trigger()
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr/speedtest")


@pytest.mark.asyncio
async def test_speedtest_handler_trigger_software(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    unifi_called_with: Callable[..., bool],
) -> None:
    """Test software speedtest trigger function."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/devmgr", payload={})
    unifi_controller.connectivity.is_unifi_os = False
    await unifi_controller.speedtest.trigger()
    assert unifi_called_with("post", "/api/s/default/cmd/devmgr", json={"cmd": "speedtest"})
