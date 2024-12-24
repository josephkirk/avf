"""Disk-based storage backend implementation."""
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
from .base import StorageBackend
from .reference import StorageReference, ReferenceType

class DiskStorage(StorageBackend):
    def __init__(self, storage_root: Path):
        """Initialize disk storage
        
        Args:
            storage_root: Root directory for version storage
        """
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.metadata_root = self.storage_root / "_metadata"
        self.metadata_root.mkdir(exist_ok=True)
        
    def _create_version_id(self, file_path: Path, timestamp: datetime) -> str:
        """Create a unique version ID based on file path and timestamp"""
        content_hash = hashlib.sha256()
        content_hash.update(file_path.read_bytes())
        timestamp_str = timestamp.isoformat()
        return f"{content_hash.hexdigest()}_{timestamp_str}"
        
    def _get_version_path(self, version_id: str) -> Path:
        """Get storage path for a version"""
        return self.storage_root / version_id[:2] / version_id[2:4] / version_id
        
    def _get_metadata_path(self, version_id: str) -> Path:
        """Get metadata path for a version"""
        return self.metadata_root / f"{version_id}.json"
        
    def store_version(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Store a new version on disk
        
        Args:
            file_path: Path to file to store
            metadata: Version metadata
            
        Returns:
            Version identifier
        """
        timestamp = datetime.now()
        version_id = self._create_version_id(file_path, timestamp)
        version_path = self._get_version_path(version_id)
        metadata_path = self._get_metadata_path(version_id)
        
        # Create version directory
        version_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file to version storage
        shutil.copy2(file_path, version_path)
        
        # Store metadata
        metadata.update({
            "original_path": str(file_path),
            "timestamp": timestamp.isoformat()
        })
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        return version_id
        
    def retrieve_version(self, version_id: str, target_path: Optional[Path] = None) -> Path:
        """Retrieve a specific version
        
        Args:
            version_id: Version identifier
            target_path: Optional path to store retrieved file
            
        Returns:
            Path to retrieved file
        """
        version_path = self._get_version_path(version_id)
        
        if not version_path.exists():
            raise FileNotFoundError(f"Version {version_id} not found")
            
        if target_path is None:
            return version_path
            
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(version_path, target_path)
        return target_path
        
    def get_version_info(self, version_id: str) -> Dict[str, Any]:
        """Get metadata for a specific version
        
        Args:
            version_id: Version identifier
            
        Returns:
            Version metadata
        """
        metadata_path = self._get_metadata_path(version_id)
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata for version {version_id} not found")
            
        return json.loads(metadata_path.read_text())

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
            
        Raises:
            ValueError: If reference type is not supported
            FileNotFoundError: If referenced file doesn't exist
        """
        if reference.reference_type != ReferenceType.FILE:
            raise ValueError(f"Unsupported reference type: {reference.reference_type}")
        
        file_path = Path(reference.path)
        if not file_path.exists():
            raise FileNotFoundError(f"Referenced file not found: {file_path}")
        
        # Create version using existing file
        timestamp = datetime.now()
        version_id = reference.storage_id or self._create_version_id(file_path, timestamp)
        version_path = self._get_version_path(version_id)
        metadata_path = self._get_metadata_path(version_id)
        
        if not version_path.parent.exists():
            version_path.parent.mkdir(parents=True)
            
        # Link or copy the file if it's not already in the correct location
        if version_path != file_path:
            try:
                # Try to create a hard link first
                version_path.hardlink_to(file_path)
            except OSError:
                # Fall back to copy if hard link fails
                shutil.copy2(file_path, version_path)
        
        # Store metadata
        metadata.update({
            "original_path": str(file_path),
            "timestamp": timestamp.isoformat(),
            "reference": reference.model_dump()
        })
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        return version_id

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
        refs = []
        if reference_type and reference_type != ReferenceType.FILE:
            return refs
            
        # Walk through storage directory
        for version_path in self.storage_root.rglob("*"):
            if version_path.is_file() and not version_path.name.endswith(".json"):
                # Skip if pattern doesn't match
                if path_pattern and path_pattern not in str(version_path):
                    continue
                    
                file_hash = hashlib.sha256()
                file_hash.update(version_path.read_bytes())
                
                refs.append(StorageReference(
                    storage_type="disk",
                    storage_id=file_hash.hexdigest(),
                    path=version_path,
                    reference_type=ReferenceType.FILE,
                    metadata={
                        "size": version_path.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            version_path.stat().st_mtime
                        ).isoformat()
                    }
                ))
                
        return refs