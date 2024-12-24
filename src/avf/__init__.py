"""Asset Version Framework - A comprehensive asset versioning system for game development pipelines"""

from .version import AssetVersion, VersionIdentifier
from .storage import DiskStorage, GitStorage, StorageBackend
from .repository import SQLiteVersionRepository, VersionRepository
from .database import DatabaseConnection
from .metadata import AssetMetadata

__version__ = "0.1.0"

__all__ = [
    "AssetVersion",
    "VersionIdentifier",
    "DiskStorage",
    "GitStorage",
    "StorageBackend",
    "SQLiteVersionRepository",
    "VersionRepository",
    "DatabaseConnection",
    "AssetMetadata",
]
