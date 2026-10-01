"""Connected clients."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from ....interfaces.api_handlers import ItemEvent
from ..api_handlers import APIHandler
from ..models.client import (
    Client,
    ClientActionRequest,
    ClientActionResponse,
    ClientData,
    GetClientRequest,
    ListClientsRequest,
    normalize_mac,
)

if TYPE_CHECKING:
    from ..api_client import ApiClient


class Clients(APIHandler[Client]):
    """Clients of the active site, keyed by MAC address.

    The console lists connected clients only. A client that disconnects stays
    in the cache with the data it had when last listed, the way the legacy
    API keeps clients it has seen; `is_connected` and `last_seen` tell whether
    and when it was last listed. Subscribers get `CHANGED` when it leaves.
    `forget` drops one for good.

    VPN and Teleport clients have no MAC address, so `update` leaves them out
    of the cache; `list_page` still returns them.
    """

    item_cls = Client
    obj_id_key = "macAddress"

    def __init__(self, api_client: ApiClient) -> None:
        """Initialize."""
        super().__init__(api_client)
        self._last_seen: dict[str, datetime] = {}
        self._connected: set[str] = set()

    def item_missing(self, obj_id: str) -> None:
        """Keep a client that left; `items_listed` tells subscribers."""

    def items_listed(self, obj_ids: set[str]) -> None:
        """Record which clients are connected, and when they were seen.

        Runs before the listed clients are stored and signalled, so a
        subscriber sees `is_connected` as it now is in every callback. A
        client that has dropped off the list is signalled once, from here.
        """
        now = datetime.now(UTC)
        left = self._connected - obj_ids
        self._connected = set(obj_ids)
        for obj_id in obj_ids:
            self._last_seen[obj_id] = now
        for obj_id in left:
            self.signal_subscribers(ItemEvent.CHANGED, obj_id)

    def is_connected(self, mac_address: str) -> bool:
        """Whether the client was listed by the latest `update`."""
        return self.normalize_obj_id(mac_address) in self._connected

    def last_seen(self, mac_address: str) -> datetime | None:
        """When an `update` last listed the client, in UTC."""
        return self._last_seen.get(self.normalize_obj_id(mac_address))

    def restore(self, raw: ClientData, last_seen: datetime | None = None) -> str | None:
        """Put a client seen before this process started into the cache.

        For callers that keep clients across restarts: the console cannot
        list a client that is not connected, so this is the only way it is
        known before it connects again. The client counts as disconnected
        until an `update` lists it. Returns its ID, or `None` without a MAC.
        """
        if (obj_id := self.process_item(dict(raw))) is not None and last_seen:
            self._last_seen[obj_id] = last_seen
        return obj_id

    def forget(self, mac_address: str) -> None:
        """Drop a client from the cache and signal `DELETED`."""
        obj_id = self.normalize_obj_id(mac_address)
        self._last_seen.pop(obj_id, None)
        self._connected.discard(obj_id)
        if self._items.pop(obj_id, None) is not None:
            self.signal_subscribers(ItemEvent.DELETED, obj_id)

    def normalize_obj_id(self, obj_id: str) -> str:
        """Canonical MAC address."""
        return normalize_mac(obj_id)

    def list_request(self, offset: int, limit: int) -> ListClientsRequest:
        """Return the list request for one page."""
        return ListClientsRequest.create(self.api_client.site_id, offset, limit)

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> list[Client]:
        """Return one page of clients without touching the cache."""
        response = await self.api_client.request(
            ListClientsRequest.create(
                self.api_client.site_id, offset, limit, filter_value
            )
        )
        return [Client(raw) for raw in response["data"]]

    async def get_details(self, client_id: str) -> Client:
        """Fetch one client."""
        response = await self.api_client.request(
            GetClientRequest.create(self.api_client.site_id, client_id)
        )
        return Client(response["data"][0])

    async def get_by_mac(self, mac_address: str) -> Client | None:
        """Look a client up by MAC address, filtered on the console."""
        clients = await self.list_page(
            limit=1, filter_value=f"macAddress.eq('{normalize_mac(mac_address)}')"
        )
        return clients[0] if clients else None

    async def authorize_guest_access(
        self,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> ClientActionResponse:
        """Authorize a guest client, with optional time, data and rate limits."""
        response = await self.api_client.request(
            ClientActionRequest.create_authorize_guest_access(
                self.api_client.site_id,
                client_id,
                time_limit_minutes,
                data_usage_limit_mbytes,
                rx_rate_limit_kbps,
                tx_rate_limit_kbps,
            )
        )
        return cast("ClientActionResponse", response["data"][0])

    async def unauthorize_guest_access(self, client_id: str) -> ClientActionResponse:
        """Revoke a guest client's authorization."""
        response = await self.api_client.request(
            ClientActionRequest.create_unauthorize_guest_access(
                self.api_client.site_id, client_id
            )
        )
        return cast("ClientActionResponse", response["data"][0])
