"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

from __future__ import annotations

from typing import Final

from ..models.device import Device
from .api import APIItems

URL: Final = "/stat/device"


class Devices(APIItems):
    """Represents network devices."""

    KEY = "mac"
    path = URL
    item_cls = Device
