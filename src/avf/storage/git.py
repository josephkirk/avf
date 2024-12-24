"""Git-based storage backend implementation."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import GitCommandError, Repo

from .base import StorageBackend
from .reference import ReferenceType, StorageReference


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
            self.repo.index.commit(f"Store version of {file_path.name}")

            # Return to original branch
            self.repo.heads.master.checkout()

            return version_id

        except GitCommandError as e:
            raise RuntimeError(f"Failed to store version in Git: {e}") from e

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
            raise RuntimeError(f"Failed to retrieve version from Git: {e}") from e
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
            metadata = json.loads(metadata_path.read_text())

            # Add Git-specific information
            commit = self.repo.head.commit
            metadata.update({
                "commit_hash": commit.hexsha,
                "commit_date": commit.committed_datetime.isoformat(),
                "commit_message": commit.message,
                "branch": branch_name
            })

            return metadata

        except GitCommandError as e:
            raise RuntimeError(f"Failed to retrieve metadata from Git: {e}") from e
        finally:
            # Always return to original branch
            original_branch.checkout()

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
            GitCommandError: If Git operation fails
        """
        if reference.reference_type != ReferenceType.COMMIT:
            raise ValueError(f"Unsupported reference type: {reference.reference_type}")

        try:
            # Get the commit
            commit = self.repo.commit(reference.storage_id)
            version_id = commit.hexsha[:12]
            branch_name = self._get_version_branch(version_id)

            # Create new branch at the specified commit
            new_branch = self.repo.create_head(branch_name, commit)

            # Store additional metadata
            metadata.update({
                "commit_hash": commit.hexsha,
                "commit_date": commit.committed_datetime.isoformat(),
                "commit_message": commit.message,
                "reference": reference.model_dump(),
                "original_path": str(reference.path)
            })

            # Checkout branch and add metadata
            original_branch = self.repo.active_branch
            new_branch.checkout()

            try:
                # Write metadata file
                metadata_path = self.repo_path / f"{reference.path.name}.metadata.json"
                metadata_path.write_text(json.dumps(metadata, indent=2))

                # Commit metadata
                self.repo.index.add([metadata_path])
                self.repo.index.commit(f"Add metadata for {reference.path.name}")

            finally:
                # Return to original branch
                original_branch.checkout()

            return version_id

        except (GitCommandError, KeyError) as e:
            raise RuntimeError(f"Failed to create version from Git reference: {e}") from e

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
        if reference_type and reference_type != ReferenceType.COMMIT:
            return refs

        try:
            # Get all commits
            for commit in self.repo.iter_commits():
                # Get changed files in this commit
                changed_files = []
                for item in commit.stats.files:
                    file_path = Path(item)
                    if path_pattern and path_pattern not in str(file_path):
                        continue
                    if not file_path.name.endswith('.metadata.json'):
                        changed_files.append(file_path)

                # Create reference for each changed file
                for file_path in changed_files:
                    refs.append(StorageReference(
                        storage_type="git",
                        storage_id=commit.hexsha,
                        path=file_path,
                        reference_type=ReferenceType.COMMIT,
                        metadata={
                            "commit_date": commit.committed_datetime.isoformat(),
                            "commit_message": commit.message,
                            "author": commit.author.name,
                            "author_email": commit.author.email
                        }
                    ))

        except GitCommandError as e:
            raise RuntimeError(f"Failed to list Git references: {e}") from e

        return refs
