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
from .interfaces.traffic_routes import TrafficRoutes
from .interfaces.traffic_rules import TrafficRules
from .interfaces.wlans import Wlans
from .models.configuration import Configuration

if TYPE_CHECKING:
    from .models.api import ApiRequest, TypedApiResponse

LOGGER = logging.getLogger(__name__)


class Controller:
    """Control a UniFi controller."""

    def __init__(self, config: Configuration) -> None:
        """Session setup."""
        self.connectivity = Connectivity(config)

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
        self.traffic_rules = TrafficRules(self)
        self.traffic_routes = TrafficRoutes(self)
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
            self.traffic_rules.update,
            self.traffic_routes.update,
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
        results = await asyncio.gather(
            *[update() for update in self.update_handlers],
            return_exceptions=True,
        )
        for result in results:
            if result is not None:
                LOGGER.warning("Exception on update %s", result)

    async def start_websocket(self) -> None:
        """Start websocket session."""
        await self.connectivity.websocket(self.messages.new_data)
