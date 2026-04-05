"""Provider abstractions for parallel UniFi API backends."""

from .base import (
    CapabilityName,
    CapabilityRegistry,
    DataSource,
    Provider,
    ProviderCapabilities,
    RoutingPreference,
    UnsupportedCapabilityError,
)

__all__ = [
    "CapabilityName",
    "CapabilityRegistry",
    "DataSource",
    "Provider",
    "ProviderCapabilities",
    "RoutingPreference",
    "UnsupportedCapabilityError",
]
