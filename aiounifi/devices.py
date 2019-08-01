"""UniFi devices are network infrastructure.

Access points, Gateways, Switches.
"""

import logging

from .api import APIItems

LOGGER = logging.getLogger(__name__)

URL = 's/{site}/stat/device'


class Devices(APIItems):
    """Represents network devices."""

    def __init__(self, raw, request):
        super().__init__(raw, request, URL, Device)


class Device:
    """Represents a network device."""

    def __init__(self, raw, request):
        self._raw = raw
        self.ports = Ports(raw.get('port_table', []))
        self._request = request

    @property
    def raw(self):
        return self._raw

    @raw.setter
    def raw(self, raw):
        self._raw = raw
        self.ports.update(raw.get('port_table', []))

    @property
    def board_rev(self):
        return self.raw['board_rev']

    @property
    def disabled(self):
        return self.raw.get('disabled', False)

    @property
    def id(self):
        return self.raw['device_id']

    @property
    def ip(self):
        return self.raw['ip']

    @property
    def fan_level(self):
        return self.raw.get('fan_level')

    @property
    def has_fan(self):
        return self.raw.get('has_fan', False)

    @property
    def last_seen(self):
        return self.raw.get('last_seen')

    @property
    def mac(self):
        return self.raw['mac']

    @property
    def model(self):
        return self.raw['model']

    @property
    def name(self):
        return self.raw['name']

    @property
    def overheating(self):
        return self.raw.get('overheating')

    @property
    def port_overrides(self):
        return self.raw['port_overrides']

    @property
    def port_table(self):
        return self.raw.get('port_table', [])

    @property
    def type(self):
        return self.raw['type']

    @property
    def version(self):
        return self.raw['version']

    @property
    def upgradable(self):
        return self.raw['upgradable']

    async def async_set_port_poe_mode(self, port_idx, mode):
        """Set port poe mode.

        Auto, 24v, passthrough, off.
        Make sure to not overwrite any existing configs.
        """
        LOGGER.debug("Override port %d with mode %s", port_idx, mode)

        no_existing_config = True
        for port_override in self.port_overrides:
            if port_idx == port_override['port_idx']:
                port_override['poe_mode'] = mode
                no_existing_config = False
                break

        if no_existing_config:
            self.port_overrides.append({
                'port_idx': port_idx,
                'portconf_id': self.ports[port_idx].portconf_id,
                'poe_mode': mode
            })

        url = 's/{site}/rest/device/' + self.id
        data = {'port_overrides': self.port_overrides}

        await self._request('put', url, json=data)

    def __repr__(self):
        """Return the representation."""
        return "<Device {}: {}>".format(self.name, self.mac)


class Ports:
    """Represents ports on a device."""

    def __init__(self, raw_list):
        self.ports = {}
        for raw in raw_list:
            port = Port(raw)
            index = None
            if port.port_idx is not None:
                index = port.port_idx
            elif port.ifname is not None:
                index = port.ifname
            if index is not None:
                self.ports[index] = port

    def update(self, raw_list):
        for raw in raw_list:
            index = None

            if 'port_idx' in raw:
                index = raw['port_idx']

            elif 'ifname' in raw:
                index = raw['ifname']

            if index in self.ports:
                self.ports[index].raw = raw

    def values(self):
        return self.ports.values()

    def __getitem__(self, obj_id):
        return self.ports[obj_id]

    def __iter__(self):
        return iter(self.ports)


class Port:
    """Represents a network port."""

    def __init__(self, raw):
        self.raw = raw

    @property
    def ifname(self):
        """Used by USG."""
        return self.raw.get('ifname')

    @property
    def media(self):
        return self.raw['media']

    @property
    def name(self):
        return self.raw['name']

    @property
    def port_idx(self):
        return self.raw.get('port_idx')

    @property
    def poe_class(self):
        return self.raw.get('poe_class')

    @property
    def poe_enable(self):
        """Indicates if Poe is supported/requested by client."""
        return self.raw.get('poe_enable')

    @property
    def poe_mode(self):
        """Indicates if Poe is auto, pasv24, passthrough, off or None"""
        return self.raw.get('poe_mode')

    @property
    def poe_power(self):
        return self.raw.get('poe_power')

    @property
    def poe_voltage(self):
        return self.raw.get('poe_voltage')

    @property
    def portconf_id(self):
        return self.raw['portconf_id']

    @property
    def port_poe(self):
        return self.raw.get('port_poe') is True

    @property
    def up(self):
        return self.raw.get('up')

    def __repr__(self):
        """Return the representation."""
        return "<{}: Poe {}>".format(self.name, self.poe_enable)
