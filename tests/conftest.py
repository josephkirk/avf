"""Test fixtures for AVF."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from avf import (
    DiskStorage, 
    GitStorage, 
    DatabaseConnection,
    SQLiteVersionRepository,
    StorageReference,
    ReferenceType,
    AssetMetadata
)

@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture(scope="function")
def test_file(temp_dir):
    """Create a test file."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content")
    yield file_path

@pytest.fixture(scope="function")
def test_metadata():
    """Create test metadata."""
    return {
        "creator": "test_user",
        "tool_version": "test_1.0",
        "description": "Test description",
        "tags": ["test", "unit"],
        "custom_data": {
            "key": "value"
        }
    }

@pytest.fixture(scope="function")
def valid_metadata(test_metadata):
    """Create valid AssetMetadata instance."""
    return AssetMetadata(**test_metadata)

@pytest.fixture(scope="function")
def disk_storage(temp_dir):
    """Create disk storage backend."""
    storage_path = temp_dir / "disk_storage"
    storage = DiskStorage(storage_path)
    return storage

@pytest.fixture(scope="function")
def git_storage(temp_dir):
    """Create git storage backend."""
    repo_path = temp_dir / "git_storage"
    storage = GitStorage(repo_path)
    yield storage

@pytest.fixture(scope="function")
def db_connection(temp_dir):
    """Create test database connection."""
    db_path = temp_dir / "test.db"
    connection = DatabaseConnection(f"sqlite:///{db_path}")
    connection.create_tables()
    yield connection
    try:
        if db_path.exists():
            db_path.unlink()
    except Exception:
        pass

@pytest.fixture(scope="function")
def version_repo(db_connection):
    """Create test version repository."""
    return SQLiteVersionRepository(db_connection)

@pytest.fixture(scope="function")
def storage_reference(test_file):
    """Create test storage reference."""
    return StorageReference(
        storage_type="disk",
        storage_id="test_id",
        path=test_file,
        reference_type=ReferenceType.FILE,
        metadata={}
    )

@pytest.fixture(scope="function")
def cleanup_temp_files():
    """Cleanup any temporary files after tests."""
    yield
    
    # Cleanup patterns that might not be caught by temp_dir
    patterns = ["test_*.txt", "*.db", "*.sqlite"]
    for pattern in patterns:
        for file in Path(".").glob(pattern):
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
            except Exception:
                pass