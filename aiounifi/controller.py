"""Python library to interact with UniFi controller."""

import logging
from pprint import pformat

from aiohttp import client_exceptions

from .clients import URL as client_url, URL_ALL as all_client_url, Clients, ClientsAll
from .devices import URL as device_url, Devices
from .dpi import (
    APP_URL as dpi_app_url,
    GROUP_URL as dpi_group_url,
    DPIRestrictionApps,
    DPIRestrictionGroups,
)
from .errors import (
    BadGateway,
    LoginRequired,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    raise_error,
)
from .events import CLIENT_EVENTS, DEVICE_EVENTS, event
from .websocket import SIGNAL_CONNECTION_STATE, SIGNAL_DATA, WSClient
from .wlan import URL as wlan_url, Wlans

LOGGER = logging.getLogger(__name__)

MESSAGE_CLIENT = "sta:sync"
MESSAGE_CLIENT_REMOVED = "user:delete"
MESSAGE_DEVICE = "device:sync"
MESSAGE_EVENT = "events"
MESSAGE_DPI_GROUP = "dpigroup"
MESSAGE_DPI_APP = "dpiapp"

ATTR_MESSAGE = "message"
ATTR_META = "meta"
ATTR_DATA = "data"

DATA_CLIENT = "client"
DATA_CLIENT_REMOVED = "client_removed"
DATA_DEVICE = "device"
DATA_EVENT = "event"
DATA_DPI_APP = "dpi_app"
DATA_DPI_APP_REMOVED = "dpi_app_removed"
DATA_DPI_GROUP = "dpi_group"
DATA_DPI_GROUP_REMOVED = "dpi_group_removed"


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
        """Session setup."""
        self.host = host
        self.session = websession
        self.port = port
        self.username = username
        self.password = password
        self.site = site
        self.sslcontext = sslcontext
        self.callback = callback
        self.can_retry_login = False

        self.url = f"https://{self.host}:{self.port}"
        self.is_unifi_os = False
        self.headers = None

        self.websocket = None

        self.clients = None
        self.clients_all = None
        self.devices = None
        self.dpi_apps = None
        self.dpi_groups = None
        self.wlans = None

    async def check_unifi_os(self) -> None:
        """Check if controller is running UniFi OS."""
        response = await self._request("get", url=self.url, allow_redirects=False)
        if response.status == 200:
            self.is_unifi_os = True
            self.headers = {"x-csrf-token": response.headers.get("x-csrf-token")}

    async def login(self) -> None:
        """Log in to controller."""
        if self.is_unifi_os:
            url = f"{self.url}/api/auth/login"
        else:
            url = f"{self.url}/api/login"

        auth = {
            "username": self.username,
            "password": self.password,
            "remember": True,
        }

        await self._request("post", url=url, json=auth)

        self.can_retry_login = True

    async def sites(self) -> dict:
        """Retrieve what sites are provided by controller."""
        if self.is_unifi_os:
            url = f"{self.url}/proxy/network/api/self/sites"
        else:
            url = f"{self.url}/api/self/sites"

        sites = await self.request("get", url=url)
        LOGGER.debug(pformat(sites))
        return {site["desc"]: site for site in sites}

    async def site_description(self) -> dict:
        """User description of current site."""
        description = await self.request("get", "/self")
        LOGGER.debug(description)
        return description

    async def initialize(self) -> None:
        """Load UniFi parameters."""
        clients = await self.request("get", client_url)
        self.clients = Clients(clients, self.request)
        devices = await self.request("get", device_url)
        self.devices = Devices(devices, self.request)
        dpi_apps = await self.request("get", dpi_app_url)
        self.dpi_apps = DPIRestrictionApps(dpi_apps, self.request)
        dpi_groups = await self.request("get", dpi_group_url)
        self.dpi_groups = DPIRestrictionGroups(dpi_groups, self.request, self.dpi_apps)
        all_clients = await self.request("get", all_client_url)
        self.clients_all = ClientsAll(all_clients, self.request)
        wlans = await self.request("get", wlan_url)
        self.wlans = Wlans(wlans, self.request)

    def start_websocket(self) -> None:
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
            events = []
            for item in message[ATTR_DATA]:
                events.append(event(item))
            self.clients.process_event(
                [
                    client_event
                    for client_event in events
                    if client_event.event in CLIENT_EVENTS
                ]
            )
            self.devices.process_event(
                [
                    device_event
                    for device_event in events
                    if device_event.event in DEVICE_EVENTS
                ]
            )
            changes[DATA_EVENT] = set(events)

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_CLIENT_REMOVED:
            changes[DATA_CLIENT_REMOVED] = self.clients.remove(message[ATTR_DATA])

        elif MESSAGE_DPI_GROUP in message[ATTR_META][ATTR_MESSAGE]:
            action = message[ATTR_META][ATTR_MESSAGE].split(":")[1]
            if action == "delete":
                changes[DATA_DPI_GROUP_REMOVED] = self.dpi_groups.remove(
                    message[ATTR_DATA]
                )
            else:
                changes[DATA_DPI_GROUP] = self.dpi_groups.process_raw(
                    message[ATTR_DATA]
                )

        elif MESSAGE_DPI_APP in message[ATTR_META][ATTR_MESSAGE]:
            action = message[ATTR_META][ATTR_MESSAGE].split(":")[1]
            if action == "delete":
                changes[DATA_DPI_APP_REMOVED] = self.dpi_apps.remove(message[ATTR_DATA])
            else:
                changes[DATA_DPI_APP] = self.dpi_apps.process_raw(message[ATTR_DATA])
                if action == "sync":
                    # Manually trigger update for related groups
                    changes[DATA_DPI_GROUP] = {
                        key
                        for key in self.dpi_groups
                        if set(self.dpi_groups[key].dpiapp_ids).intersection(
                            changes[DATA_DPI_APP]
                        )
                    }
                    for key in changes[DATA_DPI_GROUP]:
                        group = self.dpi_groups[key]
                        group.update(group.raw)

        else:
            LOGGER.debug("Unsupported message type %s", message)

        return changes

    async def request(
        self,
        method: str,
        path: str = "",
        json: dict = None,
        url: str = "",
    ):
        """Make a request to the API, retry login on failure."""
        try:
            return await self._request(method, path, json, url)
        except LoginRequired:
            if not self.can_retry_login:
                raise
            # Session likely expired, try again
            self.can_retry_login = False
            # Make sure we get a new csrf token
            await self.check_unifi_os()
            await self.login()
            return await self._request(method, path, json, url)

    async def _request(
        self,
        method: str,
        path: str = "",
        json: dict = None,
        url: str = "",
        **kwargs: bool,
    ):
        """Make a request to the API."""
        if not url:
            if self.is_unifi_os:
                url = f"{self.url}/proxy/network/api/s/{self.site}"
            else:
                url = f"{self.url}/api/s/{self.site}"

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

                if res.status == 502:
                    raise BadGateway(f"Call {url} received 502 bad gateway")

                if res.status == 503:
                    raise ServiceUnavailable(
                        f"Call {url} received 503 service unavailable"
                    )

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


def _raise_on_error(data) -> None:
    """Check response for error message."""
    if not isinstance(data, dict):
        return None

    if "meta" in data and data["meta"]["rc"] == "error":
        raise_error(data["meta"]["msg"])

    if "errors" in data:
        raise_error(data["errors"][0])
