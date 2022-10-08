"""Clients are devices on a UniFi network."""

from __future__ import annotations

from typing import Final

from ..models.client import Client
from .api_handlers import APIHandler

URL_ALL: Final = "/rest/user"  # All known and configured clients


class ClientsAll(APIHandler[Client]):
    """Represents all client network devices."""

    obj_id_key = "mac"
    path = URL_ALL
    item_cls = Client
