"""Test the v1 client and site assignment."""

import pytest

from aiounifi.controller import Controller
from aiounifi.errors import RequestError
from aiounifi.models.configuration import Configuration
from aiounifi.network.v1.api_client import ApiClient

from .conftest import BASE_URL, SITE_ID, envelope, url_pattern

SITES = [
    {"id": SITE_ID, "internalReference": "default", "name": "Default"},
    {
        "id": "b2f0c6ae-0000-4000-8000-000000000002",
        "internalReference": "5xk1",
        "name": "Cabin",
    },
]


def test_configuration_needs_only_an_api_key(config: Configuration) -> None:
    """Username and password are optional now."""
    assert config.api_key == "secret-key"
    assert config.username == ""
    assert config.password == ""


def test_controller_exposes_network_client_without_login(
    controller: Controller,
) -> None:
    """The v1 client hangs off the controller and shares its configuration."""
    assert isinstance(controller.network, ApiClient)
    assert controller.network is controller.network
    assert controller.network.config is controller.connectivity.config


def test_site_id_before_assignment(network_client: ApiClient) -> None:
    """Site-scoped calls need a site."""
    with pytest.raises(RequestError, match="assign_site"):
        _ = network_client.site_id


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("default", SITE_ID),
        (" default ", SITE_ID),
        (SITE_ID, SITE_ID),
        ("Cabin", "b2f0c6ae-0000-4000-8000-000000000002"),
        ("5xk1", "b2f0c6ae-0000-4000-8000-000000000002"),
    ],
)
async def test_assign_site_resolves_tokens(
    mock_aioresponse, network_client: ApiClient, token: str, expected: str
) -> None:
    """UUID, short name and display name all resolve."""
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope(SITES))

    assert await network_client.assign_site(token) == expected
    assert network_client.site_id == expected
    assert len(network_client.sites.items()) == 2


async def test_assign_site_defaults_to_configured_site(
    mock_aioresponse, config: Configuration
) -> None:
    """Without a token, Configuration.site is used."""
    config.site = "5xk1"
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope(SITES))

    client = ApiClient(config)

    assert await client.assign_site() == "b2f0c6ae-0000-4000-8000-000000000002"


async def test_assign_site_unknown(mock_aioresponse, network_client: ApiClient) -> None:
    """An unknown token is an error, not a silent default."""
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope(SITES))

    with pytest.raises(RequestError, match="No Network API site matches 'nope'"):
        await network_client.assign_site("nope")


async def test_get_info(mock_aioresponse, network_client: ApiClient) -> None:
    """Info is a bare object, wrapped into the envelope."""
    mock_aioresponse.get(
        f"{BASE_URL}/v1/info", payload={"applicationVersion": "10.6.106"}
    )

    assert await network_client.get_info() == {"applicationVersion": "10.6.106"}
