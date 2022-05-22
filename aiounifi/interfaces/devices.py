"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from typing import Final

from ..models.device import Device
from .api import APIItems

LOGGER = logging.getLogger(__name__)

URL: Final = "/stat/device"


class Devices(APIItems):
    """Represents network devices."""

    KEY = "mac"

    def __init__(
        self,
        raw: list[dict],
        request: Callable[..., Awaitable[list[dict]]],
    ) -> None:
        """Initialize device manager."""
        super().__init__(raw, request, URL, Device)
