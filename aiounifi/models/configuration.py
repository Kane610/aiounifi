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
    username: str
    password: str
    port: int = 8443
    site: str = "default"
    ssl_context: SSLContext | Literal[False] = False

    @property
    def url(self) -> str:
        """Represent console path."""
        return f"https://{self.host}:{self.port}"
