"""Python library to interact with UniFi controller."""

from http import HTTPStatus
import logging
from pprint import pformat
from ssl import SSLContext
from typing import Any, Callable, Dict, Final, List, Literal, Optional, Union

import aiohttp
from aiohttp import client_exceptions

from .clients import Clients, ClientsAll
from .devices import Devices
from .dpi import DPIRestrictionApps, DPIRestrictionGroups
from .errors import (
    BadGateway,
    LoginRequired,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    raise_error,
)
from .events import CLIENT_EVENTS, DEVICE_EVENTS, Event
from .websocket import (
    SIGNAL_CONNECTION_STATE,
    SIGNAL_DATA,
    SignalLiteral as WSSignalLiteral,
    StateLiteral as WSStateLiteral,
    WSClient,
)
from .wlan import Wlans

LOGGER = logging.getLogger(__name__)

MESSAGE_CLIENT: Final = "sta:sync"
MESSAGE_CLIENT_REMOVED: Final = "user:delete"
MESSAGE_DEVICE: Final = "device:sync"
MESSAGE_EVENT: Final = "events"
MESSAGE_DPI_APP_ADDED: Final = "dpiapp:add"
MESSAGE_DPI_APP_REMOVED: Final = "dpiapp:delete"
MESSAGE_DPI_APP_UPDATED: Final = "dpiapp:sync"
MESSAGE_DPI_GROUP_ADDED: Final = "dpigroup:add"
MESSAGE_DPI_GROUP_REMOVED: Final = "dpigroup:delete"
MESSAGE_DPI_GROUP_UPDATED: Final = "dpigroup:sync"

ATTR_MESSAGE: Final = "message"
ATTR_META: Final = "meta"
ATTR_DATA: Final = "data"

DATA_CLIENT: Final = "client"
DATA_CLIENT_REMOVED: Final = "client_removed"
DATA_DEVICE: Final = "device"
DATA_EVENT: Final = "event"
DATA_DPI_APP: Final = "dpi_app"
DATA_DPI_APP_REMOVED: Final = "dpi_app_removed"
DATA_DPI_GROUP: Final = "dpi_group"
DATA_DPI_GROUP_REMOVED: Final = "dpi_group_removed"


IGNORE_MESSAGES: Final = ("device:update",)


