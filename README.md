# Asset Version Framework (AVF)

A comprehensive asset versioning system for game development pipelines.

## Features

- Multi-backend storage support (Disk, Git, Perforce)
- Metadata tracking
- SQLite database integration
- Extensible storage backend system
- Version history tracking

## Installation

```bash
uv venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
uv pip install -e .
```

## Usage

```python
from asset_version import AssetVersion, DiskStorage, GitStorage, SQLiteVersionRepository, DatabaseConnection
from pathlib import Path

# Initialize database
db = DatabaseConnection("sqlite:///asset_versions.db")
db.create_tables()

# Initialize repository
repo = SQLiteVersionRepository(db)

# Initialize storage backends
storage_backends = {
    "disk": DiskStorage(Path("./asset_storage")),
    "git": GitStorage(Path("./asset_repo"))
}

# Create version manager
version_manager = AssetVersion(
    storage_backends=storage_backends,
    version_repository=repo
)

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
```

## License

MIT