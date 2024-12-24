# Asset Version Framework (AVF)

A Python framework for game asset version control that works with your existing tools. AVF makes it easy to track asset versions across different storage systems (local disk, Git, Perforce) while maintaining rich metadata and version history.

## Why Use AVF?

- **Works with Your Tools**: Keep using Git, Perforce, or local storage - AVF works with all of them
- **Rich History Tracking**: See when, why, and how assets changed across all your storage systems
- **Flexible Metadata**: Track any asset-specific information you need (polygon counts, texture sizes, etc.)
- **Simple but Powerful**: Easy to start using, but scales with your needs

## Quick Install

```bash
pip install avf
```

For development:
```bash
# Clone the repository
git clone https://github.com/your-username/avf.git
cd avf

# Install with development dependencies
uv venv .venv
.\.venv\Scripts\activate  # On Windows
source .venv/bin/activate # On Unix
uv pip install -e ".[dev]"
```

## Basic Usage

```python
from pathlib import Path
from avf import AssetVersion, DiskStorage

# Set up a simple disk storage
storage = {
    "disk": DiskStorage(Path("./asset_storage"))
}

# Create version manager
versions = AssetVersion(storage)

# Create a new version
version_ids = versions.create_version(
    file_path=Path("character.fbx"),
    metadata={
        "creator": "john_doe",
        "tool_version": "maya_2024",
        "description": "Updated character model",
        "tags": ["character", "model"],
        "custom_data": {
            "polygon_count": 15000
        }
    }
)
```

## Looking Up Version History

```python
# Get complete history of an asset
history = versions.dump_asset_history(
    Path("character.fbx")
)

# Print basic info
print(f"First version: {history['metadata']['first_version']}")
print(f"Latest version: {history['metadata']['latest_version']}")

# See timeline of changes
for event in history['timeline']:
    print(f"{event['timestamp']}: {event['action']}")
```

## Storage Options

### Local Disk
```python
from avf import DiskStorage

disk = DiskStorage(
    storage_root=Path("./assets")
)
```

### Git
```python
from avf import GitStorage

git = GitStorage(
    repo_path=Path("./git_repo"),
    branch_prefix="assets"  # Optional
)
```

### Perforce
```python
from avf import PerforceStorage

p4 = PerforceStorage(
    port="perforce:1666",
    user="username",
    client="workspace_name",
    workspace_root=Path("./p4_ws")
)
```

## Adding Database Support

```python
from avf import DatabaseConnection, SQLiteVersionRepository

# Set up database
db = DatabaseConnection("sqlite:///versions.db")
db.create_tables()

# Create repository
repo = SQLiteVersionRepository(db)

# Use with version manager
versions = AssetVersion(
    storage_backends=storage,
    version_repository=repo
)

# Now you can search versions
models = repo.find_versions(tags=["model"])
```

## Using Existing Files

If you already have files in your storage systems, you can create versions from them:

```python
from avf import StorageReference, ReferenceType

# Create version from existing file
ref = StorageReference(
    storage_type="disk",
    storage_id="file_hash",
    path=Path("./assets/existing.fbx"),
    reference_type=ReferenceType.FILE
)

version_id = storage["disk"].create_version_from_reference(
    reference=ref,
    metadata={
        "creator": "john_doe",
        "tool_version": "maya_2024",
        "description": "Existing model"
    }
)
```

## Development

Running tests:
```bash
pytest tests/
```

Code formatting:
```bash
black src/ tests/
ruff check src/ tests/
```

## License

MIT

## Project Status

Current Version: 0.1.0 (Alpha)

The API is still evolving. If you're using it in production, pin your dependencies to specific versions.

## Need Help?

- Submit issues: https://github.com/your-username/avf/issues
- Read docs: https://github.com/your-username/avf/blob/main/README.md
