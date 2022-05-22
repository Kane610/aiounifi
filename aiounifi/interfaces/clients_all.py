"""Clients are devices on a UniFi network."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Final

from .api import APIItems
from ..models.client import Client

URL_ALL: Final = "/rest/user"  # All known and configured clients


class ClientsAll(APIItems):
    """Represents all client network devices."""

    KEY = "mac"

    def __init__(
        self,
        raw: list[dict],
        request: Callable[..., Awaitable[list[dict]]],
    ) -> None:
        """Initialize all clients manager."""
        super().__init__(raw, request, URL_ALL, Client)
