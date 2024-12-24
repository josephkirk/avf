"""Main AssetVersion manager module."""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pydantic import BaseModel

from .metadata import AssetMetadata
from .repository.base import VersionRepository
from .storage.base import StorageBackend
from .utils.history import AssetHistoryDumper

logger = structlog.get_logger()

class VersionIdentifier(BaseModel):
    """Identifier for a specific version in a storage backend"""
    storage_type: str
    storage_id: str
    file_path: Path
    timestamp: datetime
    metadata: AssetMetadata

class AssetVersion:
    def __init__(
        self,
        storage_backends: Dict[str, StorageBackend],
        version_repository: Optional[VersionRepository] = None
    ):
        """Initialize AssetVersion manager

        Args:
            storage_backends: Dictionary of storage backends
            version_repository: Optional version repository for tracking
        """
        self.storage_backends = storage_backends
        self.version_repository = version_repository
        self.logger = logger.bind(module="asset_version")
        self.history_dumper = AssetHistoryDumper(storage_backends)

    def dump_asset_history(
        self,
        file_path: Path,
        include_storage_data: bool = True,
        include_timeline: bool = True,
        version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Dump complete version history of an asset.

        Args:
            file_path: Asset file path
            include_storage_data: Include backend-specific data
            include_timeline: Include history timeline
            version_id: Optional specific version to dump

        Returns:
            Complete version history as dictionary
        """
        # Get basic history from storage backends
        history = self.history_dumper.dump_history(
            file_path,
            include_storage_data,
            include_timeline,
            version_id
        )

        # Add repository data if available
        if self.version_repository:
            try:
                # Get versions from repository
                versions = self.version_repository.find_versions(file_path=file_path)
                if version_id:
                    versions = [v for v in versions if v["id"] == version_id]

                # Add repository versions
                history["repository_versions"] = []

                for version in versions:
                    version_data = {
                        "version_id": version["id"],
                        "creator": version["creator"],
                        "tool_version": version["tool_version"],
                        "description": version["description"],
                        "created_at": version["created_at"].isoformat(),
                        "tags": version["tags"],
                        "custom_data": version["custom_data"],
                    }

                    # Add storage locations
                    if include_storage_data:
                        locations = self.version_repository.get_storage_locations(version["id"])
                        version_data["storage_locations"] = locations

                    history["repository_versions"].append(version_data)

                # Update metadata
                if versions:
                    history["metadata"].update({
                        "repository_latest_version": versions[-1]["id"],
                        "repository_total_versions": len(versions)
                    })

            except Exception as e:
                self.logger.error("Failed to get repository data", error=str(e))
                history["repository_error"] = str(e)

        return history

    # ... rest of the AssetVersion class implementation ...
