"""Test object-oriented network configuration API.

pytest --cov-report term-missing --cov=aiounifi.models.object_oriented_network_config tests/test_object_oriented_network_configs.py
"""

from copy import deepcopy

import pytest

from aiounifi.models.object_oriented_network_config import (
    ObjectOrientedNetworkConfigUpdateRequest,
    ObjectOrientedNetworkInternetMode,
)

OBJECT_ORIENTED_NETWORK_CONFIGS = [
    {
        "_id": "69f6b0a5e0e3ee2d4614cb5c",
        "enabled": True,
        "name": "Nintendo Switch - Block Internet",
        "target_type": "CLIENTS",
        "targets": ["98:b6:e9:b4:4c:29"],
        "secure": {
            "enabled": True,
            "internet": {
                "mode": "TURN_OFF_INTERNET",
                "schedule": {"mode": "ALWAYS"},
            },
        },
        "qos": {"enabled": False},
        "route": {"enabled": False},
    },
    {
        "_id": "69f6b0eae0e3ee2d4614cb91",
        "enabled": False,
        "name": "TV - Block Internet",
        "target_type": "CLIENTS",
        "targets": ["64:ff:0a:f0:fb:ba"],
        "secure": {
            "enabled": True,
            "internet": {
                "mode": "TURN_OFF_INTERNET",
                "schedule": {"mode": "ALWAYS"},
            },
        },
        "qos": {"enabled": False},
        "route": {"enabled": False},
    },
]


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
async def test_object_oriented_network_config_update_request(
    mock_aioresponse, unifi_controller, unifi_called_with, enable
):
    """Test that object-oriented network configuration can be updated."""
    config_enabled = deepcopy(OBJECT_ORIENTED_NETWORK_CONFIGS[0])
    config_disabled = deepcopy(OBJECT_ORIENTED_NETWORK_CONFIGS[1])

    config = config_disabled if enable else config_enabled
    config_id = config["_id"]
    mock_aioresponse.put(
        (
            "https://host:8443/proxy/network/v2/api/site/default"
            f"/object-oriented-network-config/{config_id}"
        ),
        payload={
            **OBJECT_ORIENTED_NETWORK_CONFIGS[0 if not enable else 1],
            "enabled": enable,
        },
    )

    await unifi_controller.request(
        ObjectOrientedNetworkConfigUpdateRequest.create(config, enable)
    )

    config["enabled"] = enable
    assert unifi_called_with(
        "put",
        f"/proxy/network/v2/api/site/default/object-oriented-network-config/{config_id}",
        json=config,
    )


@pytest.mark.parametrize(
    "object_oriented_network_config_payload", [OBJECT_ORIENTED_NETWORK_CONFIGS]
)
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_toggle(
    mock_aioresponse, unifi_controller, enable
):
    """Test toggle method can enable and disable an object-oriented network configuration."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config_id = OBJECT_ORIENTED_NETWORK_CONFIGS[0 if not enable else 1]["_id"]

    mock_aioresponse.put(
        (
            "https://host:8443/proxy/network/v2/api/site/default"
            f"/object-oriented-network-config/{config_id}"
        ),
        payload={
            **OBJECT_ORIENTED_NETWORK_CONFIGS[0 if not enable else 1],
            "enabled": enable,
        },
    )
    await configs.save(configs[config_id], enable)
    assert configs[config_id].enabled is enable


@pytest.mark.parametrize(
    "object_oriented_network_config_payload", [OBJECT_ORIENTED_NETWORK_CONFIGS]
)
@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.parametrize("enable", [True, False])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_enable_disable(
    mock_aioresponse, unifi_controller, enable
):
    """Test individual methods for enabled and disabled."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config_id = OBJECT_ORIENTED_NETWORK_CONFIGS[0 if not enable else 1]["_id"]
    config_call = configs.enable if enable else configs.disable

    mock_aioresponse.put(
        (
            "https://host:8443/proxy/network/v2/api/site/default"
            f"/object-oriented-network-config/{config_id}"
        ),
        payload={
            **OBJECT_ORIENTED_NETWORK_CONFIGS[0 if not enable else 1],
            "enabled": enable,
        },
    )
    await config_call(configs[config_id])
    assert configs[config_id].enabled is enable


@pytest.mark.parametrize("is_unifi_os", [True])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_no_object_oriented_network_configs(unifi_controller, unifi_called_with):
    """Test that no object-oriented network configurations also work."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()
    assert unifi_called_with(
        "get", "/proxy/network/v2/api/site/default/object-oriented-network-configs"
    )
    assert len(configs.values()) == 0


@pytest.mark.parametrize(
    "object_oriented_network_config_payload", [OBJECT_ORIENTED_NETWORK_CONFIGS]
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_configs(unifi_controller, unifi_called_with):
    """Test that we get the expected object-oriented network configuration."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()
    assert unifi_called_with(
        "get", "/v2/api/site/default/object-oriented-network-configs"
    )
    assert len(configs.values()) == 2

    config = configs["69f6b0a5e0e3ee2d4614cb5c"]
    assert config.id == "69f6b0a5e0e3ee2d4614cb5c"
    assert config.name == "Nintendo Switch - Block Internet"
    assert config.enabled is True
    assert config.target_type == "CLIENTS"
    assert config.targets == ["98:b6:e9:b4:4c:29"]
    assert config.secure.available is True
    assert config.secure.enabled is True
    assert config.secure.internet is not None
    assert (
        config.secure.internet.mode
        == ObjectOrientedNetworkInternetMode.TURN_OFF_INTERNET
    )
    assert config.qos["enabled"] is False
    assert config.route["enabled"] is False


