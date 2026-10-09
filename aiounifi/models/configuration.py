"""Python library to enable integration between Home Assistant and UniFi."""

from dataclasses import KW_ONLY, dataclass
from ssl import SSLContext
from typing import Literal

from aiohttp import ClientSession


@dataclass
class Configuration:
    """Console configuration."""

    session: ClientSession
    host: str
    _: KW_ONLY
    username: str = ""
    password: str = ""
    port: int = 8443
    site: str = "default"
    ssl_context: SSLContext | Literal[False] = False
    totp_secret: str | None = None
    api_key: str | None = None
    """Key from Network > Integrations in the console.

    Authenticates the Network API v1 (`Controller.network`) on its own; the
    legacy interfaces still need `username` and `password`.
    """

    @property
    def url(self) -> str:
        """Represent console path."""
        return f"https://{self.host}:{self.port}"
