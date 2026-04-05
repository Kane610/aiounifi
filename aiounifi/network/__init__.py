"""Versioned UniFi Network API client package."""

from . import v1
from .v1 import Client as NetworkClient

__all__ = ["NetworkClient", "v1"]
