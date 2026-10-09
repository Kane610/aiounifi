"""Models of the Network API v1."""

from .api import ApiErrorResponse, ApiRequest, ApiResponse
from .client import Client, ClientAccessType, ClientData, ClientType
from .device import (
    Device,
    DeviceData,
    DeviceFeature,
    DevicePort,
    DevicePortConnector,
    DevicePortPoeStandard,
    DevicePortPoeState,
    DevicePortState,
    DeviceRadio,
    DeviceRadioWlanStandard,
    DeviceState,
    DeviceStatistics,
)
from .info import InfoData
from .site import Site, SiteData

__all__ = [
    "ApiErrorResponse",
    "ApiRequest",
    "ApiResponse",
    "Client",
    "ClientAccessType",
    "ClientData",
    "ClientType",
    "Device",
    "DeviceData",
    "DeviceFeature",
    "DevicePort",
    "DevicePortConnector",
    "DevicePortPoeStandard",
    "DevicePortPoeState",
    "DevicePortState",
    "DeviceRadio",
    "DeviceRadioWlanStandard",
    "DeviceState",
    "DeviceStatistics",
    "InfoData",
    "Site",
    "SiteData",
]
