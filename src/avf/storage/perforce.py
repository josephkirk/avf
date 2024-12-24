"""Perforce-based storage backend implementation."""
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from P4 import P4, P4Exception  # type: ignore
import tempfile
import shutil
import os

from .base import StorageBackend
from .reference import StorageReference, ReferenceType

class PerforceStorage(StorageBackend):
    def __init__(
        self, 
        port: str,
        user: str,
        client: str,
        workspace_root: Path,
        password: Optional[str] = None,
        charset: str = "none"
    ):
        """Initialize Perforce storage
        
        Args:
            port: Perforce server port (host:port)
            user: Perforce username
            client: Perforce client/workspace name
            workspace_root: Local workspace root path
            password: Optional password
            charset: Character set for server communication
        """
        self.workspace_root = Path(workspace_root)
        self.p4 = P4()
        self.p4.port = port
        self.p4.user = user
        self.p4.client = client
        if password:
            self.p4.password = password
        self.p4.charset = charset
        
        # Verify connection and workspace
        try:
            self.p4.connect()
            client_spec = self.p4.fetch_client()
            if not client_spec:
                raise RuntimeError(f"Client {client} not found")
                
            # Create metadata depot path if it doesn't exist
            self.metadata_path = "//depot/asset_versions/metadata"
            try:
                self.p4.run("depot", "-o", "asset_versions")
            except P4Exception:
                # Create metadata depot if it doesn't exist
                depot_spec = {
                    "Owner": user,
                    "Description": "Asset version metadata storage",
                    "Type": "local",
                    "Map": "asset_versions/..."
                }
                self.p4.save_depot("asset_versions", depot_spec)
                
        except P4Exception as e:
            raise RuntimeError(f"Failed to initialize Perforce connection: {e}")
        finally:
            self.p4.disconnect()
            
    def _connect(self):
        """Establish Perforce connection"""
        self.p4.connect()
        return self.p4
        
    def _get_metadata_path(self, version_id: str) -> str:
        """Get metadata file path in Perforce"""
        return f"{self.metadata_path}/{version_id}.json"
        
    def store_version(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Store a new version in Perforce
        
        Args:
            file_path: Path to file to store
            metadata: Version metadata
            
        Returns:
            Version identifier (changelist number)
        """
        p4 = self._connect()
        try:
            # Create new changelist
            change_spec = {
                "Description": f"Store version of {file_path.name}\n\nManaged by AVF",
                "Files": []
            }
            result = p4.save_change(change_spec)
            changelist = result[0].split()[1]  # Get changelist number
            
            # Add file to Perforce if not already there
            depot_path = f"//depot/{file_path.name}"
            try:
                p4.run("add", "-c", changelist, str(file_path))
            except P4Exception:
                # File might already exist, try edit
                p4.run("edit", "-c", changelist, str(file_path))
                
            # Store metadata
            metadata.update({
                "original_path": str(file_path),
                "changelist": changelist,
                "timestamp": datetime.now().isoformat()
            })
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                json.dump(metadata, tf, indent=2)
                metadata_file = tf.name
                
            try:
                metadata_depot_path = self._get_metadata_path(changelist)
                p4.run("add", "-c", changelist, "-t", "text", metadata_file, metadata_depot_path)
            except P4Exception as e:
                os.unlink(metadata_file)
                raise RuntimeError(f"Failed to store metadata: {e}")
                
            # Submit changelist
            p4.run_submit("-c", changelist)
            
            return changelist
            
        except P4Exception as e:
            raise RuntimeError(f"Failed to store version in Perforce: {e}")
        finally:
            if 'metadata_file' in locals():
                os.unlink(metadata_file)
            p4.disconnect()

    def retrieve_version(self, version_id: str, target_path: Optional[Path] = None) -> Path:
        """Retrieve a specific version
        
        Args:
            version_id: Version identifier (changelist number)
            target_path: Optional path to store retrieved file
            
        Returns:
            Path to retrieved file
        """
        p4 = self._connect()
        try:
            # Get files in changelist
            files = p4.run_files(f"@={version_id}")
            if not files:
                raise FileNotFoundError(f"No files found in changelist {version_id}")
                
            # Filter out metadata files
            asset_files = [f for f in files if not str(f['depotFile']).startswith(self.metadata_path)]
            if not asset_files:
                raise FileNotFoundError(f"No asset files found in changelist {version_id}")
                
            # Get the file
            depot_file = asset_files[0]['depotFile']
            if target_path:
                p4.run_print("-o", str(target_path), f"{depot_file}@{version_id}")
                result_path = target_path
            else:
                # Use workspace path
                local_path = p4.run_fstat(f"{depot_file}@{version_id}")[0]['clientFile']
                p4.run_sync(f"{depot_file}@{version_id}")
                result_path = Path(local_path)
                
            return result_path
            
        except P4Exception as e:
            raise RuntimeError(f"Failed to retrieve version from Perforce: {e}")
        finally:
            p4.disconnect()
            
    def get_version_info(self, version_id: str) -> Dict[str, Any]:
        """Get metadata for a specific version
        
        Args:
            version_id: Version identifier (changelist number)
            
        Returns:
            Version metadata
        """
        p4 = self._connect()
        try:
            metadata_path = self._get_metadata_path(version_id)
            
            # Get metadata file content
            try:
                content = p4.run_print(f"{metadata_path}@{version_id}")[1]
                metadata = json.loads(content)
                
                # Add Perforce-specific information
                change = p4.run_describe(version_id)[0]
                metadata.update({
                    "changelist": version_id,
                    "description": change.get('desc', ''),
                    "user": change.get('user', ''),
                    "client": change.get('client', ''),
                    "time": change.get('time', '')
                })
                
                return metadata
                
            except P4Exception as e:
                raise FileNotFoundError(f"Metadata for version {version_id} not found: {e}")
                
        finally:
            p4.disconnect()
            
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
            Version identifier (changelist number)
            
        Raises:
            ValueError: If reference type is not supported
            P4Exception: If Perforce operation fails
        """
        if reference.reference_type != ReferenceType.CHANGELIST:
            raise ValueError(f"Unsupported reference type: {reference.reference_type}")
            
        p4 = self._connect()
        try:
            # Verify the changelist exists
            changes = p4.run_describe(reference.storage_id)
            if not changes:
                raise ValueError(f"Changelist {reference.storage_id} not found")
                
            change = changes[0]
            
            # Create new changelist for metadata
            change_spec = {
                "Description": f"Add metadata for {reference.path}\n\nReferencing CL: {reference.storage_id}",
                "Files": []
            }
            result = p4.save_change(change_spec)
            new_changelist = result[0].split()[1]
            
            # Add metadata
            metadata.update({
                "original_changelist": reference.storage_id,
                "original_path": str(reference.path),
                "reference": reference.model_dump(),
                "timestamp": datetime.now().isoformat(),
                "source_change": {
                    "description": change.get('desc', ''),
                    "user": change.get('user', ''),
                    "client": change.get('client', ''),
                    "time": change.get('time', '')
                }
            })
            
            # Store metadata
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                json.dump(metadata, tf, indent=2)
                metadata_file = tf.name
                
            try:
                metadata_depot_path = self._get_metadata_path(new_changelist)
                p4.run("add", "-c", new_changelist, "-t", "text", metadata_file, metadata_depot_path)
                p4.run_submit("-c", new_changelist)
            except P4Exception as e:
                os.unlink(metadata_file)
                raise RuntimeError(f"Failed to store metadata: {e}")
                
            return new_changelist
            
        except P4Exception as e:
            raise RuntimeError(f"Failed to create version from Perforce reference: {e}")
        finally:
            if 'metadata_file' in locals():
                os.unlink(metadata_file)
            p4.disconnect()
            
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
        if reference_type and reference_type != ReferenceType.CHANGELIST:
            return []
            
        p4 = self._connect()
        refs = []
        
        try:
            # Get changelists excluding metadata-only changes
            changes = p4.run_changes("-l", "//depot/...")
            
            for change in changes:
                changelist = change['change']
                
                # Get files in changelist
                files = p4.run_files(f"@={changelist}")
                asset_files = [f for f in files if not str(f['depotFile']).startswith(self.metadata_path)]
                
                # Skip metadata-only changes
                if not asset_files:
                    continue
                    
                # Create reference for each file
                for file in asset_files:
                    depot_path = file['depotFile']
                    if path_pattern and path_pattern not in depot_path:
                        continue
                        
                    refs.append(StorageReference(
                        storage_type="perforce",
                        storage_id=changelist,
                        path=Path(depot_path),
                        reference_type=ReferenceType.CHANGELIST,
                        metadata={
                            "description": change.get('desc', ''),
                            "user": change.get('user', ''),
                            "client": change.get('client', ''),
                            "time": change.get('time', ''),
                            "action": file.get('action', '')
                        }
                    ))
                    
        except P4Exception as e:
            raise RuntimeError(f"Failed to list Perforce references: {e}")
        finally:
            p4.disconnect()
            
        return refs