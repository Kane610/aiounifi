"""Hotspot vouchers as part of a UniFi network."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequest


class TypedVoucher(TypedDict):
    """Voucher type definition."""

    _id: str
    site_id: str
    note: str
    code: str
    quota: int
    duration: float
    qos_overwrite: bool
    qos_usage_quota: NotRequired[str]
    qos_rate_max_up: NotRequired[int]
    qos_rate_max_down: NotRequired[int]
    used: int
    create_time: float
    start_time: NotRequired[float]
    end_time: NotRequired[float]
    for_hotspot: bool
    admin_name: str
    status: str
    status_expires: float


@dataclass
class VoucherListRequest(ApiRequest):
    """Request object for voucher list."""

    @classmethod
    def create(cls) -> Self:
        """Create voucher list request."""
        return cls(
            method="get",
            path="/stat/voucher",
        )


@dataclass
class VoucherCreateRequest(ApiRequest):
    """Request object for voucher create."""

    @classmethod
    def create(
        cls,
        number: int,
        quota: int,
        expire_number: int,
        expire_unit: int = 1,
        usage_quota: int | None = None,
        rate_max_up: int | None = None,
        rate_max_down: int | None = None,
        note: str | None = None,
    ) -> Self:
        """Create voucher create request.

        :param number: number of vouchers
        :param quota: number of using; 0 = unlimited
        :param expire_number: expiration of voucher per expire_unit
        :param expire_unit: scale of expire_number, 1 = minute, 60 = hour, 3600 = day
        :param usage_quota: quantity of bytes allowed in MB
        :param rate_max_up: up speed allowed in kbps
        :param rate_max_down: down speed allowed in kbps
        :param note: description
        """
        data = {
            "cmd": "create-voucher",
            "n": number,
            "quota": quota,
            "expire_number": expire_number,
            "expire_unit": expire_unit,
        }
        if usage_quota:
            data["bytes"] = usage_quota
        if rate_max_up:
            data["up"] = rate_max_up
        if rate_max_down:
            data["down"] = rate_max_down
        if note:
            data["note"] = note

        return cls(
            method="post",
            path="/cmd/hotspot",
            data=data,
        )


@dataclass
class VoucherDeleteRequest(ApiRequest):
    """Request object for voucher delete."""

    @classmethod
    def create(
        cls,
        obj_id: str,
    ) -> Self:
        """Create voucher delete request."""
        data = {
            "cmd": "delete-voucher",
            "_id": obj_id,
        }
        return cls(
            method="post",
            path="/cmd/hotspot",
            data=data,
        )


class Voucher(ApiItem):
    """Represents a voucher."""

    raw: TypedVoucher

    @property
    def id(self) -> str:
        """ID of voucher."""
        return self.raw["_id"]

    @property
    def site_id(self) -> str:
        """Site ID."""
        return self.raw["_id"]

    @property
    def note(self) -> str:
        """Note."""
        return self.raw.get("note") or ""

    @property
    def code(self) -> str:
        """Code."""
        if len(c := self.raw.get("code", "")) > 5:
            return f"{c[:5]}-{c[5:]}"
        return c

    @property
    def quota(self) -> int:
        """Number of uses."""
        return self.raw.get("quota", 0)

    @property
    def duration(self) -> timedelta:
        """Expiration of voucher."""
        return timedelta(minutes=self.raw.get("duration", 0))

    @property
    def qos_overwrite(self) -> bool:
        """Used count."""
        return self.raw.get("qos_overwrite", False)

    @property
    def qos_usage_quota(self) -> int:
        """Quantity of bytes allowed in MB."""
        return int(self.raw.get("qos_usage_quota", 0))

    @property
    def qos_rate_max_up(self) -> int:
        """Up speed allowed in kbps."""
        return int(self.raw.get("qos_rate_max_up", 0))

    @property
    def qos_rate_max_down(self) -> int:
        """Down speed allowed in kbps."""
        return int(self.raw.get("qos_rate_max_down", 0))

    @property
    def used(self) -> int:
        """Number of using; 0 = unlimited."""
        return self.raw.get("used", 0)

    @property
    def create_time(self) -> datetime:
        """Create datetime."""
        return datetime.fromtimestamp(self.raw["create_time"])

    @property
    def start_time(self) -> datetime | None:
        """Start datetime."""
        if "start_time" in self.raw:
            return datetime.fromtimestamp(self.raw["start_time"])

    @property
    def end_time(self) -> datetime | None:
        """End datetime."""
        if "end_time" in self.raw:
            return datetime.fromtimestamp(self.raw["end_time"])

    @property
    def for_hotspot(self) -> bool:
        """For hotspot."""
        return self.raw.get("for_hotspot", False)

    @property
    def admin_name(self) -> str:
        """Admin name."""
        return self.raw.get("admin_name", "")

    @property
    def status(self) -> str:
        """Status."""
        return self.raw.get("status", "")

    @property
    def status_expires(self) -> timedelta | None:
        """Status expires."""
        if (status_expiry := self.raw.get("status_expires", 0.0)) > 0:
            return timedelta(seconds=status_expiry)
        return None
