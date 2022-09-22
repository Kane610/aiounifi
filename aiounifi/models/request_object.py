"""Data class for doing UniFi requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RequestObject:
    """Data class with required properties of a request."""

    method: str
    path: str
    data: dict[str, Any] | None

    def generate_url(self, url: str, site: str, is_unifi_os: bool) -> str:
        """Create url to work with a specific controller."""
        if is_unifi_os:
            url = f"{url}/proxy/network"
        return f"{url}/api/s/{site}{self.path}"
