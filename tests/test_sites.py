"""Test client configuration API.

pytest --cov-report term-missing --cov=aiounifi.clients tests/test_clients.py
"""

from aiounifi.controller import Controller


async def test_sites(mock_aioresponse, unifi_controller: Controller, unifi_called_with):
    """Test sites class."""

    sites = unifi_controller.site_handler
    sites.process_raw(
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
    )

    assert len(sites.items()) == 1

    site = sites["5e231c10931eb902acf25112"]

    assert site.site_id == "5e231c10931eb902acf25112"
    assert site.description == "Default"
    assert site.hidden_id == "default"
    assert site.name == "default"
    assert site.no_delete is True
    assert site.role == "admin"
