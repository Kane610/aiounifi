"""Tests for Network API v1 APIHandler base class methods."""

from __future__ import annotations

from unittest.mock import AsyncMock

from aiounifi.network.v1.api_client import ApiClient
from aiounifi.network.v1.interfaces.clients import ListClientsRequest
from aiounifi.network.v1.models.site import SitesRequest
from aiounifi.subscription import ItemEvent

# ---------------------------------------------------------------------------
# update() — exercising lines 41-42, 47-48 and the api_request property (line 23)
# ---------------------------------------------------------------------------


async def test_api_handler_update_populates_items(network_client: ApiClient) -> None:
    """Verify update() fetches data and populates the handler's item store."""
    raw_response = {
        "offset": 0,
        "limit": 25,
        "count": 2,
        "totalCount": 2,
        "data": [
            {"id": "site-a", "internalReference": "ref-a", "name": "Alpha"},
            {"id": "site-b", "internalReference": "ref-b", "name": "Beta"},
        ],
    }
    network_client.sites.api_client.request = AsyncMock(return_value=raw_response)

    await network_client.sites.update()

    assert "site-a" in network_client.sites
    assert "site-b" in network_client.sites


# ---------------------------------------------------------------------------
# api_request property — line 23 (sites) and line 29 (clients)
# ---------------------------------------------------------------------------


def test_sites_api_request_property(network_client: ApiClient) -> None:
    """Verify Sites.api_request returns a SitesRequest."""
    req = network_client.sites.api_request
    assert isinstance(req, SitesRequest)


def test_clients_api_request_property(
    network_client_with_site: ApiClient,
) -> None:
    """Verify Clients.api_request returns a request scoped to the active site."""
    req = network_client_with_site.clients.api_request
    assert isinstance(req, ListClientsRequest)
    assert network_client_with_site.site_id in req.path


# ---------------------------------------------------------------------------
# process_item — line 54 (early return when obj_id_key missing)
# ---------------------------------------------------------------------------


def test_api_handler_process_item_ignores_missing_key(
    network_client: ApiClient,
) -> None:
    """Verify process_item silently skips items without the expected ID key."""
    network_client.sites.process_item({"name": "No ID here"})

    assert list(network_client.sites) == []


# ---------------------------------------------------------------------------
# ADDED / CHANGED events
# ---------------------------------------------------------------------------


def test_api_handler_process_item_added_event(network_client: ApiClient) -> None:
    """Verify ADDED event is signalled for a new item."""
    received: list[tuple[ItemEvent, str]] = []
    network_client.sites.subscribe(lambda event, key: received.append((event, key)))

    network_client.sites.process_item(
        {"id": "site-x", "internalReference": "ref-x", "name": "X"}
    )

    assert received == [(ItemEvent.ADDED, "site-x")]


def test_api_handler_process_item_changed_event(network_client: ApiClient) -> None:
    """Verify CHANGED event is signalled when an existing item is updated."""
    network_client.sites.process_item(
        {"id": "site-x", "internalReference": "ref-x", "name": "X"}
    )

    received: list[tuple[ItemEvent, str]] = []
    network_client.sites.subscribe(lambda event, key: received.append((event, key)))

    network_client.sites.process_item(
        {"id": "site-x", "internalReference": "ref-x", "name": "X Updated"}
    )

    assert received == [(ItemEvent.CHANGED, "site-x")]


# ---------------------------------------------------------------------------
# remove_item — lines 69-71
# ---------------------------------------------------------------------------


def test_api_handler_remove_item(network_client: ApiClient) -> None:
    """Verify remove_item removes an item and signals DELETED."""
    network_client.sites.process_item(
        {"id": "site-r", "internalReference": "ref-r", "name": "Remove Me"}
    )
    assert "site-r" in network_client.sites

    received: list[tuple[ItemEvent, str]] = []
    network_client.sites.subscribe(lambda event, key: received.append((event, key)))

    network_client.sites.remove_item({"id": "site-r"})

    assert "site-r" not in network_client.sites
    assert received == [(ItemEvent.DELETED, "site-r")]


def test_api_handler_remove_item_noop_for_unknown(network_client: ApiClient) -> None:
    """Verify remove_item is a no-op for items that are not in the store."""
    network_client.sites.remove_item({"id": "ghost"})  # should not raise


# ---------------------------------------------------------------------------
# Collection accessors — lines 76, 86, 91, 96, 101
# ---------------------------------------------------------------------------


def test_api_handler_collection_accessors(network_client: ApiClient) -> None:
    """Verify items(), values(), get(), __contains__, __getitem__, __iter__."""
    raw = {"id": "site-1", "internalReference": "ref-1", "name": "One"}
    network_client.sites.process_item(raw)

    # items() — line 76
    assert ("site-1", network_client.sites["site-1"]) in list(
        network_client.sites.items()
    )

    # values() — not a missing line, but verify it works too
    assert network_client.sites["site-1"] in list(network_client.sites.values())

    # get() — line 86
    assert network_client.sites.get("site-1") is not None
    assert network_client.sites.get("missing", None) is None

    # __contains__ — line 91
    assert "site-1" in network_client.sites
    assert "missing" not in network_client.sites

    # __getitem__ — line 96
    item = network_client.sites["site-1"]
    assert item.name == "One"

    # __iter__ — line 101
    keys = list(network_client.sites)
    assert keys == ["site-1"]
