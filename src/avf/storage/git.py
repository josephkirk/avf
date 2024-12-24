from pathlib import Path
from typing import Dict, Any, Optional
import json
from git import Repo, GitCommandError
import os
from .base import StorageBackend

class GitStorage(StorageBackend):
    def __init__(self, repo_path: Path, branch_prefix: str = "asset_versions"):
        """Initialize Git storage
        
        Args:
            repo_path: Path to Git repository
            branch_prefix: Prefix for version branches
        """
        self.repo_path = Path(repo_path)
        self.branch_prefix = branch_prefix
        
        if not (self.repo_path / ".git").exists():
            self.repo = Repo.init(self.repo_path)
        else:
            self.repo = Repo(self.repo_path)
            
        # Ensure we have an initial commit
        if not self.repo.heads:
            self._create_initial_commit()
            
    def _create_initial_commit(self):
        """Create initial commit in repository"""
        readme_path = self.repo_path / "README.md"
        readme_path.write_text("# Asset Version Storage\nManaged by asset_version system")
        self.repo.index.add([readme_path])
        self.repo.index.commit("Initial commit")
        
    def _get_version_branch(self, version_id: str) -> str:
        """Get branch name for version"""
        return f"{self.branch_prefix}/{version_id}"
        
    def store_version(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Store a new version in Git
        
        Args:
            file_path: Path to file to store
            metadata: Version metadata
            
        Returns:
            Version identifier (commit hash)
        """
        # Create new branch for version
        version_id = self.repo.active_branch.commit.hexsha[:12]
        branch_name = self._get_version_branch(version_id)
        
        try:
            # Create and checkout new branch
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            
            # Copy file to repo
            target_path = self.repo_path / file_path.name
            target_path.write_bytes(file_path.read_bytes())
            
            # Store metadata
            metadata_path = self.repo_path / f"{file_path.name}.metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            # Commit changes
            self.repo.index.add([target_path, metadata_path])
            commit = self.repo.index.commit(f"Store version of {file_path.name}")
            
            # Return to original branch
            self.repo.heads.master.checkout()
            
            return version_id
            
        except GitCommandError as e:
            raise RuntimeError(f"Failed to store version in Git: {e}")
            
    def retrieve_version(self, version_id: str, target_path: Optional[Path] = None) -> Path:
        """Retrieve a specific version
        
        Args:
            version_id: Version identifier
            target_path: Optional path to store retrieved file
            
        Returns:
            Path to retrieved file
        """
        branch_name = self._get_version_branch(version_id)
        original_branch = self.repo.active_branch
        
        try:
            # Checkout version branch
            self.repo.git.checkout(branch_name)
            
            # Find the asset file (should be only non-metadata file)
            asset_files = [f for f in os.listdir(self.repo_path) 
                         if not f.endswith('.metadata.json') and f != 'README.md']
            
            if not asset_files:
                raise FileNotFoundError(f"No asset file found in version {version_id}")
                
            source_path = self.repo_path / asset_files[0]
            
            # Copy to target if specified
            if target_path is not None:
                target_path = Path(target_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(source_path.read_bytes())
                result_path = target_path
            else:
                result_path = source_path
            
            return result_path
            
        except GitCommandError as e:
            raise RuntimeError(f"Failed to retrieve version from Git: {e}")
        finally:
            # Always return to original branch
            original_branch.checkout()
            
    def get_version_info(self, version_id: str) -> Dict[str, Any]:
        """Get metadata for a specific version
        
        Args:
            version_id: Version identifier
            
        Returns:
            Version metadata
        """
        branch_name = self._get_version_branch(version_id)
        original_branch = self.repo.active_branch
        
        try:
            # Checkout version branch
            self.repo.git.checkout(branch_name)
            
            # Find metadata file
            metadata_files = [f for f in os.listdir(self.repo_path) 
                            if f.endswith('.metadata.json')]
            
            if not metadata_files:
                raise FileNotFoundError(f"No metadata found for version {version_id}")
                
            metadata_path = self.repo_path / metadata_files[0]
            return json.loads(metadata_path.read_text())
            
        except GitCommandError as e:
            raise RuntimeError(f"Failed to retrieve metadata from Git: {e}")
        finally:
            # Always return to original branch
            original_branch.checkout()
