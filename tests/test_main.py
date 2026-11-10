"""Tests for the command-line entry point."""

import asyncio
from runpy import run_path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

import aiounifi
from aiounifi import __main__ as cli


def _session() -> Mock:
    session = Mock()
    session.close = AsyncMock()
    return session


def _controller_updates() -> SimpleNamespace:
    return SimpleNamespace(
        **{
            name: SimpleNamespace(update=AsyncMock())
            for name in (
                "clients",
                "clients_all",
                "devices",
                "dpi_apps",
                "dpi_groups",
                "port_forwarding",
                "sites",
                "system_information",
                "traffic_rules",
                "traffic_routes",
                "vouchers",
                "wlans",
            )
        },
        start_websocket=AsyncMock(),
    )


@pytest.mark.parametrize(
    "error",
    [
        aiounifi.LoginRequired(),
        aiounifi.Unauthorized(),
        TimeoutError(),
        aiounifi.RequestError("request failed"),
        aiounifi.AiounifiException(),
    ],
)
async def test_unifi_controller_login_errors_return_none(error: Exception) -> None:
    """Login failures are logged and represented by a missing controller."""
    controller = Mock()
    controller.login = AsyncMock(side_effect=error)

    with patch.object(cli, "Controller", return_value=controller):
        result = await cli.unifi_controller(
            "host", "user", "pass", 8443, "default", Mock()
        )

    assert result is None


async def test_unifi_controller_returns_logged_in_controller() -> None:
    """Return the controller when login succeeds."""
    controller = Mock()
    controller.login = AsyncMock()

    with patch.object(cli, "Controller", return_value=controller):
        result = await cli.unifi_controller(
            "host", "user", "pass", 8443, "default", Mock()
        )

    assert result is controller


async def test_network_api_lists_controller_data() -> None:
    """Fetch and log sites, devices, and clients from the Network API."""
    network = SimpleNamespace(
        get_info=AsyncMock(return_value={"applicationVersion": "1.2.3"}),
        assign_site=AsyncMock(),
        devices=SimpleNamespace(
            update=AsyncMock(),
            values=lambda: [SimpleNamespace(name="AP", model="U7", state=1)],
        ),
        clients=SimpleNamespace(
            update=AsyncMock(),
            values=lambda: [
                SimpleNamespace(name="Phone", mac_address="aa", ip_address="1.2.3.4")
            ],
        ),
        sites=SimpleNamespace(
            values=lambda: [SimpleNamespace(name="Home", site_id="site-id")]
        ),
    )
    controller = SimpleNamespace(network=network)

    with patch.object(cli, "Controller", return_value=controller):
        await cli.network_api("host", "key", 8443, "default", Mock())

    network.assign_site.assert_awaited_once_with("default")
    network.devices.update.assert_awaited_once()
    network.clients.update.assert_awaited_once()


@pytest.mark.parametrize(
    "error",
    [aiounifi.Unauthorized(), TimeoutError(), aiounifi.AiounifiException()],
)
async def test_network_api_handles_request_errors(error: Exception) -> None:
    """Network API failures are handled without attempting to list results."""
    network = SimpleNamespace(get_info=AsyncMock(side_effect=error))

    with patch.object(cli, "Controller", return_value=SimpleNamespace(network=network)):
        await cli.network_api("host", "key", 8443, "default", Mock())


async def test_main_network_api_closes_session() -> None:
    """The API-key flow closes its session even when the API call fails."""
    session = _session()

    with (
        patch.object(cli.aiohttp, "ClientSession", return_value=session),
        patch.object(cli, "network_api", new=AsyncMock(side_effect=RuntimeError)),
        pytest.raises(RuntimeError),
    ):
        await cli.main("host", "", "", 8443, "default", api_key="key")

    session.close.assert_awaited_once()


async def test_main_returns_after_network_api_success() -> None:
    """Return after a successful API-key request and close its session."""
    session = _session()

    with (
        patch.object(cli.aiohttp, "ClientSession", return_value=session),
        patch.object(cli, "network_api", new=AsyncMock()),
    ):
        await cli.main("host", "", "", 8443, "default", api_key="key")

    session.close.assert_awaited_once()


async def test_main_returns_when_login_fails() -> None:
    """Close the session when no controller is returned."""
    session = _session()

    with (
        patch.object(cli.aiohttp, "ClientSession", return_value=session),
        patch.object(cli, "unifi_controller", new=AsyncMock(return_value=None)),
    ):
        await cli.main("host", "user", "pass", 8443, "default")

    session.close.assert_awaited_once()


async def test_main_updates_and_stops_websocket_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Update controller resources and close the session on cancellation."""
    session = _session()
    controller = _controller_updates()

    async def cancel_sleep(_delay: float) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr(cli.asyncio, "sleep", cancel_sleep)
    with (
        patch.object(cli.aiohttp, "ClientSession", return_value=session),
        patch.object(cli, "unifi_controller", new=AsyncMock(return_value=controller)),
    ):
        await cli.main("host", "user", "pass", 8443, "default")

    for name in (
        "clients",
        "clients_all",
        "devices",
        "dpi_apps",
        "dpi_groups",
        "port_forwarding",
        "sites",
        "system_information",
        "traffic_rules",
        "traffic_routes",
        "vouchers",
        "wlans",
    ):
        getattr(controller, name).update.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.parametrize(
    ("arguments", "interrupt"),
    [
        (["host"], False),
        (["host", "user", "pass", "--debug", "--api-key", "key"], True),
    ],
)
def test_cli_script_guard(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    interrupt: bool,
) -> None:
    """Parse CLI arguments and handle a keyboard interrupt from asyncio.run."""
    monkeypatch.setattr(sys, "argv", ["aiounifi", *arguments])

    def run_side_effect(coroutine: object) -> None:
        coroutine.close()  # type: ignore[attr-defined]
        if interrupt:
            raise KeyboardInterrupt

    with patch.object(asyncio, "run", side_effect=run_side_effect):
        run_path(cli.__file__, run_name="__main__")
