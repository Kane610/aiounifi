"""Models used by UniFi Network API interfaces."""

from .api import ApiRequest, ApiResponse
from .site import Site, SitesRequest

__all__ = [
    "ApiRequest",
    "ApiResponse",
    "Site",
    "SitesRequest",
]