@pytest.mark.parametrize(
    "object_oriented_network_config_payload",
    [
        [
            {
                "_id": "69f6b0a5e0e3ee2d4614cb5c",
                "enabled": True,
                "name": "Nintendo Switch - Block Internet",
                "secure": {
                    "internet": {
                        "mode": "TURN_OFF_INTERNET",
                        "schedule": {"mode": "ALWAYS"},
                    },
                },
                "qos": {},
                "route": {"kill_switch": True},
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_optional_section_defaults(
    unifi_controller,
):
    """Test optional object-oriented network configuration sections."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config = configs["69f6b0a5e0e3ee2d4614cb5c"]
    assert config.target_type is None
    assert config.targets == []
    assert config.secure.available is True
    assert config.secure.enabled is False
    assert config.secure.internet is not None
    assert (
        config.secure.internet.mode
        == ObjectOrientedNetworkInternetMode.TURN_OFF_INTERNET
    )
    assert config.qos["enabled"] is False
    assert config.route["enabled"] is False
    assert config.route["kill_switch"] is True


@pytest.mark.parametrize(
    "object_oriented_network_config_payload",
    [
        [
            {
                "_id": "69f6b0a5e0e3ee2d4614cb5c",
                "enabled": True,
                "name": "Nintendo Switch - Empty Secure",
                "secure": {},
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_secure_empty(unifi_controller):
    """Test empty security configuration is available."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config = configs["69f6b0a5e0e3ee2d4614cb5c"]
    assert config.secure.available is True
    assert config.secure.enabled is False
    assert config.secure.internet is None


@pytest.mark.parametrize(
    "object_oriented_network_config_payload",
    [
        [
            {
                "_id": "69f6b0a5e0e3ee2d4614cb5c",
                "enabled": True,
                "name": "Nintendo Switch - Empty Secure Internet",
                "secure": {"internet": {}},
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_secure_internet_empty(
    unifi_controller,
):
    """Test empty internet configuration uses safe defaults."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config = configs["69f6b0a5e0e3ee2d4614cb5c"]
    assert config.secure.available is True
    assert config.secure.enabled is False
    assert config.secure.internet is not None
    assert config.secure.internet.mode == ObjectOrientedNetworkInternetMode.UNKNOWN
    assert config.secure.internet.schedule is None


@pytest.mark.parametrize(
    "object_oriented_network_config_payload",
    [
        [
            {
                "_id": "69f6b0eae0e3ee2d4614cb91",
                "enabled": True,
                "name": "VPN traffic route",
                "target_type": "NETWORKS",
                "targets": ["6060b00f45de3905133cea14"],
                "route": {"enabled": True},
                "secure": None,
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_secure_null(unifi_controller):
    """Test security configuration with null secure data."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config = configs["69f6b0eae0e3ee2d4614cb91"]
    assert config.secure.available is False
    assert config.secure.enabled is False
    assert config.secure.internet is None


@pytest.mark.parametrize(
    "object_oriented_network_config_payload",
    [
        [
            {
                "_id": "69f6b0a5e0e3ee2d4614cb5c",
                "enabled": True,
                "name": "Nintendo Switch - Unknown Internet Mode",
                "secure": {
                    "enabled": True,
                    "internet": {"mode": "SOMETHING_ELSE"},
                },
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_unknown_internet_mode(unifi_controller):
    """Test unsupported internet mode maps to unknown."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config = configs["69f6b0a5e0e3ee2d4614cb5c"]
    assert config.secure.internet is not None
    assert config.secure.internet.mode == ObjectOrientedNetworkInternetMode.UNKNOWN


@pytest.mark.parametrize(
    "object_oriented_network_config_payload",
    [
        [
            {
                "id": "69f6b0a5e0e3ee2d4614cb5c",
                "enabled": True,
                "name": "Nintendo Switch - Block Internet",
                "target_type": "CLIENTS",
                "targets": [{"type": "MAC", "value": "98:b6:e9:b4:4c:29"}],
                "secure": {
                    "enabled": True,
                    "internet": {
                        "mode": "TURN_OFF_INTERNET",
                        "schedule": {"mode": "ALWAYS"},
                    },
                },
                "qos": {"enabled": False},
                "route": {"enabled": False},
            }
        ]
    ],
)
@pytest.mark.usefixtures("_mock_endpoints")
async def test_object_oriented_network_config_id_alias(unifi_controller):
    """Test configs that use id instead of _id."""
    configs = unifi_controller.object_oriented_network_configs
    await configs.update()

    config = configs["69f6b0a5e0e3ee2d4614cb5c"]
    assert config.id == "69f6b0a5e0e3ee2d4614cb5c"
    assert config.raw["id"] == "69f6b0a5e0e3ee2d4614cb5c"
