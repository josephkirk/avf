"""Tests for main AssetVersion class."""
from pathlib import Path

import pytest

from avf import AssetVersion


def test_asset_version_initialization(disk_storage):
    """Test AssetVersion initialization."""
    version_manager = AssetVersion({"disk": disk_storage})
    assert "disk" in version_manager.storage_backends

def test_create_version(disk_storage, test_file, test_metadata):
    """Test creating a version across storage backends."""
    version_manager = AssetVersion({"disk": disk_storage})

    version_ids = version_manager.create_version(
        file_path=test_file,
        metadata=test_metadata
    )

    assert "disk" in version_ids
    version_id = version_ids["disk"]

    # Verify version creation
    version_info = disk_storage.get_version_info(version_id.storage_id)
    assert version_info["creator"] == test_metadata["creator"]
    assert version_info["tool_version"] == test_metadata["tool_version"]

def test_create_version_with_repository(disk_storage, version_repo, test_file, test_metadata):
    """Test creating a version with repository tracking."""
    version_manager = AssetVersion(
        storage_backends={"disk": disk_storage},
        version_repository=version_repo
    )

    version_ids = version_manager.create_version(
        file_path=test_file,
        metadata=test_metadata
    )

    assert "disk" in version_ids
    version_id = version_ids["disk"]

    # Verify storage version
    version_info = disk_storage.get_version_info(version_id.storage_id)
    assert version_info["creator"] == test_metadata["creator"]

    # Verify repository tracking
    versions = version_repo.find_versions(file_path=test_file)
    assert len(versions) == 1
    assert versions[0]["creator"] == test_metadata["creator"]

def test_multiple_storage_backends(disk_storage, git_storage, test_file, test_metadata):
    """Test creating versions across multiple storage backends."""
    version_manager = AssetVersion({
        "disk": disk_storage,
        "git": git_storage
    })

    version_ids = version_manager.create_version(
        file_path=test_file,
        metadata=test_metadata
    )

    assert "disk" in version_ids
    assert "git" in version_ids

    # Verify versions in both storages
    for storage_type, version_id in version_ids.items():
        backend = version_manager.storage_backends[storage_type]
        version_info = backend.get_version_info(version_id.storage_id)
        assert version_info["creator"] == test_metadata["creator"]

def test_get_version(disk_storage, test_file, test_metadata):
    """Test retrieving a version."""
    version_manager = AssetVersion({"disk": disk_storage})
    version_ids = version_manager.create_version(test_file, test_metadata)

    version_id = version_ids["disk"]
    target_path = Path(test_file.parent / "retrieved.txt")

    # Test retrieval
    retrieved_path = version_manager.get_version(
        "disk",
        version_id.storage_id,
        target_path
    )

    assert retrieved_path.exists()
    assert retrieved_path.read_text() == test_file.read_text()

def test_get_version_info(disk_storage, test_file, test_metadata):
    """Test getting version metadata."""
    version_manager = AssetVersion({"disk": disk_storage})
    version_ids = version_manager.create_version(test_file, test_metadata)

    version_id = version_ids["disk"]
    info = version_manager.get_version_info("disk", version_id.storage_id)

    assert info.creator == test_metadata["creator"]
    assert info.tool_version == test_metadata["tool_version"]
    assert info.description == test_metadata["description"]

def test_find_versions(disk_storage, version_repo, test_file, test_metadata):
    """Test finding versions through repository."""
    version_manager = AssetVersion(
        storage_backends={"disk": disk_storage},
        version_repository=version_repo
    )

    # Create multiple versions
    version_manager.create_version(test_file, test_metadata)
    version_manager.create_version(test_file, {
        **test_metadata,
        "description": "Updated version"
    })

    # Find versions
    versions = version_manager.find_versions(file_path=test_file)
    assert len(versions) == 2

    # Find by tags
    versions = version_manager.find_versions(tags=test_metadata["tags"])
    assert len(versions) > 0

def test_dump_asset_history(disk_storage, test_file, test_metadata):
    """Test dumping complete asset history."""
    version_manager = AssetVersion({"disk": disk_storage})

    # Create multiple versions
    version_manager.create_version(test_file, test_metadata)
    version_manager.create_version(test_file, {
        **test_metadata,
        "description": "Updated version"
    })

    # Dump history
    history = version_manager.dump_asset_history(
        test_file,
        include_storage_data=True,
        include_timeline=True
    )

    assert history["asset_path"] == str(test_file)
    assert "metadata" in history
    assert "storage_summary" in history["metadata"]
    assert "disk" in history["metadata"]["storage_summary"]

    if "timeline" in history:
        assert len(history["timeline"]) > 0

    if "storage_versions" in history:
        assert len(history["storage_versions"]) > 0

def test_error_handling(disk_storage, test_file, test_metadata):
    """Test error handling in version manager."""
    version_manager = AssetVersion({"disk": disk_storage})

    # Test invalid storage type
    with pytest.raises(KeyError):
        version_manager.get_version("invalid", "some_id")

    with pytest.raises(KeyError):
        version_manager.get_version_info("invalid", "some_id")

    # Test without repository
    with pytest.raises(RuntimeError):
        version_manager.find_versions(tags=["test"])

def test_version_identifier_validation(disk_storage, test_file, test_metadata):
    """Test version identifier model validation."""
    version_manager = AssetVersion({"disk": disk_storage})
    version_ids = version_manager.create_version(test_file, test_metadata)

    version_id = version_ids["disk"]
    assert version_id.storage_type == "disk"
    assert version_id.storage_id
    assert version_id.file_path == test_file
    assert version_id.timestamp
    assert version_id.metadata.creator == test_metadata["creator"]
