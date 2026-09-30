"""UniFi Network Integration API v1.

Authenticates with an API key created in the UniFi console under
Network > Integrations. Unlike the legacy REST interfaces this needs no
local user, which makes it the only path on consoles joined to a UniFi
fabric, where local users cannot be created.
"""

from .api_client import ApiClient
from .interfaces import Clients, Devices, Sites

__all__ = ["ApiClient", "Clients", "Devices", "Sites"]
