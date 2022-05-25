"""Clients are devices on a UniFi network."""

from __future__ import annotations

from typing import Final

from ..models.client import Client
from .api import APIItems

URL_ALL: Final = "/rest/user"  # All known and configured clients


class ClientsAll(APIItems):
    """Represents all client network devices."""

    KEY = "mac"
    path = URL_ALL
    item_cls = Client
