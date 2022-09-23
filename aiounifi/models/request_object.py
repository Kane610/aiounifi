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

    def full_path(self, site: str, is_unifi_os: bool) -> str:
        """Create url to work with a specific controller."""
        if is_unifi_os:
            return f"/proxy/network/api/s/{site}{self.path}"
        return f"/api/s/{site}{self.path}"
