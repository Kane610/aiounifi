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
MESSAGE_DEVICE = "device:sync"
MESSAGE_EVENT = "events"

ATTR_MESSAGE = "message"
ATTR_META = "meta"
ATTR_DATA = "data"


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

        self.base_path = ""
        self.is_unifi_os = False

        self.callback = callback
        self.add_device_callback = None
        self.connection_status_callback = None

        self.websocket = None

        self.clients = None
        self.clients_all = None
        self.devices = None
        self.wlans = None

        self.headers = None

    async def check_unifi_os(self):
        response = await self.request("get", include_site=False)

        headers = {
            "x-csrf-token": response.headers.get("x-csrf-token")
        }

        self.headers = headers

        if response.status == 200:
            self.is_unifi_os = True

    async def login(self):
        self.base_path = "api"
        auth = {
            "username": self.username,
            "password": self.password,
            "remember": True,
        }
        url = "login"
        if self.is_unifi_os:
            url = "auth/login"
        await self.request("post", url, json=auth, include_site=False)

        if self.is_unifi_os:
            self.base_path = "proxy/network/api"

    async def sites(self):
        url = "self/sites"
        sites = await self.request("get", url, include_site=False)
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
            callback=self.session_handler,
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
                self.callback("new_data", new_items)

        elif signal == SIGNAL_CONNECTION_STATE and self.callback:
            self.callback(SIGNAL_CONNECTION_STATE, self.websocket.state)

    def message_handler(self, message: dict) -> dict:
        """Receive event from websocket and identifies where the event belong."""
        new_items = None

        if message[ATTR_META][ATTR_MESSAGE] not in (
            MESSAGE_CLIENT,
            MESSAGE_DEVICE,
            MESSAGE_EVENT,
        ):
            LOGGER.debug(f"Unsupported message type {message}")

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_CLIENT:
            new_items = {"clients": self.clients.process_raw(message[ATTR_DATA])}

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_DEVICE:
            new_items = {"devices": self.devices.process_raw(message[ATTR_DATA])}

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_EVENT:
            new_items = {"event": event(message[ATTR_DATA][0])}

        return new_items

    async def request(self, method, path=None, json=None, include_site=True, url=None):
        """Make a request to the API."""
        url = f"https://{self.host}:{self.port}/{self.base_path}"
        url = f"https://{self.host}/{self.base_path}"

        if include_site:
            url += f"/s/{self.site}"

        if path is not None:
            url += f"/{path}"

        try:
            async with self.session.request(
                method, url, json=json, ssl=self.sslcontext, headers=self.headers
            ) as res:
                print(res.status, res)
                if res.status == 401:
                    raise LoginRequired(f"Call {url} received 401 Unauthorized")

                if res.status == 404:
                    raise ResponseError(f"Call {url} received 404 Not Found")

                if res.content_type == "application/json":
                    response = await res.json()
                    _raise_on_error(response)
                    return response.get("data") or response
                return res

        except client_exceptions.ClientError as err:
            raise RequestError(
                f"Error requesting data from {self.host}: {err}"
            ) from None


def _raise_on_error(data):
    """Check response for error message."""
    if isinstance(data, dict):
        if data.get("errors"):
            error = str(data["errors"]).strip("[]")
            raise_error(error)
        if data.get("meta") and data.get("meta").get("rc") == "error":
            error = data["meta"]["rc"]
            raise_error(error)
