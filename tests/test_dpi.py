"""Test dpi configuration API.

pytest --cov-report term-missing --cov=aiounifi.dpi tests/test_dpi.py
"""

from asyncio import Future
from unittest.mock import AsyncMock

import pytest

from aiounifi.dpi import DPIRestrictionApps, DPIRestrictionApp, DPIRestrictionGroups, DPIRestrictionGroup

from fixtures import DPI_APPS, DPI_GROUPS


@pytest.mark.asyncio
async def test_no_groups():
    """Test that no ports also work."""
    mock_requests = AsyncMock(return_value=Future())
    mock_requests.return_value.set_result("")
    dpi_apps = DPIRestrictionApps([], mock_requests)
    await dpi_apps.update()
    dpi_groups = DPIRestrictionGroups([], mock_requests, dpi_apps)
    await dpi_groups.update()

    assert mock_requests.call_count == 2
    assert len(dpi_apps.values()) == 0
    assert len(dpi_groups.values()) == 0


@pytest.mark.asyncio
async def test_dpi_groups():
    """Test that different types of ports work."""
    mock_requests = AsyncMock(return_value=Future())
    mock_requests.return_value.set_result("")
    dpi_apps = DPIRestrictionApps(DPI_APPS, mock_requests)
    dpi_groups = DPIRestrictionGroups(DPI_GROUPS, mock_requests, dpi_apps)

    assert len(dpi_apps.values()) == 1
    assert len(dpi_groups.values()) == 2

    app: DPIRestrictionApp = dpi_apps["5f976f62e3c58f018ec7e17d"]
    assert app.id == "5f976f62e3c58f018ec7e17d"
    assert app.apps == []
    assert app.blocked
    assert app.cats == ["4"]
    assert app.enabled
    assert app.log
    assert app.site_id == "5ba29dd4e3c58f026e9d7c38"

    group: DPIRestrictionGroup = dpi_groups["5f976f4ae3c58f018ec7dff6"]
    assert group.id == "5f976f4ae3c58f018ec7dff6"
    assert not group.attr_no_delete
    assert group.attr_hidden_id == ""
    assert group.name == "No Media"
    assert group.site_id == "5ba29dd4e3c58f026e9d7c38"
    assert group.dpiapp_ids == ["5f976f62e3c58f018ec7e17d"]

    await dpi_groups.async_enable(group)
    mock_requests.assert_called_with(
        "put", "/rest/dpiapp/5f976f62e3c58f018ec7e17d", json={"enabled": True}
    )

    await dpi_groups.async_disable(group)
    mock_requests.assert_called_with(
        "put", "/rest/dpiapp/5f976f62e3c58f018ec7e17d", json={"enabled": False}
    )
