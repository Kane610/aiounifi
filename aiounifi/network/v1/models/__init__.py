"""Models used by UniFi Network API interfaces."""

from .api import ApiErrorResponse, ApiRequest, ApiResponse
from .client import (
    Access,
    Client,
    ClientData,
    ClientOverviewData,
    ExecuteClientActionRequest,
    ExecuteClientActionResponse,
    GetClientDetailsRequest,
    GuestAuthorizationDetails,
    ListClientsRequest,
    Usage,
)
from .site import Site, SiteData, SitesRequest

__all__ = [
    "Access",
    "ApiErrorResponse",
    "ApiRequest",
    "ApiResponse",
    "Client",
    "ClientData",
    "ClientOverviewData",
    "ExecuteClientActionRequest",
    "ExecuteClientActionResponse",
    "GetClientDetailsRequest",
    "GuestAuthorizationDetails",
    "ListClientsRequest",
    "Site",
    "SiteData",
    "SitesRequest",
    "Usage",
]
