"""Simple UniFi connection tester using aiounifi.

Usage examples:

- CLI args:
  python scripts/test_unifi_connection.py 192.168.1.1 username password --site default --port 8443 --insecure

- Environment variables (override with CLI):
  UNIFI_HOST=192.168.1.1 \
  UNIFI_USERNAME=username \
  UNIFI_PASSWORD=password \
  UNIFI_SITE=default \
  UNIFI_PORT=443 \
  UNIFI_INSECURE=1 \
  python scripts/test_unifi_connection.py

Notes:
- Use --insecure or UNIFI_INSECURE=1 for self-signed certs on UniFi consoles.
- You can also provide an API key via --api-key or UNIFI_API_KEY to skip username/password login.

"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import ssl
from ssl import SSLContext

import aiohttp

import aiounifi
from aiounifi.controller import Controller
from aiounifi.models.configuration import Configuration

LOGGER = logging.getLogger("aiounifi.connection_test")


async def connect_and_fetch(
    host: str,
    username: str,
    password: str,
    port: int,
    site: str,
    insecure: bool,
    api_key: str | None,
) -> int:
    """Attempt to connect and print basic system info.

    Returns process exit code: 0 on success, non-zero on failure.
    """
    cookie_jar = aiohttp.CookieJar(unsafe=True)
    session = aiohttp.ClientSession(cookie_jar=cookie_jar)

    # Configure SSL policy: verify by default using a system trust store, or disable if requested.
    ssl_context: SSLContext | bool
    ssl_context = False if insecure else ssl.create_default_context()

    config = Configuration(
        session=session,
        host=host,
        username=None if api_key else username,
        password=None if api_key else password,
        port=port,
        site=site,
        ssl_context=ssl_context if ssl_context is not None else False,
        api_key=api_key or "",
    )

    controller = Controller(config)

    try:
        await controller.login()

        # Always resolve the site list first to verify/normalize the provided site token.
        # Some environments require the hidden/site id (attr_hidden_id) for API paths.
        await controller.sites.update()
        sites = list(controller.sites.values())
        # Build lookup maps
        hidden_to_name = {s.hidden_id: s.name for s in sites}
        name_to_hidden = {s.name: s.hidden_id for s in sites}

        # Normalize provided site against available options
        desired = site
        resolved_hidden: str | None = None
        if desired in hidden_to_name:
            resolved_hidden = desired
        elif desired in name_to_hidden:
            resolved_hidden = name_to_hidden[desired]
        else:
            # Try case-insensitive match on hidden_id and name
            low = desired.lower()
            for h in hidden_to_name:
                if h.lower() == low:
                    resolved_hidden = h
                    break
            if resolved_hidden is None:
                for n, h in name_to_hidden.items():
                    if n.lower() == low:
                        resolved_hidden = h
                        break

        if resolved_hidden is None and sites:
            # Fallback to first site
            resolved_hidden = sites[0].hidden_id
            LOGGER.warning(
                "Provided site '%s' not found; falling back to '%s'",
                site,
                resolved_hidden,
            )

        if resolved_hidden:
            # Update configuration site for subsequent requests
            controller.connectivity.config.site = resolved_hidden
            LOGGER.debug("Using site token: %s", resolved_hidden)

        # Fetch system information now that site is normalized
        await controller.system_information.update()

        # Print basic details
        sysinfo = next(iter(controller.system_information.values()), None)
        if sysinfo is None:
            LOGGER.warning("Connected but no system information returned")
        else:
            LOGGER.info("Connected to UniFi controller")
            LOGGER.info("- Name: %s", sysinfo.name)
            LOGGER.info("- Version: %s", sysinfo.version)
            LOGGER.info("- Hostname: %s", sysinfo.hostname)
            LOGGER.info(
                "- IPs: %s",
                ", ".join(sysinfo.ip_address) if sysinfo.ip_address else "n/a",
            )
            LOGGER.info("- Device type: %s", sysinfo.device_type)

        site_names = [s.name for s in controller.sites.values()]
        if site_names:
            LOGGER.info("Sites: %s", ", ".join(site_names))
        else:
            LOGGER.info("Sites: none returned")

        return 0

    except aiounifi.LoginRequired:
        LOGGER.error("Login failed: unauthorized or 2FA required")
        return 2
    except aiounifi.Unauthorized:
        LOGGER.error("Unauthorized: account not registered on console")
        return 3
    except (TimeoutError, aiounifi.RequestError) as err:
        LOGGER.error("Connection error: %s", err)
        return 4
    except aiounifi.AiounifiException as err:
        LOGGER.error("UniFi API error: %s", err)
        return 5
    except Exception as err:  # fallback
        LOGGER.exception("Unexpected error: %s", err)
        return 10
    finally:
        await session.close()


def env_bool(name: str, default: bool = False) -> bool:
    """Read an environment variable as a boolean.

    Accepts 1/true/yes/on (case-insensitive) as True, otherwise False.
    """
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def main() -> None:
    """Parse arguments and run the connection test."""
    parser = argparse.ArgumentParser(description="Test connection to UniFi console")
    parser.add_argument(
        "host",
        nargs="?",
        default=os.getenv("UNIFI_HOST", ""),
        help="Controller hostname or IP (env: UNIFI_HOST)",
    )
    parser.add_argument(
        "username",
        nargs="?",
        default=os.getenv("UNIFI_USERNAME", ""),
        help="Username (env: UNIFI_USERNAME)",
    )
    parser.add_argument(
        "password",
        nargs="?",
        default=os.getenv("UNIFI_PASSWORD", ""),
        help="Password (env: UNIFI_PASSWORD)",
    )
    parser.add_argument("--site", default=os.getenv("UNIFI_SITE", "default"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("UNIFI_PORT", "8443")),
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        default=env_bool("UNIFI_INSECURE", False),
        help="Disable SSL verification (for self-signed certs)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("UNIFI_API_KEY", ""),
        help="API key for token-based auth (skips username/password login)",
    )
    parser.add_argument("-D", "--debug", action="store_true")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    if not args.host:
        parser.error("host is required (arg or UNIFI_HOST)")
    if not args.api_key and (not args.username or not args.password):
        parser.error("username and password are required unless --api-key is provided")

    exit_code = asyncio.run(
        connect_and_fetch(
            host=args.host,
            username=args.username,
            password=args.password,
            port=args.port,
            site=args.site,
            insecure=args.insecure,
            api_key=args.api_key or None,
        )
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
