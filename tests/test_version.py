from pathlib import Path
import pytest
from avf import AssetVersion, DiskStorage

def test_disk_storage_initialization():
    storage_path = Path("./test_storage")
    storage = DiskStorage(storage_path)
    
    assert storage.storage_root == storage_path
    assert (storage_path / "_metadata").exists()
    
    # Cleanup
    import shutil
    if storage_path.exists():
        shutil.rmtree(storage_path)

def test_version_creation():
    # Setup
    storage_path = Path("./test_storage")
    storage_backends = {
        "disk": DiskStorage(storage_path)
    }
    
    version_manager = AssetVersion(storage_backends)
    
    # Create a test file
    test_file = Path("./test_file.txt")
    test_file.write_text("Test content")
    
    # Create version
    metadata = {
        "creator": "test_user",
        "tool_version": "test_1.0",
        "description": "Test version",
        "tags": ["test"],
        "custom_data": {"test_key": "test_value"}
    }
    
    try:
        version_ids = version_manager.create_version(test_file, metadata)
        
        # Verify version creation
        assert "disk" in version_ids
        assert version_ids["disk"].metadata == metadata
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        if storage_path.exists():
            import shutil
            shutil.rmtree(storage_path)
