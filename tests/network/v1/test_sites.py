"""Test the sites interface."""

from aiounifi.network.v1.api_client import ApiClient

from .conftest import envelope, requests_to, url_pattern


async def test_list_page(mock_aioresponse, network_client: ApiClient) -> None:
    """One page, with a filter, leaves the cache alone."""
    mock_aioresponse.get(
        url_pattern("/v1/sites"),
        payload=envelope([{"id": "z", "internalReference": "zulu", "name": "Zulu"}]),
    )

    sites = await network_client.sites.list_page(
        offset=10, limit=1, filter_value="name.eq('Zulu')"
    )

    assert len(sites) == 1
    assert sites[0].site_id == "z"
    assert sites[0].internal_reference == "zulu"
    assert sites[0].name == "Zulu"
    assert not network_client.sites.items()
    (call,) = requests_to(mock_aioresponse, "get", "/v1/sites")
    assert call.kwargs["params"] == {
        "offset": 10,
        "limit": 1,
        "filter": "name.eq('Zulu')",
    }


async def test_page_params_are_clamped(
    mock_aioresponse, network_client: ApiClient
) -> None:
    """Offset below zero and limits outside 1..200 are corrected."""
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope([]))
    mock_aioresponse.get(url_pattern("/v1/sites"), payload=envelope([]))

    await network_client.sites.list_page(offset=-5, limit=0)
    await network_client.sites.list_page(limit=999)

    calls = requests_to(mock_aioresponse, "get", "/v1/sites")
    assert [call.kwargs["params"] for call in calls] == [
        {"offset": 0, "limit": 1},
        {"offset": 0, "limit": 200},
    ]
