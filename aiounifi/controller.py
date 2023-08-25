"""Python library to interact with UniFi controller."""

import asyncio
from collections.abc import Callable, Coroutine
import logging
from typing import TYPE_CHECKING, Any

from .interfaces.clients import Clients
from .interfaces.clients_all import ClientsAll
from .interfaces.connectivity import Connectivity
from .interfaces.devices import Devices
from .interfaces.dpi_restriction_apps import DPIRestrictionApps
from .interfaces.dpi_restriction_groups import DPIRestrictionGroups
from .interfaces.events import EventHandler
from .interfaces.messages import MessageHandler
from .interfaces.outlets import Outlets
from .interfaces.port_forwarding import PortForwarding
from .interfaces.ports import Ports
from .interfaces.sites import Sites
from .interfaces.system_information import SystemInformationHandler
from .interfaces.wlans import Wlans
from .models.configuration import Configuration
from .websocket import WebsocketSignal, WebsocketState, WSClient

if TYPE_CHECKING:
    from .models.api import ApiRequest, TypedApiResponse

LOGGER = logging.getLogger(__name__)


class Controller:
    """Control a UniFi controller."""

    def __init__(self, config: Configuration) -> None:
        """Session setup."""
        self.connectivity = Connectivity(config)

        self.websocket: WSClient | None = None
        self.ws_state_callback: Callable[[WebsocketState], None] | None = None

        self.messages = MessageHandler(self)
        self.events = EventHandler(self)

        self.clients = Clients(self)
        self.clients_all = ClientsAll(self)
        self.devices = Devices(self)
        self.outlets = Outlets(self)
        self.ports = Ports(self)
        self.dpi_apps = DPIRestrictionApps(self)
        self.dpi_groups = DPIRestrictionGroups(self)
        self.port_forwarding = PortForwarding(self)
        self.sites = Sites(self)
        self.system_information = SystemInformationHandler(self)
        self.wlans = Wlans(self)

        self.update_handlers: tuple[Callable[[], Coroutine[Any, Any, None]], ...] = (
            self.clients.update,
            self.clients_all.update,
            self.devices.update,
            self.dpi_apps.update,
            self.dpi_groups.update,
            self.port_forwarding.update,
            self.sites.update,
            self.system_information.update,
            self.wlans.update,
        )

    async def login(self) -> None:
        """Log in to controller."""
        await self.connectivity.check_unifi_os()
        await self.connectivity.login()

    async def request(self, api_request: "ApiRequest") -> "TypedApiResponse":
        """Make a request to the API, retry login on failure."""
        return await self.connectivity.request(api_request)

    async def initialize(self) -> None:
        """Load UniFi parameters."""
        await asyncio.gather(*[update() for update in self.update_handlers])

    def start_websocket(self) -> None:
        """Start websession and websocket to UniFi."""
        self.websocket = WSClient(
            self.connectivity.config,
            callback=self.session_handler,
            is_unifi_os=self.connectivity.is_unifi_os,
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

        elif signal == WebsocketSignal.CONNECTION_STATE and self.ws_state_callback:
            self.ws_state_callback(self.websocket.state)
