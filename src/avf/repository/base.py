from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class VersionRepository(ABC):
    @abstractmethod
    def create_version(
        self,
        file_path: Path,
        creator: str,
        tool_version: str,
        description: Optional[str],
        tags: List[str],
        custom_data: Dict[str, Any],
    ) -> int:
        """Create a new version entry

        Args:
            file_path: Path to the versioned file
            creator: Name of the creator
            tool_version: Version of the tool used
            description: Optional description
            tags: List of tags
            custom_data: Additional metadata

        Returns:
            Version ID
        """
        pass

    @abstractmethod
    def add_storage_location(self, version_id: int, storage_type: str, storage_id: str) -> None:
        """Add storage location for a version

        Args:
            version_id: Version ID
            storage_type: Type of storage (e.g., 'disk', 'git')
            storage_id: Backend-specific identifier
        """
        pass

    @abstractmethod
    def get_version_info(self, version_id: int) -> Dict[str, Any]:
        """Get version information

        Args:
            version_id: Version ID

        Returns:
            Version metadata
        """
        pass

    @abstractmethod
    def get_storage_locations(self, version_id: int) -> List[Dict[str, Any]]:
        """Get all storage locations for a version

        Args:
            version_id: Version ID

        Returns:
            List of storage locations
        """
        pass

    @abstractmethod
    def find_versions(
        self,
        file_path: Optional[Path] = None,
        tags: Optional[List[str]] = None,
        creator: Optional[str] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Find versions matching criteria

        Args:
            file_path: Optional file path filter
            tags: Optional list of tags to match
            creator: Optional creator name
            after: Optional datetime for versions after
            before: Optional datetime for versions before

        Returns:
            List of matching versions
        """
        pass
