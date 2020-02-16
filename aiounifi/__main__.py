""""""

import aiohttp
import aiounifi
import argparse
import asyncio
import async_timeout
import logging

LOGGER = logging.getLogger(__name__)


def signalling_callback(signal, data):
    LOGGER.info(f"{signal}, {data}")


async def unifi_controller(
    host, username, password, port, site, session, sslcontext, callback
):
    """Setup UniFi controller and verify credentials."""
    controller = aiounifi.Controller(
        host,
        username=username,
        password=password,
        port=port,
        site=site,
        websession=session,
        sslcontext=sslcontext,
        callback=callback,
    )

    try:
        with async_timeout.timeout(10):
            await controller.login()
        return controller

    except aiounifi.Unauthorized:
        LOGGER.warning(f"Connected to UniFi at {host} but not registered")

    except (asyncio.TimeoutError, aiounifi.RequestError):
        LOGGER.error(f"Error connecting to the UniFi controller at {host}")

    except aiounifi.AiounifiException:
        LOGGER.exception("Unknown UniFi communication error occurred")


async def main(host, username, password, port, site, sslcontext=False):
    """Main function."""
    LOGGER.info("Starting aioUniFi")
    loop = asyncio.get_event_loop()

    websession = aiohttp.ClientSession(
        loop=loop, cookie_jar=aiohttp.CookieJar(unsafe=True)
    )

    controller = await unifi_controller(
        host=host,
        username=username,
        password=password,
        port=port,
        site=site,
        session=websession,
        sslcontext=sslcontext,
        callback=signalling_callback,
    )

    if not controller:
        LOGGER.error("Couldn't connect to UniFi controller.")
        return

    await controller.initialize()
    await controller.sites()
    controller.start_websocket()

    try:
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        controller.stop_websocket()
        await controller.session.close()


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str)
    parser.add_argument("username", type=str)
    parser.add_argument("password", type=str)
    parser.add_argument("-p", "--port", type=int, default=8443)
    parser.add_argument("-s", "--site", type=str, default="default")
    args = parser.parse_args()
    LOGGER.info(
        "%s %s %s %s %s", args.host, args.username, args.password, args.port, args.site
    )
    asyncio.run(
        main(
            host=args.host,
            username=args.username,
            password=args.password,
            port=args.port,
            site=args.site,
        )
    )
