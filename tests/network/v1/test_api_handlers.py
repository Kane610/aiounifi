"""Test paging and reconciliation of the v1 handler base."""

from unittest.mock import Mock

from aiounifi.interfaces.api_handlers import ItemEvent
from aiounifi.network.v1.api_client import ApiClient

from .conftest import envelope, requests_to, url_pattern

SITE_A = {"id": "a", "internalReference": "default", "name": "A"}
SITE_B = {"id": "b", "internalReference": "b", "name": "B"}
SITE_C = {"id": "c", "internalReference": "c", "name": "C"}


async def test_update_walks_every_page(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """Pages are requested until totalCount is reached, 200 at a time."""
    mock_aioresponse.get(
        url_pattern("/v1/sites"),
        payload=envelope([SITE_A, SITE_B], limit=200, totalCount=3),
    )
    mock_aioresponse.get(
        url_pattern("/v1/sites"),
        payload=envelope([SITE_C], offset=2, limit=200, totalCount=3),
    )

    await network_client.sites.update()

    assert list(network_client.sites) == ["a", "b", "c"]
    calls = requests_to(mock_aioresponse, "get", "/v1/sites")
    assert [call.kwargs["params"] for call in calls] == [
        {"offset": 0, "limit": 200},
        {"offset": 2, "limit": 200},
    ]


async def test_update_stops_on_empty_page(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """A console that over-reports totalCount cannot cause an endless loop."""
    mock_aioresponse.get(
        url_pattern("/v1/sites"), payload=envelope([SITE_A], totalCount=5)
    )
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope([], totalCount=5))

    await network_client.sites.update()

    assert list(network_client.sites) == ["a"]


async def test_update_signals_added_changed_deleted(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """Subscribers learn about every change, including items that vanish."""
    callback = Mock()
    network_client.sites.subscribe(callback)
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope([SITE_A, SITE_B]))
    mock_aioresponse.get(
        url_pattern("/v1/sites"), payload=envelope([SITE_A | {"name": "A2"}, SITE_C])
    )

    await network_client.sites.update()
    await network_client.sites.update()

    assert callback.call_args_list == [
        ((ItemEvent.ADDED, "a"),),
        ((ItemEvent.ADDED, "b"),),
        ((ItemEvent.CHANGED, "a"),),
        ((ItemEvent.ADDED, "c"),),
        ((ItemEvent.DELETED, "b"),),
    ]
    assert "b" not in network_client.sites
    assert network_client.sites["a"].name == "A2"
    assert network_client.sites.get("b") is None
    assert [site.site_id for site in network_client.sites.values()] == ["a", "c"]
    assert dict(network_client.sites.items()).keys() == {"a", "c"}


async def test_items_without_id_are_skipped(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """A malformed item does not poison the cache."""
    mock_aioresponse.get(
        url_pattern("/v1/sites"), payload=envelope([{"name": "no id"}, SITE_A])
    )

    await network_client.sites.update()

    assert list(network_client.sites) == ["a"]
