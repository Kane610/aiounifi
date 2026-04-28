"""Tests for Network API v1 ApiClient."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from aiounifi.errors import RequestError
from aiounifi.network.v1.api_client import ApiClient


def test_site_id_raises_when_not_set(network_client: ApiClient) -> None:
    """Verify site_id raises RequestError when no site has been assigned."""
    assert network_client._site_id is None
    with pytest.raises(RequestError, match="not set"):
        _ = network_client.site_id


async def test_assign_site_fast_path(network_client: ApiClient) -> None:
    """Verify assign_site returns immediately when _site_id is already resolved."""
    network_client._site_id = "cached-uuid"

    result = await network_client.assign_site("any-site")

    assert result == "cached-uuid"


async def test_assign_site_piggyback_path(network_client: ApiClient) -> None:
    """Verify concurrent callers piggyback on an in-flight resolution task."""
    event = asyncio.Event()

    async def slow_resolver() -> None:
        await event.wait()
        network_client._site_id = "resolved-uuid"

    # Inject an in-flight task simulating a concurrent first caller.
    network_client._site_task = asyncio.create_task(slow_resolver())
    piggyback_task = asyncio.create_task(network_client.assign_site("x"))

    # Yield so both tasks can start: slow_resolver suspends on event,
    # assign_site sees _site_task is not None and suspends on it (lines 61-62).
    await asyncio.sleep(0)

    # Unblock the in-flight resolver so both tasks can complete.
    event.set()
    result = await piggyback_task

    assert result == "resolved-uuid"


async def test_assign_site_raises_when_resolution_fails(
    network_client: ApiClient,
) -> None:
    """Verify assign_site propagates RequestError when all resolution steps fail."""
    # All resolution steps return falsy/empty without a network hit.
    network_client.controller.sites.resolve_site_uuid = lambda _: None
    network_client.sites.list_page = AsyncMock(return_value=[])

    with pytest.raises(RequestError, match="Could not resolve"):
        await network_client.assign_site("unknown-site")
