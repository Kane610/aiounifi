"""Shared fixtures for Network Integration API v1 tests."""

from __future__ import annotations

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
def network_config_fixture(unifi_controller: Controller, api_key: str) -> Configuration:
    """Return controller config with an Integration API key."""
    unifi_controller.connectivity.config.api_key = api_key
    return unifi_controller.connectivity.config


@pytest.fixture(name="network_client")
def network_client_fixture(unifi_controller: Controller, api_key: str) -> ApiClient:
    """Return controller-backed Integration API client."""
    unifi_controller.connectivity.config.api_key = api_key
    return unifi_controller.network


@pytest.fixture(name="network_connectivity")
def network_connectivity_fixture(network_config: Configuration) -> Connectivity:
    """Build connectivity helper for direct unit tests."""
    return Connectivity(network_config)
