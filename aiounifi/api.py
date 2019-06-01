import logging

from pprint import pformat

LOGGER = logging.getLogger(__name__)


class APIItems:
    """Base class for a map of API Items."""

    def __init__(self, raw, request, path, item_cls):
        self._request = request
        self._path = path
        self._item_cls = item_cls
        self._items = {}
        self.process_raw(raw)
        LOGGER.debug(pformat(raw))

    async def update(self):
        raw = await self._request('get', self._path)
        self.process_raw(raw)

    def process_raw(self, raw):
        for raw_item in raw:
            mac = raw_item['mac']
            obj = self._items.get(mac)

            if obj is not None:
                obj.raw = raw_item
            else:
                self._items[mac] = self._item_cls(raw_item, self._request)

    def values(self):
        return self._items.values()

    def __getitem__(self, obj_id):
        try:
            return self._items[obj_id]
        except KeyError:
            LOGGER.error("Couldn't find key: '{}'".format(obj_id))

    def __iter__(self):
        return iter(self._items)