class Controller:
    """Control a UniFi controller."""

    def __init__(
        self,
        host: str,
        websession: aiohttp.ClientSession,
        *,
        username: str,
        password: str,
        port=8443,
        site="default",
        sslcontext: Optional[SSLContext] = None,
        callback: Optional[
            Callable[[Literal[WSSignalLiteral, WSStateLiteral], Union[dict, str]], None]
        ] = None,
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
        self.headers: Dict[str, Any] = {}
        self.last_response: Optional[aiohttp.ClientResponse] = None

        self.websocket: Optional[WSClient] = None

        self.clients = Clients([], self.request)
        self.clients_all = ClientsAll([], self.request)
        self.devices = Devices([], self.request)
        self.dpi_apps = DPIRestrictionApps([], self.request)
        self.dpi_groups = DPIRestrictionGroups([], self.request)
        self.wlans = Wlans([], self.request)

    async def check_unifi_os(self) -> None:
        """Check if controller is running UniFi OS."""
        await self._request("get", url=self.url, allow_redirects=False)
        if (
            response := self.last_response
        ) is not None and response.status == HTTPStatus.OK:
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

    async def site_description(self) -> List[dict]:
        """User description of current site."""
        description = await self.request("get", "/self")
        LOGGER.debug(description)
        return description

    async def initialize(self) -> None:
        """Load UniFi parameters."""
        await self.clients.update()
        await self.clients_all.update()
        await self.devices.update()
        await self.dpi_apps.update()
        await self.dpi_groups.update()
        await self.wlans.update()

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

    def session_handler(self, signal: WSSignalLiteral) -> None:
        """Signalling from websocket.

        data - new data available for processing.
        state - network state has changed.
        """
        assert self.websocket

        if signal == SIGNAL_DATA:
            new_items = self.message_handler(self.websocket.data)
            if new_items and self.callback:
                self.callback(SIGNAL_DATA, new_items)

        elif signal == SIGNAL_CONNECTION_STATE and self.callback:
            self.callback(SIGNAL_CONNECTION_STATE, self.websocket.state)

    def message_handler(self, message: dict) -> dict:
        """Receive event from websocket and identifies where the event belong."""
        changes: Dict[str, set] = {}

        if message[ATTR_META][ATTR_MESSAGE] == MESSAGE_EVENT:
            changes[DATA_EVENT] = set()
            client_events = []
            device_events = []

            for raw in message[ATTR_DATA]:
                changes[DATA_EVENT].add(event := Event(raw))

                if event.event in CLIENT_EVENTS:
                    client_events.append(event)
                elif event.event in DEVICE_EVENTS:
                    device_events.append(event)

            self.clients.process_event(client_events)
            self.devices.process_event(device_events)

        # Client

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_CLIENT:
            changes[DATA_CLIENT] = self.clients.process_raw(message[ATTR_DATA])

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_CLIENT_REMOVED:
            changes[DATA_CLIENT_REMOVED] = self.clients.remove(message[ATTR_DATA])

        # Device

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_DEVICE:
            changes[DATA_DEVICE] = self.devices.process_raw(message[ATTR_DATA])

        # DPI App

        elif message[ATTR_META][ATTR_MESSAGE] in (
            MESSAGE_DPI_APP_ADDED,
            MESSAGE_DPI_APP_UPDATED,
        ):
            changes[DATA_DPI_APP] = self.dpi_apps.process_raw(message[ATTR_DATA])

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_DPI_APP_REMOVED:
            changes[DATA_DPI_APP_REMOVED] = self.dpi_apps.remove(message[ATTR_DATA])

        # DPI Group

        elif message[ATTR_META][ATTR_MESSAGE] in (
            MESSAGE_DPI_GROUP_ADDED,
            MESSAGE_DPI_GROUP_UPDATED,
        ):
            changes[DATA_DPI_GROUP] = self.dpi_groups.process_raw(message[ATTR_DATA])

        elif message[ATTR_META][ATTR_MESSAGE] == MESSAGE_DPI_GROUP_REMOVED:
            changes[DATA_DPI_GROUP_REMOVED] = self.dpi_groups.remove(message[ATTR_DATA])

        # Unsupported

        elif message[ATTR_META][ATTR_MESSAGE] in IGNORE_MESSAGES:
            pass

        else:
            LOGGER.debug("Unsupported message type %s", message)

        return changes

    async def request(
        self,
        method: str,
        path: str = "",
        json: Optional[Dict[str, Any]] = None,
        url: str = "",
    ) -> List[dict]:
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
        json: Optional[Dict[str, Any]] = None,
        url: str = "",
        **kwargs: bool,
    ) -> List[dict]:
        """Make a request to the API."""
        self.last_response = None

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

                self.last_response = res

                if res.status == HTTPStatus.UNAUTHORIZED:
                    raise LoginRequired(f"Call {url} received 401 Unauthorized")

                if res.status == HTTPStatus.NOT_FOUND:
                    raise ResponseError(f"Call {url} received 404 Not Found")

                if res.status == HTTPStatus.BAD_GATEWAY:
                    raise BadGateway(f"Call {url} received 502 bad gateway")

                if res.status == HTTPStatus.SERVICE_UNAVAILABLE:
                    raise ServiceUnavailable(
                        f"Call {url} received 503 service unavailable"
                    )

                if res.content_type == "application/json":
                    response = await res.json()
                    _raise_on_error(response)
                    if "data" in response:
                        return response["data"]
                    return response
                return []

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
