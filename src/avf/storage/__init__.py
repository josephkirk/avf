"""Storage backends for version management"""

from .base import StorageBackend
from .disk import DiskStorage
from .git import GitStorage

__all__ = [
    "StorageBackend",
    "DiskStorage",
    "GitStorage",
]
