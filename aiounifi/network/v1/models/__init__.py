"""Models used by UniFi Network API interfaces."""

from .api import ApiErrorResponse, ApiRequest, ApiResponse
from .site import Site, SiteData, SitesRequest

__all__ = [
    "ApiErrorResponse",
    "ApiRequest",
    "ApiResponse",
    "Site",
    "SiteData",
    "SitesRequest",
]
