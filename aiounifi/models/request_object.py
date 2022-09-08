"""Data class for doing UniFi requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RequestObject:
    """Data class with required properties of a request."""

    method: str
    path: str
    data: dict[str, Any]
