"""Device port implementation."""

from __future__ import annotations

from .device import TypedDevicePortTable


# from dataclasses import dataclass

# @dataclass
# def port():


class Port:
    """Represents a network port."""

    def __init__(self, raw: TypedDevicePortTable) -> None:
        """Initialize port."""
        self.raw = raw

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
    def port_poe(self) -> bool:
        """Is POE used."""
        return self.raw.get("port_poe")

    @property
    def up(self) -> bool | None:
        """Is port up."""
        return self.raw.get("up")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<{self.name}: Poe {self.poe_enable}>"
