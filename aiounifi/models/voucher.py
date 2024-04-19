"""Hotspot vouchers as part of a UniFi network."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NotRequired, Self, TypedDict

from .api import ApiItem, ApiRequest


class TypedVoucher(TypedDict):
    """Voucher type definition."""

    _id: str
    site_id: str
    note: NotRequired[str]
    code: str
    quota: int
    duration: float
    qos_overwrite: NotRequired[bool]
    qos_usage_quota: NotRequired[str]
    qos_rate_max_up: NotRequired[int]
    qos_rate_max_down: NotRequired[int]
    used: int
    create_time: float
    start_time: NotRequired[float]
    end_time: NotRequired[float]
    for_hotspot: NotRequired[bool]
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
        return self.raw["site_id"]

    @property
    def note(self) -> str:
        """Note given by user to voucher."""
        return self.raw.get("note") or ""

    @property
    def code(self) -> str:
        """Code in known format 00000-00000."""
        if len(c := self.raw.get("code", "")) > 5:
            # API returns the code without a hyphen. But this is necessary. Separate the API string after the fifth digit.
            return f"{c[:5]}-{c[5:]}"
        return c

    @property
    def quota(self) -> int:
        """Allowed uses (0 = unlimited) of voucher."""
        return self.raw["quota"]

    @property
    def duration(self) -> timedelta:
        """Expiration of voucher."""
        return timedelta(minutes=self.raw["duration"])

    @property
    def qos_overwrite(self) -> bool:
        """QoS defaults overwritten by the use of this voucher."""
        return self.raw.get("qos_overwrite", False)

    @property
    def qos_usage_quota(self) -> int:
        """Quantity of bytes (in MB) allowed when using this voucher."""
        return int(self.raw.get("qos_usage_quota", 0))

    @property
    def qos_rate_max_up(self) -> int:
        """Up speed (in kbps) allowed when using this voucher."""
        return self.raw.get("qos_rate_max_up", 0)

    @property
    def qos_rate_max_down(self) -> int:
        """Down speed (in kbps) allowed when using this voucher."""
        return self.raw.get("qos_rate_max_down", 0)

    @property
    def used(self) -> int:
        """Number of uses of this voucher."""
        return self.raw["used"]

    @property
    def create_time(self) -> datetime:
        """Create datetime of voucher."""
        return datetime.fromtimestamp(self.raw["create_time"])

    @property
    def start_time(self) -> datetime | None:
        """Start datetime of first usage of voucher."""
        if "start_time" in self.raw:
            return datetime.fromtimestamp(self.raw["start_time"])
        return None

    @property
    def end_time(self) -> datetime | None:
        """End datetime of latest usage of voucher."""
        if "end_time" in self.raw:
            return datetime.fromtimestamp(self.raw["end_time"])
        return None

    @property
    def for_hotspot(self) -> bool:
        """For hotspot use.

        False
        """
        return self.raw.get("for_hotspot", False)

    @property
    def admin_name(self) -> str:
        """Creator name of voucher."""
        return self.raw["admin_name"]

    @property
    def status(self) -> str:
        """Status of voucher.

        VALID_ONE
        VALID_MULTI
        USED_MULTIPLE
        """
        return self.raw["status"]

    @property
    def status_expires(self) -> timedelta | None:
        """Status expires in seconds."""
        if (status_expiry := self.raw["status_expires"]) > 0:
            return timedelta(seconds=status_expiry)
        return None
