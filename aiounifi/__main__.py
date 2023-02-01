"""Use aiounifi as a CLI."""

import argparse
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Callable

import aiohttp
import async_timeout

import aiounifi
from aiounifi.controller import Controller

if TYPE_CHECKING:
    from ssl import SSLContext

    from aiounifi.websocket import WebsocketSignal, WebsocketState

LOGGER = logging.getLogger(__name__)


def signalling_callback(
    signal: WebsocketSignal, data: dict[str, Any] | WebsocketState
) -> None:
    """Receive and print events from websocket."""
    LOGGER.info("%s, %s", signal, data)


async def unifi_controller(
    host: str,
    username: str,
    password: str,
    port: int,
    site: str,
    session: aiohttp.ClientSession,
    ssl_context: SSLContext | bool,
    callback: Callable[[WebsocketSignal, dict[str, Any] | WebsocketState], None],
) -> Controller | None:
    """Set up UniFi controller and verify credentials."""
    controller = Controller(
        host,
        username=username,
        password=password,
        port=port,
        site=site,
        websession=session,
        ssl_context=ssl_context,
        callback=callback,
    )

    try:
        async with async_timeout.timeout(10):
            await controller.check_unifi_os()
            await controller.login()
        return controller

    except aiounifi.LoginRequired:
        LOGGER.warning("Connected to UniFi at %s but couldn't log in", host)

    except aiounifi.Unauthorized:
        LOGGER.warning("Connected to UniFi at %s but not registered", host)

    except (asyncio.TimeoutError, aiounifi.RequestError):
        LOGGER.exception("Error connecting to the UniFi controller at %s", host)

    except aiounifi.AiounifiException:
        LOGGER.exception("Unknown UniFi communication error occurred")

    return None


async def main(
    host: str,
    username: str,
    password: str,
    port: int,
    site: str,
    ssl_context: SSLContext | bool = False,
) -> None:
    """CLI method for library."""
    LOGGER.info("Starting aioUniFi")

    websession = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))

    controller = await unifi_controller(
        host=host,
        username=username,
        password=password,
        port=port,
        site=site,
        session=websession,
        ssl_context=ssl_context,
        callback=signalling_callback,
    )

    if not controller:
        LOGGER.error("Couldn't connect to UniFi controller")
        await websession.close()
        return

    await controller.initialize()
    await controller.sites()
    await controller.site_description()
    controller.start_websocket()

    try:
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        pass

    finally:
        controller.stop_websocket()
        await websession.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str)
    parser.add_argument("username", type=str)
    parser.add_argument("password", type=str)
    parser.add_argument("-p", "--port", type=int, default=8443)
    parser.add_argument("-s", "--site", type=str, default="default")
    parser.add_argument("-D", "--debug", action="store_true")
    args = parser.parse_args()

    LOG_LEVEL = logging.INFO
    if args.debug:
        LOG_LEVEL = logging.DEBUG
    logging.basicConfig(format="%(message)s", level=LOG_LEVEL)

    LOGGER.info(
        "%s, %s, %s, %i, %s",
        args.host,
        args.username,
        args.password,
        args.port,
        args.site,
    )

    try:
        asyncio.run(
            main(
                host=args.host,
                username=args.username,
                password=args.password,
                port=args.port,
                site=args.site,
            )
        )
    except KeyboardInterrupt:
        pass
