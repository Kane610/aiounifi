"""Device port implementation."""

from typing import cast

from .api import ApiItem
from .device import TypedDevicePortTable


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
        if (name := self.raw["name"]) == "":
            # Unifi controller allows to set an empty port name, but it
            # shows up as "Port N" consistently across UI. We mirror the
            # behavior, as empty name is rarely visually helpful.
            return f"Port {self.port_idx}"
        return name

    @property
    def port_idx(self) -> int | None:
        """Port index."""
        return self.raw.get("port_idx")

    @property
    def poe_caps(self) -> int | None:
        """Port PoE capabilities.

        0 - no caps
        3 - auto (PoE/PoE+)
        35 - auto (Poe/PoE+/PoE++)
        7 - 24V passive
        8 - Passthrough
        """
        return self.raw.get("poe_caps")

    @property
    def poe_class(self) -> str | None:
        """Port PoE class."""
        return self.raw.get("poe_class")

    @property
    def poe_enable(self) -> bool | None:
        """Is PoE supported/requested by client."""
        return self.raw.get("poe_enable")

    @property
    def poe_mode(self) -> str | None:
        """Is PoE auto, pasv24, passthrough, off or None."""
        return self.raw.get("poe_mode")

    @property
    def poe_power(self) -> str | None:
        """Is PoE power usage."""
        return self.raw.get("poe_power")

    @property
    def poe_voltage(self) -> str | None:
        """Is PoE voltage usage."""
        return self.raw.get("poe_voltage")

    @property
    def portconf_id(self) -> str | None:
        """Port configuration ID."""
        return self.raw.get("portconf_id")

    @property
    def port_poe(self) -> bool | None:
        """Is PoE used."""
        return self.raw.get("port_poe")

    @property
    def rx_bytes(self) -> int:
        """Bytes received."""
        return self.raw.get("rx_bytes", 0)

    @property
    def rx_bytes_r(self) -> int:
        """Bytes recently received."""
        return cast(int, self.raw.get("rx_bytes-r", 0))

    @property
    def tx_bytes(self) -> int:
        """Bytes transferred."""
        return self.raw.get("tx_bytes", 0)

    @property
    def tx_bytes_r(self) -> int:
        """Bytes recently transferred."""
        return cast(int, self.raw.get("tx_bytes-r", 0))

    @property
    def up(self) -> bool | None:
        """Is port up."""
        return self.raw.get("up")

    @property
    def enabled(self) -> bool | None:
        """Is port enabled."""
        return self.raw.get("enable")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: Poe {self.poe_enable}>"
