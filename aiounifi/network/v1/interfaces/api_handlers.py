"""Base class of the v1 resource interfaces."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import ItemsView, Iterator, ValuesView
from typing import TYPE_CHECKING, Any, Generic, final

from ....interfaces.api_handlers import ItemEvent, SubscriptionHandler
from ....models.api import ApiItemT
from ..models.api import MAX_PAGE_LIMIT

if TYPE_CHECKING:
    from ..api_client import ApiClient
    from ..models.api import ApiRequest


class APIHandler(SubscriptionHandler, Generic[ApiItemT]):
    """A cache of one resource, kept fresh by polling.

    The v1 API has no websocket, so `update` is the only source of change.
    It walks every page of the list endpoint and then drops every item the
    console no longer lists, signalling `DELETED`, unless `keep_missing` is
    set. `items_listed` is the one hook a subclass may fill in.
    """

    item_cls: type[ApiItemT]
    obj_id_key: str
    keep_missing = False
    """Keep items the console no longer lists instead of dropping them."""

    def __init__(self, api_client: ApiClient) -> None:
        """Initialize."""
        super().__init__()
        self.api_client = api_client
        self._items: dict[str, ApiItemT] = {}

    @abstractmethod
    def list_request(self, offset: int, limit: int) -> ApiRequest:
        """Return the list request for one page."""

    @final
    async def update(self) -> None:
        """Fetch every page and reconcile the cache with it."""
        offset = 0
        listed: list[dict[str, Any]] = []
        while True:
            response = await self.api_client.request(
                self.list_request(offset, MAX_PAGE_LIMIT)
            )
            page = response["data"]
            listed.extend(page)
            offset += len(page)
            if not page or offset >= response.get("totalCount", 0):
                break

        seen = {obj_id for raw in listed if (obj_id := self._obj_id(raw)) is not None}
        self.items_listed(seen)
        for raw in listed:
            self.process_item(raw)
        if self.keep_missing:
            return None
        for obj_id in [obj_id for obj_id in self._items if obj_id not in seen]:
            self._forget(obj_id)

    def items_listed(self, obj_ids: set[str]) -> None:
        """Handle the IDs a completed `update` listed.

        Called before any item is stored or signalled, so what a subclass
        records here is in place when subscribers hear of the changes.
        """
        return None

    @final
    def _forget(self, obj_id: str) -> None:
        """Drop an item from the cache and signal `DELETED`, if it was there."""
        if self._items.pop(obj_id, None) is not None:
            self.signal_subscribers(ItemEvent.DELETED, obj_id)

    @final
    def _obj_id(self, raw: dict[str, Any]) -> str | None:
        """Return the ID of one raw item, or `None` if it has none."""
        return raw.get(self.obj_id_key)

    @final
    def process_item(self, raw: dict[str, Any]) -> str | None:
        """Store one item and tell subscribers. Returns its ID."""
        if (obj_id := self._obj_id(raw)) is None:
            return None
        obj_is_known = obj_id in self._items
        self._items[obj_id] = self.item_cls(raw)
        self.signal_subscribers(
            ItemEvent.CHANGED if obj_is_known else ItemEvent.ADDED, obj_id
        )
        return obj_id

    @final
    def items(self) -> ItemsView[str, ApiItemT]:
        """Return items dictionary."""
        return self._items.items()

    @final
    def values(self) -> ValuesView[ApiItemT]:
        """Return items."""
        return self._items.values()

    @final
    def get(self, obj_id: str, default: Any | None = None) -> ApiItemT | None:
        """Get item value based on key, return default if no match."""
        return self._items.get(obj_id, default)

    @final
    def __contains__(self, obj_id: str) -> bool:
        """Validate membership of item ID."""
        return obj_id in self._items

    @final
    def __getitem__(self, obj_id: str) -> ApiItemT:
        """Get item value based on key."""
        return self._items[obj_id]

    @final
    def __iter__(self) -> Iterator[str]:
        """Allow iterate over items."""
        return iter(self._items)
