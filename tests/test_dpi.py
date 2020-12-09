"""Test dpi configuration API.

pytest --cov-report term-missing --cov=aiounifi.dpi tests/test_dpi.py
"""

import pytest
from yarl import URL

from aiounifi.dpi import (
    DPIRestrictionApps,
    DPIRestrictionApp,
    DPIRestrictionGroups,
    DPIRestrictionGroup,
)

from fixtures import DPI_APPS, DPI_GROUPS


def verify_call(
    aioresponse: tuple, method: str, url: str, expected_json_payload: dict = None
) -> bool:
    for req, call_list in aioresponse.requests.items():

        if req != (method, URL(url)):
            continue

        for call in call_list:
            if call[1].get("json") == expected_json_payload:
                return True

    return False


@pytest.mark.asyncio
async def test_no_groups(mock_aioresponse, unifi_controller):
    """Test that no ports also work."""
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpiapp", payload={},
    )
    mock_aioresponse.get(
        "https://host:8443/api/s/default/rest/dpigroup", payload={},
    )

    dpi_apps = DPIRestrictionApps([], unifi_controller.request)
    await dpi_apps.update()

    dpi_groups = DPIRestrictionGroups([], unifi_controller.request, dpi_apps)
    await dpi_groups.update()

    assert verify_call(
        mock_aioresponse, "get", "https://host:8443/api/s/default/rest/dpiapp"
    )
    assert verify_call(
        mock_aioresponse, "get", "https://host:8443/api/s/default/rest/dpigroup"
    )

    assert len(dpi_apps.values()) == 0
    assert len(dpi_groups.values()) == 0


@pytest.mark.asyncio
async def test_dpi_groups(mock_aioresponse, unifi_controller):
    """Test that different types of ports work."""
    dpi_apps = DPIRestrictionApps(DPI_APPS, unifi_controller.request)
    dpi_groups = DPIRestrictionGroups(DPI_GROUPS, unifi_controller.request, dpi_apps)

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

    mock_aioresponse.put(
        "https://host:8443/api/s/default/rest/dpiapp/5f976f62e3c58f018ec7e17d",
        payload={},
        repeat=True,
    )
    await dpi_groups.async_enable(group)
    assert verify_call(
        mock_aioresponse,
        "put",
        "https://host:8443/api/s/default/rest/dpiapp/5f976f62e3c58f018ec7e17d",
        {"enabled": True},
    )

    await dpi_groups.async_disable(group)
    assert verify_call(
        mock_aioresponse,
        "put",
        "https://host:8443/api/s/default/rest/dpiapp/5f976f62e3c58f018ec7e17d",
        {"enabled": False},
    )
