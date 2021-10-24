"""Python library to connect UniFi and Home Assistant to work together."""

import asyncio
import json
import logging
from ssl import SSLContext
from typing import Callable, Optional

import aiohttp

LOGGER = logging.getLogger(__name__)

SIGNAL_DATA = "data"
SIGNAL_CONNECTION_STATE = "state"

STATE_DISCONNECTED = "disconnected"
STATE_RUNNING = "running"
STATE_STARTING = "starting"
STATE_STOPPED = "stopped"


class WSClient:
    """Websocket transport, session handling, message generation."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        ssl_context: Optional[SSLContext],
        site: str,
        callback: Callable[[str], None],
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

        self._data: dict = {}
        self._state = ""

    @property
    def data(self) -> dict:
        """Return data."""
        return self._data

    @property
    def state(self) -> str:
        """State of websocket."""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        """Set state of websocket."""
        self._state = value
        LOGGER.debug("Websocket %s", value)
        self.session_handler_callback(SIGNAL_CONNECTION_STATE)

    def start(self) -> None:
        """Start websocket and update its state."""
        if self.state != STATE_RUNNING:
            self.state = STATE_STARTING
            self._loop.create_task(self.running())

    def stop(self) -> None:
        """Close websocket connection."""
        self.state = STATE_STOPPED

    async def running(self) -> None:
        """Start websocket connection."""
        try:
            async with self.session.ws_connect(
                self.url, ssl=self.ssl_context, heartbeat=15
            ) as ws:
                self.state = STATE_RUNNING

                async for msg in ws:

                    if self.state == STATE_STOPPED:
                        break

                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._data = json.loads(msg.data)
                        self.session_handler_callback(SIGNAL_DATA)
                        LOGGER.debug(msg.data)

                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        LOGGER.warning("AIOHTTP websocket connection closed")
                        break

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        LOGGER.error("AIOHTTP websocket error")
                        break

        except aiohttp.ClientConnectorError:
            if self.state != STATE_STOPPED:
                LOGGER.error("Client connection error")
                self.state = STATE_DISCONNECTED

        except Exception as err:
            if self.state != STATE_STOPPED:
                LOGGER.error("Unexpected error %s", err)
                self.state = STATE_DISCONNECTED

        else:
            if self.state != STATE_STOPPED:
                self.state = STATE_DISCONNECTED
