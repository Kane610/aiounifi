"""Python library to connect UniFi and Home Assistant to work together."""

import asyncio
import json
import logging

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

    def __init__(self, session, host, port, ssl_context, site, callback):
        """Create resources for websocket communication."""
        self.session = session
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.site = site
        self.session_handler_callback = callback

        self._loop = asyncio.get_running_loop()

        self._data = None
        self._state = None

    @property
    def data(self):
        return self._data

    @property
    def state(self):
        """"""
        return self._state

    @state.setter
    def state(self, value):
        """"""
        self._state = value
        LOGGER.debug("Websocket %s", value)
        self.session_handler_callback(SIGNAL_CONNECTION_STATE)

    def start(self):
        if self.state != STATE_RUNNING:
            self.state = STATE_STARTING
            self._loop.create_task(self.running())

    def stop(self):
        """Close websocket connection."""
        self.state = STATE_STOPPED

    async def running(self):
        """Start websocket connection."""
        url = f"wss://{self.host}:{self.port}/wss/s/{self.site}/events"

        try:
            async with self.session.ws_connect(
                url, ssl=self.ssl_context, heartbeat=15
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
