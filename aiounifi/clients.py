"""Clients are devices on a UniFi network."""

from .api import APIItems

URL = 's/{site}/stat/sta'


class Clients(APIItems):
    """Represents client network devices."""

    def __init__(self, raw, request):
        super().__init__(raw, request, URL, Client)


class Client:
    """Represents a client network device."""

    def __init__(self, raw, request):
        self.raw = raw
        self._request = request

    @property
    def hostname(self):
        return self.raw.get('hostname')

    @property
    def ip(self):
        return self.raw.get('ip')

    @property
    def is_wired(self):
        return self.raw.get('is_wired')

    @property
    def mac(self):
        return self.raw.get('mac')

    @property
    def name(self):
        return self.raw.get('name')

    @property
    def oui(self):
        return self.raw.get('oui')

    @property
    def site_id(self):
        return self.raw.get('site_id')

    @property
    def sw_mac(self):
        """MAC for switch client is connected to."""
        return self.raw.get('sw_mac')

    @property
    def sw_port(self):
        """Switch port client is connected to."""
        return self.raw.get('sw_port')

    @property
    def wired_rx_bytes(self):
        """Bytes received over wired connection."""
        return self.raw.get('wired-rx_bytes', 0)

    @property
    def wired_tx_bytes(self):
        """Bytes transferred over wired connection."""
        return self.raw.get('wired-tx_bytes', 0)

    def __repr__(self):
        """Return the representation."""
        name = self.name
        if not name:
            name = self.hostname
        return "<Client {}: {} {}\n>".format(name, self.mac, self.raw)
