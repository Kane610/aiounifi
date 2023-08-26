"""Test DPI configuration API.

pytest --cov-report term-missing --cov=aiounifi.dpi tests/test_dpi.py
"""
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

from aioresponses import aioresponses
import pytest

from aiounifi.controller import Controller
from aiounifi.models.dpi_restriction_app import DPIRestrictionApp
from aiounifi.models.dpi_restriction_group import DPIRestrictionGroup

from .fixtures import DPI_APPS, DPI_GROUPS


@pytest.mark.parametrize("dpi_app_payload", [DPI_APPS])
async def test_dpi_apps(
    mock_aioresponse: aioresponses,
    unifi_controller: Controller,
    _mock_endpoints: None,
    unifi_called_with: Callable[[str, str, dict[str, Any]], bool],
) -> None:
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
async def test_dpi_groups(unifi_controller: Controller, _mock_endpoints: None) -> None:
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


async def test_dpi_apps_websocket(
    unifi_controller: Controller, _new_ws_data_fn: Callable[[dict[str, Any]], None]
) -> None:
    """Test controller managing devices."""
    unifi_controller.dpi_apps.subscribe(mock_app_callback := Mock())

    # Add DPI app from websocket
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpiapp:add"},
            "data": [
                {
                    "apps": [524292],
                    "blocked": False,
                    "cats": [],
                    "enabled": False,
                    "log": False,
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                    "_id": "61783e89c1773a18c0c61f00",
                }
            ],
        }
    )
    assert len(unifi_controller.dpi_apps.values()) == 1
    assert "61783e89c1773a18c0c61f00" in unifi_controller.dpi_apps

    mock_app_callback.assert_called()
    mock_app_callback.reset_mock()

    # DPI group is enabled with app from websocket
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpiapp:sync"},
            "data": [
                {
                    "_id": "61783e89c1773a18c0c61f00",
                    "apps": [524292],
                    "blocked": False,
                    "cats": [],
                    "enabled": True,
                    "log": False,
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                }
            ],
        }
    )
    dpi_app = unifi_controller.dpi_apps["61783e89c1773a18c0c61f00"]
    assert dpi_app.enabled

    mock_app_callback.assert_called()
    mock_app_callback.reset_mock()

    # Signal removal of app from apps
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpiapp:delete"},
            "data": [
                {
                    "_id": "61783e89c1773a18c0c61f00",
                    "apps": [524292],
                    "blocked": False,
                    "cats": [],
                    "enabled": True,
                    "log": False,
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                }
            ],
        }
    )
    assert len(unifi_controller.dpi_apps.values()) == 0
    assert "61783e89c1773a18c0c61f00" not in unifi_controller.dpi_apps
    mock_app_callback.assert_called()


async def test_dpi_group_websocket(
    unifi_controller: Controller, _new_ws_data_fn: Callable[[dict[str, Any]], None]
) -> None:
    """Test controller managing devices."""
    unifi_controller.dpi_groups.subscribe(mock_group_callback := Mock())

    # Add DPI group from websocket
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpigroup:add"},
            "data": [
                {
                    "name": "dpi group",
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                    "_id": "61783dbdc1773a18c0c61ef6",
                }
            ],
        }
    )
    assert len(unifi_controller.dpi_groups.values()) == 1
    assert "61783dbdc1773a18c0c61ef6" in unifi_controller.dpi_groups

    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    # Update DPI group with app from websocket
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpigroup:sync"},
            "data": [
                {
                    "_id": "61783dbdc1773a18c0c61ef6",
                    "name": "dpi group",
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                    "dpiapp_ids": ["61783e89c1773a18c0c61f00"],
                }
            ],
        }
    )
    dpi_group = unifi_controller.dpi_groups["61783dbdc1773a18c0c61ef6"]
    assert "61783e89c1773a18c0c61f00" in dpi_group.dpiapp_ids

    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    # Signal for group to remove app
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpigroup:sync"},
            "data": [
                {
                    "_id": "61783dbdc1773a18c0c61ef6",
                    "name": "dpi group",
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                    "dpiapp_ids": [],
                }
            ],
        }
    )
    mock_group_callback.assert_called()
    mock_group_callback.reset_mock()

    # Remove group from UniFI controller group from websocket
    _new_ws_data_fn(
        {
            "meta": {"rc": "ok", "message": "dpigroup:delete"},
            "data": [
                {
                    "_id": "61783dbdc1773a18c0c61ef6",
                    "name": "dpi group",
                    "site_id": "5f3edd27ba4cc806a19f2d9c",
                    "dpiapp_ids": [],
                }
            ],
        }
    )
    mock_group_callback.assert_called()
    assert len(unifi_controller.dpi_groups.values()) == 0
    assert "61783dbdc1773a18c0c61ef6" not in unifi_controller.dpi_groups
