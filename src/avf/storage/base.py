"""Base classes for storage backends."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .reference import StorageReference


class StorageBackend(ABC):
    """Abstract base class for version control storage backends"""

    @abstractmethod
    def store_version(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Store a new version of the file

        Args:
            file_path: Path to the file to store
            metadata: Version metadata

        Returns:
            Version identifier
        """
        pass

    @abstractmethod
    def retrieve_version(self, version_id: str, target_path: Optional[Path] = None) -> Path:
        """Retrieve a specific version of a file

        Args:
            version_id: Version identifier
            target_path: Optional path to store retrieved file

        Returns:
            Path to retrieved file
        """
        pass

    @abstractmethod
    def get_version_info(self, version_id: str) -> Dict[str, Any]:
        """Get metadata for a specific version

        Args:
            version_id: Version identifier

        Returns:
            Version metadata
        """
        pass

    @abstractmethod
    def create_version_from_reference(
        self,
        reference: StorageReference,
        metadata: Dict[str, Any]
    ) -> str:
        """Create a new version from existing content in storage

        Args:
            reference: Reference to existing content
            metadata: Version metadata

        Returns:
            Version identifier
        """
        pass

    @abstractmethod
    def list_references(
        self,
        reference_type: Optional[str] = None,
        path_pattern: Optional[str] = None
    ) -> List[StorageReference]:
        """List available references in storage

        Args:
            reference_type: Optional filter by reference type
            path_pattern: Optional path pattern to filter

        Returns:
            List of storage references
        """
        pass
