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
    username: str | None = None
    password: str | None = None
    port: int = 8443
    site: str = "default"
    ssl_context: SSLContext | Literal[False] = False
    api_key: str = ""

    def __post_init__(self) -> None:
        """Ensure mutually exclusive authentication configuration."""
        if self.api_key and (self.username is not None or self.password is not None):
            raise ValueError(
                "Provide either api_key or username/password credentials, not both"
            )

    @property
    def url(self) -> str:
        """Represent console path."""
        return f"https://{self.host}:{self.port}"
