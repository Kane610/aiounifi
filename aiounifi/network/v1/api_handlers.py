"""API handler base class for UniFi Network API v1."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import ItemsView, Iterator, ValuesView
from typing import TYPE_CHECKING, Any, Generic, final

from ...models.api import ApiItemT
from ...models.subscription import ItemEvent, SubscriptionHandler

if TYPE_CHECKING:
    from .api_client import ApiClient
    from .models.api import ApiRequest


class APIHandler(SubscriptionHandler, Generic[ApiItemT]):
    """Base class for Network API v1 resource interfaces."""

    item_cls: type[ApiItemT]
    obj_id_key: str

    def __init__(self, api_client: ApiClient) -> None:
        """Initialize API handler."""
        super().__init__()
        self.api_client = api_client
        self._items: dict[str, ApiItemT] = {}

    @property
    @abstractmethod
    def api_request(self) -> ApiRequest:
        """Return the API request used to refresh this resource."""

    def normalize_obj_id(self, obj_id: str) -> str:
        """Normalize object IDs used for storage and lookup."""
        return obj_id

    @final
    async def update(self) -> None:
        """Refresh data.

        For site-scoped handlers, ``ApiClient.assign_site()`` must be called
        first so that the site ID is resolved before this method is invoked.
        """
        raw = await self.api_client.request(self.api_request)
        self.process_raw(raw.get("data", []))

    @final
    def process_raw(self, raw: list[dict[str, Any]]) -> None:
        """Process full raw response."""
        for raw_item in raw:
            self.process_item(raw_item)

    @final
    def process_item(self, raw: dict[str, Any]) -> None:
        """Process item data."""
        if self.obj_id_key not in raw:
            return

        obj_id: str
        obj_is_known = (
            obj_id := self.normalize_obj_id(raw[self.obj_id_key])
        ) in self._items
        self._items[obj_id] = self.item_cls(raw)

        self.signal_subscribers(
            ItemEvent.CHANGED if obj_is_known else ItemEvent.ADDED,
            obj_id,
        )

    @final
    def remove_item(self, raw: dict[str, Any]) -> None:
        """Remove item."""
        obj_id: str
        if (obj_id := self.normalize_obj_id(raw[self.obj_id_key])) in self._items:
            self._items.pop(obj_id)
            self.signal_subscribers(ItemEvent.DELETED, obj_id)

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
        return self._items.get(self.normalize_obj_id(obj_id), default)

    @final
    def __contains__(self, obj_id: str) -> bool:
        """Validate membership of item ID."""
        return self.normalize_obj_id(obj_id) in self._items

    @final
    def __getitem__(self, obj_id: str) -> ApiItemT:
        """Get item value based on key."""
        return self._items[self.normalize_obj_id(obj_id)]

    @final
    def __iter__(self) -> Iterator[str]:
        """Allow iterate over items."""
        return iter(self._items)
