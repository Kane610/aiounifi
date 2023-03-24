"""Setup for AioUnifi."""

from setuptools import find_packages, setup

MIN_PY_VERSION = "3.10"
PACKAGES = find_packages(exclude=["tests", "tests.*"])
VERSION = "45"

setup(
    name="aiounifi",
    packages=PACKAGES,
    package_data={"aiounifi": ["py.typed"]},
    version=VERSION,
    description="An asynchronous Python library for communicating with UniFi Network Controller API",
    author="Robert Svensson",
    author_email="Kane610@users.noreply.github.com",
    license="MIT",
    url="https://github.com/Kane610/aiounifi",
    download_url=f"https://github.com/Kane610/aiounifi/archive/v{VERSION}.tar.gz",
    install_requires=["aiohttp", "async_timeout", "orjson"],
    tests_require=["aioresponses", "pytest", "pytest-asyncio", "pytest-aiohttp"],
    keywords=["unifi", "homeassistant"],
    classifiers=["Natural Language :: English", "Programming Language :: Python :: 3"],
    python_requires=f">={MIN_PY_VERSION}",
)
