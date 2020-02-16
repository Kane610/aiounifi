import logging

from pprint import pformat

LOGGER = logging.getLogger(__name__)


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

    def process_raw(self, raw):
        new_items = set()

        for raw_item in raw:
            key = raw_item[self.KEY]
            obj = self._items.get(key)

            if obj is not None:
                obj.update(raw_item)
            else:
                self._items[key] = self._item_cls(raw_item, self._request)
                new_items.add(key)

        return new_items

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
        self._callbacks = []

    @property
    def raw(self):
        """Read only raw data."""
        return self._raw

    def update(self, raw):
        """Update raw data and signal new data is available."""
        self._raw = raw
        for signal_update in self._callbacks:
            signal_update()

    def register_callback(self, callback):
        """Register callback for signalling.

        Callback will be used by update.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback):
        """Remove all registered callbacks."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
