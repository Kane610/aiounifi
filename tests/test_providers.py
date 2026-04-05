"""Tests for provider capability routing."""

import pytest

from aiounifi.providers import (
    CapabilityRegistry,
    DataSource,
    ProviderCapabilities,
    RoutingPreference,
    UnsupportedCapabilityError,
)


class StubProvider:
    """Simple provider stub for registry tests."""

    def __init__(self, capabilities: ProviderCapabilities) -> None:
        """Store provider capabilities."""
        self._capabilities = capabilities

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return self._capabilities


def test_capability_registry_support_lookup() -> None:
    """Verify support lookups honor both provider sources."""
    registry = CapabilityRegistry(
        (
            StubProvider(
                ProviderCapabilities(
                    source=DataSource.EXTENDED,
                    supported=frozenset({"devices.list", "ports.set_poe_mode"}),
                )
            ),
            StubProvider(
                ProviderCapabilities(
                    source=DataSource.OFFICIAL,
                    supported=frozenset({"devices.list"}),
                )
            ),
        )
    )

    assert registry.supports(DataSource.EXTENDED, "ports.set_poe_mode")
    assert registry.supports(DataSource.OFFICIAL, "devices.list")
    assert not registry.supports(DataSource.OFFICIAL, "ports.set_poe_mode")
    assert registry.sources_for("devices.list") == (
        DataSource.OFFICIAL,
        DataSource.EXTENDED,
    )


def test_capability_registry_prefer_official() -> None:
    """Verify prefer-official resolves to the official provider when possible."""
    registry = CapabilityRegistry(
        (
            StubProvider(
                ProviderCapabilities(
                    source=DataSource.EXTENDED,
                    supported=frozenset({"devices.list", "devices.restart"}),
                )
            ),
            StubProvider(
                ProviderCapabilities(
                    source=DataSource.OFFICIAL,
                    supported=frozenset({"devices.list"}),
                )
            ),
        )
    )

    assert registry.resolve("devices.list", RoutingPreference.PREFER_OFFICIAL) == (
        DataSource.OFFICIAL,
    )
    assert registry.resolve("devices.restart", RoutingPreference.PREFER_OFFICIAL) == (
        DataSource.EXTENDED,
    )


def test_capability_registry_merge() -> None:
    """Verify merge returns all supporting sources in stable order."""
    registry = CapabilityRegistry(
        (
            StubProvider(
                ProviderCapabilities(
                    source=DataSource.EXTENDED,
                    supported=frozenset({"clients.list"}),
                )
            ),
            StubProvider(
                ProviderCapabilities(
                    source=DataSource.OFFICIAL,
                    supported=frozenset({"clients.list"}),
                )
            ),
        )
    )

    assert registry.resolve("clients.list", RoutingPreference.MERGE) == (
        DataSource.OFFICIAL,
        DataSource.EXTENDED,
    )


def test_capability_registry_missing_capability() -> None:
    """Verify missing capabilities fail with a specific exception."""
    registry = CapabilityRegistry()

    with pytest.raises(UnsupportedCapabilityError) as err:
        registry.resolve("sites.list", RoutingPreference.PREFER_EXTENDED)

    assert err.value.capability == "sites.list"
    assert err.value.preference is RoutingPreference.PREFER_EXTENDED
