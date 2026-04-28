"""Versioned UniFi Network API client package."""

from . import v1
from .v1 import ApiClient

__all__ = ["ApiClient", "v1"]
