"""Data models."""

from typing import TypeVar

from .api import ApiItem

ResourceType = TypeVar("ResourceType", bound=ApiItem)
