"""Unifi implementation."""

import logging

from pprint import pformat

from aiohttp import client_exceptions

from .clients import Clients, URL as client_url, ClientsAll, URL_ALL as all_client_url
from .devices import Devices, URL as device_url
from .errors import raise_error, LoginRequired, ResponseError, RequestError
from .events import event
from .websocket import WSClient, SIGNAL_CONNECTION_STATE, SIGNAL_DATA, STATE_RUNNING
from .wlan import Wlans, URL as wlan_url

LOGGER = logging.getLogger(__name__)

MESSAGE_CLIENT = "sta:sync"
MESSAGE_CLIENT_REMOVED = "user:delete"
MESSAGE_DEVICE = "device:sync"
MESSAGE_EVENT = "events"

ATTR_MESSAGE = "message"
ATTR_META = "meta"
ATTR_DATA = "data"

DATA_CLIENT = "client"
DATA_CLIENT_REMOVED = "client_removed"
DATA_DEVICE = "device"
DATA_EVENT = "event"


class Controller:
    """Control a UniFi controller."""

    def __init__(
        self,
        host,
        websession,
        *,
        username,
        password,
        port=8443,
        site="default",
        sslcontext=None,
        callback=None,
    ):
        self.host = host
        self.session = websession
        self.port = port
        self.username = username
        self.password = password
        self.site = site
        self.sslcontext = sslcontext

        self.url = f"https://{self.host}:{self.port}"
        self.is_unifi_os = False
        self.headers = None

        self.callback = callback
        self.add_device_callback = None
        self.connection_status_callback = None

        self.websocket = None

        self.clients = None
        self.clients_all = None
        self.devices = None
        self.wlans = None

    async def check_unifi_os(self):
        response = await self.request("get", url=self.url, allow_redirects=False)
        if response.status == 200:
            self.is_unifi_os = True
            self.headers = {"x-csrf-token": response.headers.get("x-csrf-token")}

    async def login(self):
        if self.is_unifi_os:
            url = f"{self.url}/api/auth/login"
        else:
            url = f"{self.url}/api/login"

        auth = {
            "username": self.username,
            "password": self.password,
            "remember": True,
        }

        await self.request("post", url=url, json=auth)

    async def sites(self):
        if self.is_unifi_os:
            url = f"{self.url}/proxy/network/api/self/sites"
        else:
            url = f"{self.url}/api/self/sites"

        sites = await self.request("get", url=url)
        LOGGER.debug(pformat(sites))
        return {site["desc"]: site for site in sites}

    async def initialize(self):
        clients = await self.request("get", client_url)
        self.clients = Clients(clients, self.request)
        devices = await self.request("get", device_url)
        self.devices = Devices(devices, self.request)
        all_clients = await self.request("get", all_client_url)
        self.clients_all = ClientsAll(all_clients, self.request)
        wlans = await self.request("get", wlan_url)
        self.wlans = Wlans(wlans, self.request)

    def start_websocket(self):
        """Start websession and websocket to UniFi."""
        self.websocket = WSClient(
            self.session,
            self.host,
            self.port,
            self.sslcontext,
            self.site,
            callback=self.session_handler,
            is_unifi_os=self.is_unifi_os,
        )
        self.websocket.start()

    def stop_websocket(self) -> None:
        """Close websession and websocket to UniFi."""
        LOGGER.info("Shutting down connections to UniFi.")
        if self.websocket:
            self.websocket.stop()

    def session_handler(self, signal: str) -> None:
        """Signalling from websocket.

           data - new data available for processing.
           state - network state has changed.
        """
        if not self.websocket:
            return

        if signal == SIGNAL_DATA:
            new_items = self.message_handler(self.websocket.data)
            if new_items and self.callback:
                self.callback(SIGNAL_DATA, new_items)

        elif signal == SIGNAL_CONNECTION_STATE and self.callback:
            self.callback(SIGNAL_CONNECTION_STATE, self.websocket.state)

    def message_handler(self, message: dict) -> dict:
        """Receive event from websocket and identifies where the event belong."""
        changes = {}

        if message[ATTR_META][ATTR_MESSAGE] == MESSAGE_CLIENT:
            changes[DATA_CLIENT] = self.clients.process_raw(message[ATTR_DATA])

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_DEVICE:
            changes[DATA_DEVICE] = self.devices.process_raw(message[ATTR_DATA])

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_EVENT:
            self.clients.process_event(message[ATTR_DATA])
            changes[DATA_EVENT] = event(message[ATTR_DATA][0])

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_CLIENT_REMOVED:
            changes[DATA_CLIENT_REMOVED] = self.clients.remove(message[ATTR_DATA])

        else:
            LOGGER.debug(f"Unsupported message type {message}")

        return changes

    async def request(self, method, path=None, json=None, url=None, **kwargs):
        """Make a request to the API."""
        if not url:
            if self.is_unifi_os:
                url = f"{self.url}/proxy/network/api/s/{self.site}"
            else:
                url = f"{self.url}/api/s/{self.site}"

            if path is not None:
                url += f"{path}"

        LOGGER.debug("%s", url)

        try:
            async with self.session.request(
                method,
                url,
                json=json,
                ssl=self.sslcontext,
                headers=self.headers,
                **kwargs,
            ) as res:
                LOGGER.debug("%s %s %s", res.status, res.content_type, res)

                if res.status == 401:
                    raise LoginRequired(f"Call {url} received 401 Unauthorized")

                if res.status == 404:
                    raise ResponseError(f"Call {url} received 404 Not Found")

                if res.content_type == "application/json":
                    response = await res.json()
                    _raise_on_error(response)
                    if "data" in response:
                        return response["data"]
                    return response
                return res

        except client_exceptions.ClientError as err:
            raise RequestError(
                f"Error requesting data from {self.host}: {err}"
            ) from None


def _raise_on_error(data):
    """Check response for error message."""
    if not isinstance(data, dict):
        return

    if "meta" in data and data["meta"]["rc"] == "error":
        raise_error(data["meta"]["msg"])

    if "errors" in data:
        raise_error(data["errors"][0])
