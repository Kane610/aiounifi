"""Shared fixtures for Network API v1 tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from aiounifi.controller import Controller
from aiounifi.models.configuration import Configuration
from aiounifi.network.v1.api_client import ApiClient
from aiounifi.network.v1.connectivity import Connectivity


@pytest.fixture(name="api_key")
def api_key_v1_fixture() -> str:
    """Provide API key for Network API v1 tests."""
    return "secret-key"


@pytest.fixture(name="network_config")
def network_config_fixture(unifi_controller: Controller) -> Configuration:
    """Return controller-backed config for v1 tests."""
    return unifi_controller.connectivity.config


@pytest.fixture(name="network_client")
def network_client_fixture(unifi_controller: Controller) -> ApiClient:
    """Return controller-backed network API client."""
    return unifi_controller.network


@pytest.fixture(name="network_connectivity")
def network_connectivity_fixture(network_config: Configuration) -> Connectivity:
    """Build connectivity helper for direct unit tests."""
    return Connectivity(network_config)


@pytest.fixture(name="network_client_with_site")
async def network_client_with_site_fixture(
    network_client: ApiClient,
) -> AsyncGenerator[ApiClient]:
    """Return network client with active test site UUID assigned."""
    original_resolver = network_client.controller.sites.resolve_site_uuid
    network_client.controller.sites.resolve_site_uuid = lambda _: "site-uuid"
    await network_client.assign_site("default")
    try:
        yield network_client
    finally:
        network_client.controller.sites.resolve_site_uuid = original_resolver
