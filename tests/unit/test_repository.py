"""Tests for version repository."""
from datetime import datetime, timedelta
from pathlib import Path


def test_create_version(version_repo, test_metadata):
    """Test creating a version in repository."""
    version_id = version_repo.create_version(
        file_path=Path("test.fbx"),
        creator=test_metadata["creator"],
        tool_version=test_metadata["tool_version"],
        description=test_metadata["description"],
        tags=test_metadata["tags"],
        custom_data=test_metadata["custom_data"]
    )

    assert version_id > 0

    info = version_repo.get_version_info(version_id)
    assert info["creator"] == test_metadata["creator"]
    assert info["tool_version"] == test_metadata["tool_version"]
    assert info["tags"] == test_metadata["tags"]

def test_add_storage_location(version_repo, test_metadata):
    """Test adding storage locations."""
    version_id = version_repo.create_version(
        file_path=Path("test.fbx"),
        creator=test_metadata["creator"],
        tool_version=test_metadata["tool_version"],
        description=test_metadata["description"],
        tags=test_metadata["tags"],
        custom_data=test_metadata["custom_data"]
    )

    # Add storage location
    version_repo.add_storage_location(
        version_id=version_id,
        storage_type="disk",
        storage_id="test_storage_id"
    )

    locations = version_repo.get_storage_locations(version_id)
    assert len(locations) == 1
    assert locations[0]["storage_type"] == "disk"
    assert locations[0]["storage_id"] == "test_storage_id"

def test_find_versions(version_repo, test_metadata):
    """Test finding versions with different criteria."""
    # Create some test versions
    version_repo.create_version(
        file_path=Path("test1.fbx"),
        creator="user1",
        tool_version="1.0",
        description="Test 1",
        tags=["model", "character"],
        custom_data={}
    )

    version_repo.create_version(
        file_path=Path("test2.fbx"),
        creator="user2",
        tool_version="1.0",
        description="Test 2",
        tags=["model", "prop"],
        custom_data={}
    )

    # Test find by creator
    versions = version_repo.find_versions(creator="user1")
    assert len(versions) == 1
    assert versions[0]["creator"] == "user1"

    # Test find by tags
    versions = version_repo.find_versions(tags=["model"])
    assert len(versions) == 2

    versions = version_repo.find_versions(tags=["character"])
    assert len(versions) == 1

    # Test find by date range
    now = datetime.now(tz=version_repo.timezone)
    versions = version_repo.find_versions(
        after=now - timedelta(minutes=5),
        before=now + timedelta(minutes=5)
    )
    assert len(versions) == 2

def test_version_history(version_repo, test_metadata):
    """Test getting version history for a file."""
    file_path = Path("test.fbx")

    # Create multiple versions
    version_repo.create_version(
        file_path=file_path,
        creator="user1",
        tool_version="1.0",
        description="Version 1",
        tags=[],
        custom_data={}
    )

    version_repo.create_version(
        file_path=file_path,
        creator="user1",
        tool_version="1.0",
        description="Version 2",
        tags=[],
        custom_data={}
    )

    versions = version_repo.find_versions(file_path=file_path)
    assert len(versions) == 2
    assert versions[0]["description"] == "Version 1"
    assert versions[1]["description"] == "Version 2"

def test_error_handling(version_repo):
    """Test repository error handling."""
    # Test non-existent version
    version_repo.get_version_info(999)

    version_repo.get_storage_locations(999)

    # Test invalid storage location
    version_repo.add_storage_location(
        version_id=999,
        storage_type="disk",
        storage_id="test"
    )
