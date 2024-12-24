# Asset Version Framework (AVF)

AVF is a comprehensive asset versioning system designed for game development pipelines. It provides a flexible, extensible framework for tracking asset versions across multiple storage backends while maintaining rich metadata and version history.

## Key Features

### Storage Reference System
- Create versions from existing storage states without file copies
- Support for different reference types (files, commits, changelists)
- Track file moves and renames between versions
- Unified interface across storage backends

### Multi-Backend Storage Support
- Local disk storage with organized directory structure
- Git integration with branch-based version tracking
- Perforce support (coming soon)
- Extensible storage backend system for custom implementations

### Rich Metadata Management
- Track creator, tool versions, and timestamps
- Custom metadata support for asset-specific information
- Tagging system for version organization
- Full version history with searchable metadata

### SQLite Database Integration
- Efficient version tracking and querying
- Relationship mapping between versions and storage locations
- Tag-based searching and filtering
- Performance optimized for large asset collections

## Installation

Using UV (Recommended):
```bash
uv venv venv
source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate
uv pip install -e .
```

Using pip:
```bash
pip install avf
```

## Quick Start

### Basic Version Creation

```python
from pathlib import Path
from avf import AssetVersion, DiskStorage, GitStorage

# Initialize storage backends
storage_backends = {
    "disk": DiskStorage(Path("./asset_storage")),
    "git": GitStorage(Path("./asset_repo"))
}

# Create version manager
version_manager = AssetVersion(storage_backends)

# Create a new version
version_ids = version_manager.create_version(
    file_path=Path("character_model.fbx"),
    metadata={
        "creator": "john_doe",
        "tool_version": "maya_2024",
        "description": "Updated character model",
        "tags": ["character", "model", "HighPoly"],
        "custom_data": {
            "polygon_count": 15000
        }
    }
)
```

### Creating versions from existing version already in storage

```python
from avf import StorageReference, ReferenceType

# For existing files in disk storage
disk_reference = StorageReference(
    storage_type="disk",
    storage_id="existing_file_hash",
    path=Path("./asset_storage/existing_file.fbx"),
    reference_type=ReferenceType.FILE
)

disk_version_id = storage_backends["disk"].create_version_from_reference(
    reference=disk_reference,
    metadata={
        "creator": "john_doe",
        "tool_version": "maya_2024",
        "description": "Version from existing file"
    }
)

# For existing Git commits
git_reference = StorageReference(
    storage_type="git",
    storage_id="commit_hash",
    path=Path("assets/model.fbx"),
    reference_type=ReferenceType.COMMIT
)

git_version_id = storage_backends["git"].create_version_from_reference(
    reference=git_reference,
    metadata={
        "creator": "john_doe",
        "tool_version": "maya_2024",
        "description": "Version from existing commit"
    }
)
```

### Listing Storage References

```python
# List all file references in disk storage
disk_refs = storage_backends["disk"].list_references(
    reference_type=ReferenceType.FILE,
    path_pattern="*.fbx"
)

# List all commit references in Git storage
git_refs = storage_backends["git"].list_references(
    reference_type=ReferenceType.COMMIT,
    path_pattern="assets/"
)
```

### Database Integration

```python
from avf import DatabaseConnection, SQLiteVersionRepository

# Initialize database
db = DatabaseConnection("sqlite:///asset_versions.db")
db.create_tables()

# Initialize repository
repo = SQLiteVersionRepository(db)

# Create version manager with repository
version_manager = AssetVersion(
    storage_backends=storage_backends,
    version_repository=repo
)

# Find versions by tags
character_versions = repo.find_versions(tags=["character"])

# Get version history
version_history = repo.get_version_history(Path("character_model.fbx"))
```

## Storage Backend Configuration

### Disk Storage
```python
disk_storage = DiskStorage(
    storage_root=Path("./asset_storage")
)
```

Features:
- Organized directory structure
- Automatic file deduplication
- Metadata storage alongside assets
- Support for existing file references
- Hard linking optimization when possible

### Git Storage
```python
git_storage = GitStorage(
    repo_path=Path("./asset_repo"),
    branch_prefix="asset_versions"
)
```

Features:
- Branch-based version tracking
- Support for existing commit references
- Track file moves/renames through Git history
- Full commit metadata preservation
- Efficient storage through Git's object model

## Advanced Usage

### Custom Storage Backend

```python
from avf import StorageBackend, StorageReference
from pathlib import Path
from typing import Dict, Any, Optional, List

class CustomStorage(StorageBackend):
    def create_version_from_reference(
        self,
        reference: StorageReference,
        metadata: Dict[str, Any]
    ) -> str:
        # Implementation
        pass

    def list_references(
        self,
        reference_type: Optional[str] = None,
        path_pattern: Optional[str] = None
    ) -> List[StorageReference]:
        # Implementation
        pass

    # Implement other required methods
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/avf.git
cd avf
```

2. Run the development setup script:
```bash
# On Windows:
.\dev-setup.ps1

# On Unix:
./dev-setup.sh
```

3. Run tests:
```bash
uv run test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT

## Project Status

Current Version: 0.1.0 (Alpha)

Under active development. API may change.
