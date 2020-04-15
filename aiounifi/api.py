import logging

from pprint import pformat

from .events import event as event_class

LOGGER = logging.getLogger(__name__)

SOURCE_DATA = "data"
SOURCE_EVENT = "event"


class APIItems:
    """Base class for a map of API Items."""

    KEY = None

    def __init__(self, raw, request, path, item_cls):
        self._request = request
        self._path = path
        self._item_cls = item_cls
        self._items = {}
        self.process_raw(raw)
        LOGGER.debug(pformat(raw))

    async def update(self):
        raw = await self._request("get", self._path)
        self.process_raw(raw)

    def process_raw(self, raw: list) -> set:
        new_items = set()

        for raw_item in raw:
            key = raw_item[self.KEY]
            obj = self._items.get(key)

            if obj is not None:
                obj.update(raw=raw_item)
            else:
                self._items[key] = self._item_cls(raw_item, self._request)
                new_items.add(key)

        return new_items

    def process_event(self, events: list) -> set:
        new_items = set()

        for raw_event in events:
            event = event_class(raw_event)
            obj = self._items.get(event.mac)

            if obj is not None:
                obj.update(event=event)
                new_items.add(event.mac)

        return new_items

    def remove(self, raw: list) -> set:
        removed_items = set()

        for raw_item in raw:
            key = raw_item[self.KEY]

            if key in self._items:
                self._items.pop(key)
                removed_items.add(key)

        return removed_items

    def values(self):
        return self._items.values()

    def __getitem__(self, obj_id):
        try:
            return self._items[obj_id]
        except KeyError:
            LOGGER.error(f"Couldn't find key: {obj_id}")

    def __iter__(self):
        return iter(self._items)


class APIItem:
    def __init__(self, raw, request):
        self._raw = raw
        self._request = request
        self._event = None
        self._source = SOURCE_DATA
        self._callbacks = []

    @property
    def raw(self) -> dict:
        """Read only raw data."""
        return self._raw

    @property
    def event(self) -> dict:
        """Read only event data."""
        return self._event

    @property
    def last_updated(self) -> str:
        """Which source, data or event last called update."""
        return self._source

    def update(self, raw=None, event=None) -> None:
        """Update raw data and signal new data is available."""
        if raw:
            self._raw = raw
            self._source = SOURCE_DATA

        elif event:
            self._event = event
            self._source = SOURCE_EVENT

        else:
            return

        for signal_update in self._callbacks:
            signal_update()

    def register_callback(self, callback) -> None:
        """Register callback for signalling.

        Callback will be used by update.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback) -> None:
        """Remove all registered callbacks."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
