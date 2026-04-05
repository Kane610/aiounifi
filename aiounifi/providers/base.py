"""Provider contracts for long-lived parallel API implementations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

CapabilityName = str


class DataSource(StrEnum):
    """Stable names for the supported API families."""

    EXTENDED = "extended"
    OFFICIAL = "official"


class RoutingPreference(StrEnum):
    """How downstream clients want a capability resolved."""

    EXTENDED = "extended"
    OFFICIAL = "official"
    PREFER_EXTENDED = "prefer_extended"
    PREFER_OFFICIAL = "prefer_official"
    MERGE = "merge"


class UnsupportedCapabilityError(LookupError):
    """Raised when a capability cannot be resolved for a routing request."""

    def __init__(
        self,
        capability: CapabilityName,
        preference: RoutingPreference,
    ) -> None:
        """Store the failed capability resolution request."""
        super().__init__(
            f"Capability {capability!r} is unsupported for routing {preference.value!r}"
        )
        self.capability = capability
        self.preference = preference


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Capabilities exposed by a single provider implementation."""

    source: DataSource
    supported: frozenset[CapabilityName]

    def supports(self, capability: CapabilityName) -> bool:
        """Return whether this provider exposes the capability."""
        return capability in self.supported


@runtime_checkable
class Provider(Protocol):
    """Protocol implemented by official, extended, and composite providers."""

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return provider capability metadata."""


class CapabilityRegistry:
    """Resolve which provider can satisfy a named capability."""

    def __init__(self, providers: tuple[Provider, ...] = ()) -> None:
        """Initialize the registry with any already-known providers."""
        self._providers: dict[DataSource, ProviderCapabilities] = {}

        for provider in providers:
            self.register(provider)

    def register(self, provider: Provider) -> None:
        """Add or replace a provider definition in the registry."""
        capabilities = provider.capabilities
        self._providers[capabilities.source] = capabilities

    def capabilities_for(self, source: DataSource) -> ProviderCapabilities | None:
        """Return capabilities for a specific source."""
        return self._providers.get(source)

    def supports(self, source: DataSource, capability: CapabilityName) -> bool:
        """Return whether a source supports a capability."""
        if capabilities := self.capabilities_for(source):
            return capabilities.supports(capability)
        return False

    def sources_for(self, capability: CapabilityName) -> tuple[DataSource, ...]:
        """Return all sources that support a capability in stable order."""
        matches = [
            source
            for source in (DataSource.OFFICIAL, DataSource.EXTENDED)
            if self.supports(source, capability)
        ]
        return tuple(matches)

    def resolve(
        self,
        capability: CapabilityName,
        preference: RoutingPreference,
    ) -> tuple[DataSource, ...]:
        """Resolve source selection for a capability and routing preference."""
        if preference is RoutingPreference.OFFICIAL:
            if self.supports(DataSource.OFFICIAL, capability):
                return (DataSource.OFFICIAL,)
            raise UnsupportedCapabilityError(capability, preference)

        if preference is RoutingPreference.EXTENDED:
            if self.supports(DataSource.EXTENDED, capability):
                return (DataSource.EXTENDED,)
            raise UnsupportedCapabilityError(capability, preference)

        if preference is RoutingPreference.PREFER_OFFICIAL:
            for source in (DataSource.OFFICIAL, DataSource.EXTENDED):
                if self.supports(source, capability):
                    return (source,)
            raise UnsupportedCapabilityError(capability, preference)

        if preference is RoutingPreference.PREFER_EXTENDED:
            for source in (DataSource.EXTENDED, DataSource.OFFICIAL):
                if self.supports(source, capability):
                    return (source,)
            raise UnsupportedCapabilityError(capability, preference)

        if sources := self.sources_for(capability):
            return sources
        raise UnsupportedCapabilityError(capability, preference)
