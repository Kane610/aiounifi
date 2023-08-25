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
async def test_sites(unifi_controller: Controller, _mock_endpoints: None) -> None:
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
