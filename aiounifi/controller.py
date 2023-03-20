"""Python library to interact with UniFi controller."""

from collections.abc import Callable
from http import HTTPStatus
import logging
from pprint import pformat
from ssl import SSLContext
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp import client_exceptions

from .errors import (
    BadGateway,
    Forbidden,
    LoginRequired,
    RequestError,
    ResponseError,
    ServiceUnavailable,
    raise_error,
)
from .interfaces.clients import Clients
from .interfaces.clients_all import ClientsAll
from .interfaces.devices import Devices
from .interfaces.dpi_restriction_apps import DPIRestrictionApps
from .interfaces.dpi_restriction_groups import DPIRestrictionGroups
from .interfaces.events import EventHandler
from .interfaces.messages import MessageHandler
from .interfaces.outlets import Outlets
from .interfaces.ports import Ports
from .interfaces.wlans import Wlans
from .models.site import SiteDescriptionRequest, SiteListRequest
from .websocket import WebsocketSignal, WebsocketState, WSClient

if TYPE_CHECKING:
    from .models.api import ApiRequest

LOGGER = logging.getLogger(__name__)


class Controller:
    """Control a UniFi controller."""

    def __init__(
        self,
        host: str,
        websession: aiohttp.ClientSession,
        *,
        username: str,
        password: str,
        port: int = 8443,
        site: str = "default",
        ssl_context: SSLContext | bool = False,
        callback: Callable[[WebsocketSignal, dict[str, Any] | WebsocketState], None]
        | None = None,
    ) -> None:
        """Session setup."""
        self.host = host
        self.session = websession
        self.port = port
        self.username = username
        self.password = password
        self.site = site
        self.ssl_context = ssl_context
        self.callback = callback
        self.can_retry_login = False

        self.url = f"https://{self.host}:{self.port}"
        self.is_unifi_os = False
        self.headers: dict[str, Any] = {}
        self.last_response: aiohttp.ClientResponse | None = None

        self.websocket: WSClient | None = None

        self.messages = MessageHandler(self)
        self.events = EventHandler(self)

        self.clients = Clients(self)
        self.clients_all = ClientsAll(self)
        self.devices = Devices(self)
        self.outlets = Outlets(self)
        self.ports = Ports(self)
        self.dpi_apps = DPIRestrictionApps(self)
        self.dpi_groups = DPIRestrictionGroups(self)
        self.wlans = Wlans(self)

    async def check_unifi_os(self) -> None:
        """Check if controller is running UniFi OS."""
        await self._request("get", self.url, allow_redirects=False)
        if (
            response := self.last_response
        ) is not None and response.status == HTTPStatus.OK:
            self.is_unifi_os = True
            self.session.cookie_jar.clear_domain(self.host)
        LOGGER.debug("Talking to UniFi OS device: %s", self.is_unifi_os)

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

        await self._request("post", url, json=auth)

        if (
            (response := self.last_response) is not None
            and response.status == HTTPStatus.OK
            and (csrf_token := response.headers.get("x-csrf-token")) is not None
        ):
            self.headers = {"x-csrf-token": csrf_token}

        self.can_retry_login = True

    async def sites(self) -> dict[str, Any]:
        """Retrieve what sites are provided by controller."""
        sites = await self.request(SiteListRequest.create())
        LOGGER.debug(pformat(sites))
        return {site["desc"]: site for site in sites}

    async def site_description(self) -> list[dict[str, Any]]:
        """User description of current site."""
        description = await self.request(SiteDescriptionRequest.create())
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
            self.ssl_context,
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

    def session_handler(self, signal: WebsocketSignal) -> None:
        """Signalling from websocket.

        data - new data available for processing.
        state - network state has changed.
        """
        assert self.websocket

        if signal == WebsocketSignal.DATA:
            self.messages.handler(self.websocket.data)

        elif signal == WebsocketSignal.CONNECTION_STATE and self.callback:
            self.callback(WebsocketSignal.CONNECTION_STATE, self.websocket.state)

    async def request(self, api_request: "ApiRequest") -> list[dict[str, Any]]:
        """Make a request to the API, retry login on failure."""
        url = self.url + api_request.full_path(self.site, self.is_unifi_os)

        try:
            response: list[dict[str, Any]] = await self._request(
                api_request.method, url, api_request.data
            )
            return response

        except LoginRequired:
            if not self.can_retry_login:
                raise
            # Session likely expired, try again
            self.can_retry_login = False
            await self.login()
            return await self.request(api_request)

    async def _request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        **kwargs: bool,
    ) -> list[dict[str, Any]] | Any:
        """Make a request to the API."""
        self.last_response = None

        LOGGER.debug("%s", url)

        try:
            async with self.session.request(
                method,
                url,
                json=json,
                ssl=self.ssl_context,
                headers=self.headers,
                **kwargs,
            ) as res:
                LOGGER.debug("%s %s %s", res.status, res.content_type, res)

                self.last_response = res

                if res.status == HTTPStatus.UNAUTHORIZED:
                    raise LoginRequired(f"Call {url} received 401 Unauthorized")

                if res.status == HTTPStatus.FORBIDDEN:
                    raise Forbidden(f"Call {url} received 403 Forbidden")

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


def _raise_on_error(data: dict[str, Any] | None) -> None:
    """Check response for error message."""
    if not isinstance(data, dict):
        return None

    if "meta" in data and data["meta"]["rc"] == "error":
        raise_error(data["meta"]["msg"])

    if "errors" in data:
        raise_error(data["errors"][0])
