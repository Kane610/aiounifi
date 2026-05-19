"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.clients tests/test_clients.py
"""

import pytest

from aiounifi.controller import Controller


@pytest.mark.parametrize(
    "site_payload",
    [
        [
            {
                "_id": "5e231c10931eb902acf25112",
                "name": "default",
                "desc": "Default",
                "attr_hidden_id": "default",
                "attr_no_delete": True,
                "role": "admin",
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_sites(unifi_controller: Controller) -> None:
    """Test sites class."""
    sites = unifi_controller.sites
    await sites.update()
    assert len(sites.items()) == 1

    site = sites["5e231c10931eb902acf25112"]
    assert site.site_id == "5e231c10931eb902acf25112"
    assert site.description == "Default"
    assert site.hidden_id == "default"
    assert site.name == "default"
    assert site.no_delete is True
    assert site.role == "admin"


@pytest.mark.parametrize(
    "site_payload",
    [
        [
            {
                "_id": "5e231c10931eb902acf25112",
                "name": "default",
                "desc": "Default",
                "attr_hidden_id": "default",
                "attr_no_delete": True,
                "role": "admin",
                "external_id": "network-default-uuid",
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_sites_resolve_site_uuid_ignores_surrounding_whitespace(
    unifi_controller: Controller,
) -> None:
    """Verify legacy site UUID resolution trims accidental whitespace."""
    sites = unifi_controller.sites
    await sites.update()

    assert sites.resolve_site_uuid("  default  ") == "network-default-uuid"
