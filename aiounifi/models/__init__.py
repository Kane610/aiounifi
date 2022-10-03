"""Data models."""

from typing import TypeVar

from .api import APIItem

ResourceType = TypeVar("ResourceType", bound=APIItem)
