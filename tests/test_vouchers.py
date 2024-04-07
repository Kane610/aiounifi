"""Test voucher configuration API.

pytest --cov-report term-missing --cov=aiounifi.voucher tests/test_vouchers.py
"""

from datetime import datetime, timedelta

import pytest

from aiounifi.models.voucher import (
    VoucherCreateRequest,
    VoucherDeleteRequest,
)

from .fixtures import VOUCHERS


async def test_voucher_create(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test create voucher."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/hotspot", payload={})

    await unifi_controller.request(VoucherCreateRequest.create(1, 0, 3600))

    assert unifi_called_with(
        "post",
        "/api/s/default/cmd/hotspot",
        json={
            "cmd": "create-voucher",
            "n": 1,
            "quota": 0,
            "expire_number": 3600,
            "expire_unit": 1,
        },
    )


async def test_voucher_delete(mock_aioresponse, unifi_controller, unifi_called_with):
    """Test create voucher."""
    mock_aioresponse.post("https://host:8443/api/s/default/cmd/hotspot", payload={})

    await unifi_controller.request(
        VoucherDeleteRequest.create("657e370a4543a555901865c7")
    )

    assert unifi_called_with(
        "post",
        "/api/s/default/cmd/hotspot",
        json={
            "cmd": "delete-voucher",
            "_id": "657e370a4543a555901865c7",
        },
    )


@pytest.mark.usefixtures("_mock_endpoints")
async def test_no_vouchers(unifi_controller, _mock_endpoints, unifi_called_with):
    """Test that no ports also work."""
    vouchers = unifi_controller.vouchers
    await vouchers.update()

    assert unifi_called_with("get", "/api/s/default/stat/voucher")
    assert len(vouchers.values()) == 0


@pytest.mark.parametrize("voucher_payload", [VOUCHERS])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_vouchers(
    mock_aioresponse, unifi_controller, _mock_endpoints, unifi_called_with
):
    """Test that different types of ports work."""
    vouchers = unifi_controller.vouchers
    await vouchers.update()
    assert len(vouchers.values()) == 2

    voucher = vouchers["657e370a4543a555901865c7"]
    assert voucher.id == "657e370a4543a555901865c7"
    assert voucher.site_id == "5a32aa4ee4b0412345678910"
    assert voucher.note == "auto-generated"
    assert voucher.code == "74700-75124"
    assert voucher.quota == 1
    assert voucher.duration == timedelta(minutes=480)
    assert voucher.qos_overwrite is False
    assert voucher.qos_usage_quota == 0
    assert voucher.qos_rate_max_up == 0
    assert voucher.qos_rate_max_down == 0
    assert voucher.used == 0
    assert voucher.create_time == datetime.fromtimestamp(1702770442)
    assert voucher.start_time is None
    assert voucher.end_time is None
    assert voucher.for_hotspot is False
    assert voucher.admin_name == "Admin"
    assert voucher.status == "VALID_ONE"
    assert voucher.status_expires == 0
