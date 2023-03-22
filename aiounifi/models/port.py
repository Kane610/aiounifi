"""Device port implementation."""

from dataclasses import dataclass

from .api import ApiItem
from .device import TypedDevicePortTable


@dataclass
class Port2:
    """Network port representation."""

    ifname: str | None
    media: str | None
    name: str
    port_idx: int | None
    poe_class: str | None
    poe_enable: bool | None
    poe_mode: str | None
    poe_power: str | None
    poe_voltage: str | None
    portconf_id: str | None
    port_poe: bool | None
    up: bool | None

    @classmethod
    def from_dict(cls, data: TypedDevicePortTable) -> "Port2":
        """Create data container instance from dict."""
        return cls(
            ifname=data.get("ifname"),  # Port index as name used by USG
            media=data.get("media"),  # Media port is connected to
            name=data["name"],  # Port name
            port_idx=data.get("port_idx"),  # Port index
            poe_class=data.get("poe_class"),  # Port PoE class
            poe_enable=data.get("poe_enable"),  # Is PoE supported/requested by client
            poe_mode=data.get("poe_mode"),  # auto, pasv24, passthrough, off or None
            poe_power=data.get("poe_power"),  # PoE power usage
            poe_voltage=data.get("poe_voltage"),  # PoE voltage usage
            portconf_id=data.get("portconf_id"),  # Port configuration ID
            port_poe=data.get("port_poe"),  # Is PoE used
            up=data.get("up"),  # Is port up
        )


class Port(ApiItem):
    """Represents a network port."""

    raw: TypedDevicePortTable

    @property
    def ifname(self) -> str | None:
        """Port name used by USG."""
        return self.raw.get("ifname")

    @property
    def media(self) -> str | None:
        """Media port is connected to."""
        return self.raw.get("media")

    @property
    def name(self) -> str:
        """Port name."""
        return self.raw["name"]

    @property
    def port_idx(self) -> int | None:
        """Port index."""
        return self.raw.get("port_idx")

    @property
    def poe_class(self) -> str | None:
        """Port POE class."""
        return self.raw.get("poe_class")

    @property
    def poe_enable(self) -> bool | None:
        """Is POE supported/requested by client."""
        return self.raw.get("poe_enable")

    @property
    def poe_mode(self) -> str | None:
        """Is POE auto, pasv24, passthrough, off or None."""
        return self.raw.get("poe_mode")

    @property
    def poe_power(self) -> str | None:
        """POE power usage."""
        return self.raw.get("poe_power")

    @property
    def poe_voltage(self) -> str | None:
        """POE voltage usage."""
        return self.raw.get("poe_voltage")

    @property
    def portconf_id(self) -> str | None:
        """Port configuration ID."""
        return self.raw.get("portconf_id")

    @property
    def port_poe(self) -> bool | None:
        """Is POE used."""
        return self.raw.get("port_poe")

    @property
    def up(self) -> bool | None:
        """Is port up."""
        return self.raw.get("up")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: Poe {self.poe_enable}>"
