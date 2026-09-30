"""UniFi devices."""

from __future__ import annotations

from ..api_handlers import APIHandler
from ..models.client import normalize_mac
from ..models.device import (
    Device,
    DeviceActionRequest,
    DeviceStatistics,
    GetDeviceRequest,
    GetDeviceStatisticsRequest,
    ListDevicesRequest,
    PortActionRequest,
)


class Devices(APIHandler[Device]):
    """Devices adopted on the active site, keyed by MAC address."""

    item_cls = Device
    obj_id_key = "macAddress"

    def normalize_obj_id(self, obj_id: str) -> str:
        """Canonical MAC address."""
        return normalize_mac(obj_id)

    def list_request(self, offset: int, limit: int) -> ListDevicesRequest:
        """Return the list request for one page."""
        return ListDevicesRequest.create(self.api_client.site_id, offset, limit)

    async def list_page(
        self,
        offset: int = 0,
        limit: int = 25,
        filter_value: str | None = None,
    ) -> list[Device]:
        """Return one page of devices without touching the cache."""
        response = await self.api_client.request(
            ListDevicesRequest.create(
                self.api_client.site_id, offset, limit, filter_value
            )
        )
        return [Device(raw) for raw in response["data"]]

    async def get_details(self, device_id: str) -> Device:
        """Fetch one device with its ports, radios and uplink.

        The result replaces the cached item of the same MAC, so `ports` and
        `radios` stay available from the cache until the next `update`.
        """
        response = await self.api_client.request(
            GetDeviceRequest.create(self.api_client.site_id, device_id)
        )
        raw = response["data"][0]
        self.process_item(raw)
        return Device(raw)

    async def get_statistics(self, device_id: str) -> DeviceStatistics:
        """Fetch the latest statistics of one device."""
        response = await self.api_client.request(
            GetDeviceStatisticsRequest.create(self.api_client.site_id, device_id)
        )
        return DeviceStatistics(response["data"][0])

    async def restart(self, device_id: str) -> None:
        """Restart a device."""
        await self.api_client.request(
            DeviceActionRequest.create_restart(self.api_client.site_id, device_id)
        )

    async def power_cycle_port(self, device_id: str, port_idx: int) -> None:
        """Power cycle the PoE output of one port."""
        await self.api_client.request(
            PortActionRequest.create_power_cycle(
                self.api_client.site_id, device_id, port_idx
            )
        )
