"""Test DPI configuration API.

pytest --cov-report term-missing --cov=aiounifi.dpi tests/test_dpi.py
"""

import pytest

from aiounifi.models.dpi_restriction_app import DPIRestrictionApp
from aiounifi.models.dpi_restriction_group import DPIRestrictionGroup

from .fixtures import DPI_APPS, DPI_GROUPS


async def test_no_apps(
    mock_aioresponse, unifi_controller, mock_endpoints, unifi_called_with
):
    """Test that dpi_apps work without data."""
    dpi_apps = unifi_controller.dpi_apps
    await dpi_apps.update()

    assert unifi_called_with("get", "/api/s/default/rest/dpiapp")
    assert len(dpi_apps.values()) == 0


async def test_no_groups(
    mock_aioresponse, unifi_controller, mock_endpoints, unifi_called_with
):
    """Test that dpi_groups work without data."""
    dpi_groups = unifi_controller.dpi_groups
    await dpi_groups.update()

    assert unifi_called_with("get", "/api/s/default/rest/dpigroup")
    assert len(dpi_groups.values()) == 0


@pytest.mark.parametrize("dpi_app_payload", [DPI_APPS])
async def test_dpi_apps(
    mock_aioresponse, unifi_controller, mock_endpoints, unifi_called_with
):
    """Test that dpi_apps can create an app."""
    dpi_apps = unifi_controller.dpi_apps
    await dpi_apps.update()
    assert len(dpi_apps.values()) == 1

    app: DPIRestrictionApp = dpi_apps["5f976f62e3c58f018ec7e17d"]
    assert app.id == "5f976f62e3c58f018ec7e17d"
    assert app.apps == []
    assert app.blocked
    assert app.cats == ["4"]
    assert app.enabled
    assert app.log
    assert app.site_id == "5ba29dd4e3c58f026e9d7c38"

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/dpiapp/5f976f62e3c58f018ec7e17d",
        payload={},
        repeat=True,
    )
    await dpi_apps.enable("5f976f62e3c58f018ec7e17d")
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/dpiapp/5f976f62e3c58f018ec7e17d",
        json={"enabled": True},
    )

    await dpi_apps.disable("5f976f62e3c58f018ec7e17d")
    assert unifi_called_with(
        "put",
        "/api/s/default/rest/dpiapp/5f976f62e3c58f018ec7e17d",
        json={"enabled": False},
    )


@pytest.mark.parametrize("dpi_group_payload", [DPI_GROUPS])
async def test_dpi_groups(mock_aioresponse, unifi_controller, mock_endpoints):
    """Test that dpi_groups can create a group."""
    dpi_groups = unifi_controller.dpi_groups
    await dpi_groups.update()
    assert len(dpi_groups.values()) == 2

    group: DPIRestrictionGroup = dpi_groups["5f976f4ae3c58f018ec7dff6"]
    assert group.id == "5f976f4ae3c58f018ec7dff6"
    assert not group.attr_no_delete
    assert group.attr_hidden_id == ""
    assert group.name == "No Media"
    assert group.site_id == "5ba29dd4e3c58f026e9d7c38"
    assert group.dpiapp_ids == ["5f976f62e3c58f018ec7e17d"]
