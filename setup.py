"""Setup for aioUnifi"""

from setuptools import setup

setup(
    name="aiounifi",
    packages=["aiounifi"],
    version="28",
    description="An asynchronous Python library for communicating with Unifi Controller API",
    author="Robert Svensson",
    author_email="Kane610@users.noreply.github.com",
    license="MIT",
    url="https://github.com/Kane610/aiounifi",
    download_url="https://github.com/Kane610/aiounifi/archive/v28.tar.gz",
    install_requires=["aiohttp"],
    tests_require=["pytest-asyncio", "pytest-aiohttp", "pytest", "aioresponses"],
    keywords=["unifi", "homeassistant"],
    classifiers=["Natural Language :: English", "Programming Language :: Python :: 3"],
)
