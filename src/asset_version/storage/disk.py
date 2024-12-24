import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
from .base import StorageBackend

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
