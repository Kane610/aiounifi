"""Models used by UniFi Network API interfaces."""

from .api import ApiErrorResponse, ApiRequest, ApiResponse
from .client import (
    Access,
    Client,
    ClientDetailData,
    ClientSummaryData,
    ExecuteClientActionRequest,
    ExecuteClientActionResponse,
    GetClientDetailsRequest,
    GuestAuthorizationDetails,
    ListClientsRequest,
    Usage,
    normalize_mac,
)
from .site import Site, SiteData, SitesRequest

__all__ = [
    "Access",
    "ApiErrorResponse",
    "ApiRequest",
    "ApiResponse",
    "Client",
    "ClientDetailData",
    "ClientSummaryData",
    "ExecuteClientActionRequest",
    "ExecuteClientActionResponse",
    "GetClientDetailsRequest",
    "GuestAuthorizationDetails",
    "ListClientsRequest",
    "normalize_mac",
    "Site",
    "SiteData",
    "SitesRequest",
    "Usage",
]
