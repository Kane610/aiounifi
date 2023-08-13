"""UniFi sites of network infrastructure."""

from typing import Any

from ..models.message import MessageKey
from ..models.site import Site
from .api_handlers import APIHandler


class Devices(APIHandler[Site]):
    """Represent UniFi sites."""

    obj_id_key = "mac"
    path = "/stat/device"  # sxxxxxxxx
    item_cls = Site
