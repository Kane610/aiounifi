"""Python library to connect UniFi and Home Assistant to work together."""

import asyncio
from collections.abc import Callable
import enum
import logging
from ssl import SSLContext
from typing import Any

import aiohttp
import orjson

LOGGER = logging.getLogger(__name__)


class WebsocketSignal(enum.Enum):
    """Websocket signal."""

    CONNECTION_STATE = "state"
    DATA = "data"


class WebsocketState(enum.Enum):
    """Websocket state."""

    DISCONNECTED = "disconnected"
    RUNNING = "running"
    STARTING = "starting"
    STOPPED = "stopped"


class WSClient:
    """Websocket transport, session handling, message generation."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        ssl_context: SSLContext | bool,
        site: str,
        callback: Callable[[WebsocketSignal], None],
        is_unifi_os: bool = False,
    ):
        """Create resources for websocket communication."""
        self.session = session
        self.ssl_context = ssl_context
        self.session_handler_callback = callback

        if is_unifi_os:
            self.url = f"wss://{host}:{port}/proxy/network/wss/s/{site}/events"
        else:
            self.url = f"wss://{host}:{port}/wss/s/{site}/events"

        self._loop = asyncio.get_running_loop()

        self._data: dict[str, Any] = {}
        self._state = WebsocketState.STOPPED

    @property
    def data(self) -> dict[str, Any]:
        """Return data."""
        return self._data

    @property
    def state(self) -> WebsocketState:
        """State of websocket."""
        return self._state

    @state.setter
    def state(self, value: WebsocketState) -> None:
        """Set state of websocket."""
        self._state = value
        LOGGER.debug("Websocket %s", value)
        self.session_handler_callback(WebsocketSignal.CONNECTION_STATE)

    def start(self) -> None:
        """Start websocket and update its state."""
        if self.state != WebsocketState.RUNNING:
            self.state = WebsocketState.STARTING
            self._loop.create_task(self.running())

    def stop(self) -> None:
        """Close websocket connection."""
        self.state = WebsocketState.STOPPED

    async def running(self) -> None:
        """Start websocket connection."""
        try:
            async with self.session.ws_connect(
                self.url, ssl=self.ssl_context, heartbeat=15
            ) as ws:
                self.state = WebsocketState.RUNNING

                async for msg in ws:
                    if self.state == WebsocketState.STOPPED:
                        break

                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._data = orjson.loads(msg.data)
                        self.session_handler_callback(WebsocketSignal.DATA)
                        LOGGER.debug(msg.data)

                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        LOGGER.warning("AIOHTTP websocket connection closed")
                        break

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        LOGGER.error("AIOHTTP websocket error: '%s'", msg.data)
                        break

        except aiohttp.ClientConnectorError:
            if self.state != WebsocketState.STOPPED:
                LOGGER.error("Client connection error")
                self.state = WebsocketState.DISCONNECTED

        except Exception as err:
            if self.state != WebsocketState.STOPPED:
                LOGGER.error("Unexpected error %s", err)
                self.state = WebsocketState.DISCONNECTED

        else:
            if self.state != WebsocketState.STOPPED:
                self.state = WebsocketState.DISCONNECTED
