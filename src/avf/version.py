from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
import structlog

from .storage.base import StorageBackend
from .repository.base import VersionRepository
from .metadata import AssetMetadata

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
        
    def create_version(
        self, 
        file_path: Path, 
        metadata: Dict[str, Any],
        storage_types: Optional[List[str]] = None
    ) -> Dict[str, VersionIdentifier]:
        """Create a new version across specified storage backends
        
        Args:
            file_path: Path to file to version
            metadata: Version metadata dictionary
            storage_types: Optional list of storage types to use
            
        Returns:
            Dict mapping storage type to version identifier
        """
        if storage_types is None:
            storage_types = list(self.storage_backends.keys())
            
        version_ids = {}
        metadata_obj = AssetMetadata(**metadata)
        
        # Create version in repository if available
        version_id = None
        if self.version_repository:
            try:
                version_id = self.version_repository.create_version(
                    file_path=file_path,
                    creator=metadata_obj.creator,
                    tool_version=metadata_obj.tool_version,
                    description=metadata_obj.description,
                    tags=metadata_obj.tags,
                    custom_data=metadata_obj.custom_data
                )
            except Exception as e:
                self.logger.error("Failed to create version in repository", error=str(e))
                raise
        
        # Store in each backend
        for storage_type in storage_types:
            try:
                storage = self.storage_backends[storage_type]
                storage_id = storage.store_version(file_path, metadata_obj.model_dump())
                
                # Record storage location in repository
                if self.version_repository and version_id:
                    try:
                        self.version_repository.add_storage_location(
                            version_id=version_id,
                            storage_type=storage_type,
                            storage_id=storage_id
                        )
                    except Exception as e:
                        self.logger.error(
                            "Failed to record storage location",
                            storage=storage_type,
                            error=str(e)
                        )
                
                version_ids[storage_type] = VersionIdentifier(
                    storage_type=storage_type,
                    storage_id=storage_id,
                    file_path=file_path,
                    timestamp=datetime.now(),
                    metadata=metadata_obj
                )
            except Exception as e:
                self.logger.error(
                    "Failed to create version in storage",
                    storage=storage_type,
                    error=str(e)
                )
                raise
                
        return version_ids
        
    def get_version(
        self, 
        storage_type: str, 
        version_id: str,
        target_path: Optional[Path] = None
    ) -> Path:
        """Retrieve a specific version from storage
        
        Args:
            storage_type: Type of storage to retrieve from
            version_id: Version identifier
            target_path: Optional path to store retrieved file
            
        Returns:
            Path to retrieved file
        """
        if storage_type not in self.storage_backends:
            raise KeyError(f"Unknown storage type: {storage_type}")
            
        storage = self.storage_backends[storage_type]
        return storage.retrieve_version(version_id, target_path)
        
    def get_version_info(
        self, 
        storage_type: str, 
        version_id: str
    ) -> AssetMetadata:
        """Get version metadata from storage
        
        Args:
            storage_type: Type of storage to query
            version_id: Version identifier
            
        Returns:
            Version metadata
        """
        if storage_type not in self.storage_backends:
            raise KeyError(f"Unknown storage type: {storage_type}")
            
        storage = self.storage_backends[storage_type]
        metadata_dict = storage.get_version_info(version_id)
        return AssetMetadata(**metadata_dict)
        
    def find_versions(
        self,
        file_path: Optional[Path] = None,
        tags: Optional[List[str]] = None,
        creator: Optional[str] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Find versions matching criteria using repository
        
        Args:
            file_path: Optional file path filter
            tags: Optional list of tags to match
            creator: Optional creator name
            after: Optional datetime for versions after
            before: Optional datetime for versions before
            
        Returns:
            List of matching versions
            
        Raises:
            RuntimeError: If no repository is configured
        """
        if not self.version_repository:
            raise RuntimeError("No repository configured for version tracking")
            
        return self.version_repository.find_versions(
            file_path=file_path,
            tags=tags,
            creator=creator,
            after=after,
            before=before
        )
