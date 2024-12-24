"""Tests for disk storage backend."""

import json
from pathlib import Path

import pytest


def test_disk_storage_initialization(disk_storage):
    """Test disk storage initialization."""
    assert disk_storage.storage_root.exists()
    assert (disk_storage.storage_root / "_metadata").exists()


def test_store_version(disk_storage, test_file, test_metadata):
    """Test storing a version."""
    version_id = disk_storage.store_version(test_file, test_metadata)

    assert version_id
    version_path = disk_storage._get_version_path(version_id)
    metadata_path = disk_storage._get_metadata_path(version_id)

    assert version_path.exists()
    assert metadata_path.exists()
    assert version_path.read_text() == "Test content"

    stored_metadata = json.loads(metadata_path.read_text())
    assert stored_metadata["creator"] == test_metadata["creator"]
    assert stored_metadata["tool_version"] == test_metadata["tool_version"]


def test_retrieve_version(disk_storage, test_file, test_metadata):
    """Test retrieving a stored version."""
    version_id = disk_storage.store_version(test_file, test_metadata)

    # Test retrieval without target path
    retrieved_path = disk_storage.retrieve_version(version_id)
    assert retrieved_path.exists()
    assert retrieved_path.read_text() == "Test content"

    # Test retrieval with target path
    target_path = Path(test_file.parent / "retrieved_file.txt")
    retrieved_path = disk_storage.retrieve_version(version_id, target_path)
    assert retrieved_path.exists()
    assert retrieved_path.read_text() == "Test content"
    assert retrieved_path == target_path


def test_get_version_info(disk_storage, test_file, test_metadata):
    """Test getting version metadata."""
    version_id = disk_storage.store_version(test_file, test_metadata)
    info = disk_storage.get_version_info(version_id)

    assert info["creator"] == test_metadata["creator"]
    assert info["tool_version"] == test_metadata["tool_version"]
    assert "original_path" in info
    assert "timestamp" in info


def test_create_version_from_reference(disk_storage, storage_reference, test_metadata):
    """Test creating version from reference."""
    version_id = disk_storage.create_version_from_reference(storage_reference, test_metadata)

    assert version_id
    info = disk_storage.get_version_info(version_id)
    assert info["creator"] == test_metadata["creator"]
    assert info["tool_version"] == test_metadata["tool_version"]


def test_list_references(disk_storage, test_file, test_metadata):
    """Test listing storage references."""
    disk_storage.store_version(test_file, test_metadata)
    refs = disk_storage.list_references(path_pattern=test_file.name)

    assert len(refs) > 0
    ref = refs[0]
    assert ref.storage_type == "disk"
    assert ref.path.exists()
    assert ref.metadata


def test_error_handling(disk_storage):
    """Test error handling."""
    # Test non-existent version
    with pytest.raises(FileNotFoundError):
        disk_storage.retrieve_version("non_existent_id")

    with pytest.raises(FileNotFoundError):
        disk_storage.get_version_info("non_existent_id")


def test_version_id_uniqueness(disk_storage, test_file, test_metadata):
    """Test that version IDs are unique."""
    id1 = disk_storage.store_version(test_file, test_metadata)
    id2 = disk_storage.store_version(test_file, test_metadata)

    assert id1 != id2
