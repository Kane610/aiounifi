"""Test dpi configuration API.

pytest --cov-report term-missing --cov=aiounifi.dpi tests/test_dpi.py
"""

from asyncio import Future
from unittest.mock import AsyncMock

import pytest

from aiounifi.dpi import DPIRestrictionGroups, DPIRestrictionGroup

from fixtures import DPI_GROUPS


@pytest.mark.asyncio
async def test_no_groups():
    """Test that no ports also work."""
    mock_requests = AsyncMock(return_value=Future())
    mock_requests.return_value.set_result("")
    dpi_groups = DPIRestrictionGroups([], mock_requests)
    await dpi_groups.update()

    mock_requests.assert_called_once
    assert len(dpi_groups.values()) == 0


@pytest.mark.asyncio
async def test_dpi_groups():
    """Test that different types of ports work."""
    mock_requests = AsyncMock(return_value=Future())
    mock_requests.return_value.set_result("")
    dpi_groups = DPIRestrictionGroups(DPI_GROUPS, mock_requests)

    assert len(dpi_groups.values()) == 2

    group: DPIRestrictionGroup = dpi_groups["No Media"]
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
