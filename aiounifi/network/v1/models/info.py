"""Application information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .api import ApiRequest


class InfoData(TypedDict):
    """Payload of GET /v1/info."""

    applicationVersion: str


@dataclass
class InfoRequest(ApiRequest):
    """Request the Network application version.

    The cheapest authenticated call there is, so it doubles as a credential
    check.
    """

    @classmethod
    def create(cls) -> InfoRequest:
        """Create the request."""
        return cls(method="get", path="/v1/info")
