import shutil
from datetime import datetime
from pathlib import Path

import pytz

from avf import AssetVersion, DiskStorage

# Define the timezone
timezone = pytz.timezone("Asia/Ho_Chi_Minh")


def test_disk_storage_initialization():
    storage_path = Path("./test_storage")
    storage = DiskStorage(storage_path)

    assert storage.storage_root == storage_path
    assert (storage_path / "_metadata").exists()

    # Cleanup
    if storage_path.exists():
        shutil.rmtree(storage_path)


def test_version_creation():
    # Setup
    storage_path = Path("./test_storage")
    storage_backends = {"disk": DiskStorage(storage_path)}

    version_manager = AssetVersion(storage_backends)

    # Create a test file
    test_file = Path("./test_file.txt")
    test_file.write_text("Test content")

    # Create metadata
    metadata = {
        "creator": "test_user",
        "tool_version": "test_1.0",
        "description": "Test version",
        "tags": ["test"],
        "custom_data": {"test_key": "test_value"},
        "creation_time": datetime.now(tz=timezone),
    }

    try:
        version_ids = version_manager.create_version(test_file, metadata)

        # Verify version creation
        assert "disk" in version_ids
        disk_version = version_ids["disk"]
        assert disk_version.metadata.creator == metadata["creator"]
        assert disk_version.metadata.tool_version == metadata["tool_version"]
        assert disk_version.metadata.description == metadata["description"]
        assert disk_version.metadata.tags == metadata["tags"]
        assert disk_version.metadata.custom_data == metadata["custom_data"]

        # Test version retrieval
        retrieved_info = version_manager.get_version_info("disk", disk_version.storage_id)
        assert retrieved_info.creator == metadata["creator"]
        assert retrieved_info.tool_version == metadata["tool_version"]

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        if storage_path.exists():
            shutil.rmtree(storage_path)


def test_version_retrieval():
    # Setup similar to test_version_creation
    storage_path = Path("./test_storage")
    storage_backends = {"disk": DiskStorage(storage_path)}
    version_manager = AssetVersion(storage_backends)
    test_file = Path("./test_file.txt")
    test_content = "Test content for retrieval"
    test_file.write_text(test_content)

    metadata = {
        "creator": "test_user",
        "tool_version": "test_1.0",
        "description": "Test version",
        "tags": ["test"],
        "custom_data": {},
        "creation_time": datetime.now(tz=timezone),
    }

    try:
        # Create version
        version_ids = version_manager.create_version(test_file, metadata)
        disk_version = version_ids["disk"]

        # Test retrieval to new location
        retrieval_path = Path("./retrieved_file.txt")
        retrieved_path = version_manager.get_version(
            "disk", disk_version.storage_id, retrieval_path
        )

        # Verify content
        assert retrieved_path.exists()
        assert retrieved_path.read_text() == test_content

    finally:
        # Cleanup
        for path in [test_file, retrieval_path]:
            if path.exists():
                path.unlink()
        if storage_path.exists():
            shutil.rmtree(storage_path)
