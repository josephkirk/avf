# Asset Version Framework (AVF)

AVF is a comprehensive asset versioning system designed for game development pipelines. It provides a flexible, extensible framework for tracking asset versions across multiple storage backends while maintaining rich metadata and version history.

## Key Features

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

### Type-Safe Implementation
- Full type hinting support
- Pydantic models for data validation
- SQLAlchemy ORM with type checking

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

### Basic Usage

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

# Create a version
version_ids = version_manager.create_version(
    file_path=Path("character_model.fbx"),
    metadata={
        "creator": "john_doe",
        "tool_version": "maya_2024",
        "description": "Updated character model",
        "tags": ["character", "model"],
        "custom_data": {
            "polygon_count": 15000,
            "texture_resolution": "4k"
        }
    }
)

# Retrieve a version
retrieved_path = version_manager.get_version(
    "disk",
    version_ids["disk"].storage_id,
    Path("./retrieved_model.fbx")
)
```

### With Database Integration

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
from avf import DiskStorage

disk_storage = DiskStorage(
    storage_root=Path("./asset_storage")
)
```

Features:
- Organized directory structure
- Automatic file deduplication
- Metadata storage alongside assets
- Efficient retrieval system

### Git Storage
```python
from avf import GitStorage

git_storage = GitStorage(
    repo_path=Path("./asset_repo"),
    branch_prefix="asset_versions"
)
```

Features:
- Branch-based version tracking
- Full Git history integration
- Metadata stored in JSON
- Branch naming conventions

## Metadata System

AVF provides a flexible metadata system:

```python
metadata = {
    "creator": "john_doe",         # Required
    "tool_version": "maya_2024",   # Required
    "description": "Updated model", # Optional
    "tags": ["character", "model"], # Optional
    "custom_data": {               # Optional
        "polygon_count": 15000,
        "texture_resolution": "4k",
        "material_count": 5
    }
}
```

## Advanced Usage

### Custom Storage Backend

```python
from avf import StorageBackend
from pathlib import Path
from typing import Dict, Any, Optional

class CustomStorage(StorageBackend):
    def store_version(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        # Implementation
        pass

    def retrieve_version(self, version_id: str, target_path: Optional[Path] = None) -> Path:
        # Implementation
        pass

    def get_version_info(self, version_id: str) -> Dict[str, Any]:
        # Implementation
        pass
```

### Version Querying

```python
from datetime import datetime, timedelta

# Find versions by creator
versions = repo.find_versions(creator="john_doe")

# Find versions by date range
week_ago = datetime.now() - timedelta(days=7)
recent_versions = repo.find_versions(after=week_ago)

# Complex queries
character_versions = repo.find_versions(
    tags=["character"],
    creator="john_doe",
    after=week_ago
)
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