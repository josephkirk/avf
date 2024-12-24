"""Tests for asset history dumper."""
from pathlib import Path

from avf.utils.history import AssetHistoryDumper


def test_history_dumper_initialization(disk_storage):
    """Test history dumper initialization."""
    dumper = AssetHistoryDumper({"disk": disk_storage})
    assert dumper.storage_backends == {"disk": disk_storage}

def test_collect_storage_references(disk_storage, test_file, test_metadata):
    """Test collecting references from storage."""
    dumper = AssetHistoryDumper({"disk": disk_storage})

    # Create some versions
    disk_storage.store_version(test_file, test_metadata)
    disk_storage.store_version(test_file, {
        **test_metadata,
        "description": "Updated version"
    })

    refs = dumper._collect_storage_references(test_file)
    assert "disk" in refs
    assert len(refs["disk"]) > 0

    # Test with non-existent path
    refs = dumper._collect_storage_references(Path("non_existent.txt"))
    assert "disk" in refs
    assert len(refs["disk"]) == 0

def test_build_storage_summary(disk_storage, test_file, test_metadata):
    """Test building storage summary."""
    dumper = AssetHistoryDumper({"disk": disk_storage})

    # Create versions
    disk_storage.store_version(test_file, test_metadata)

    # Get references
    refs = dumper._collect_storage_references(test_file)

    # Build summary
    summary = dumper._build_storage_summary(refs)
    assert "disk" in summary
    assert summary["disk"]["versions"] > 0
    assert "references" in summary["disk"]

def test_extract_timeline(disk_storage, test_file, test_metadata):
    """Test timeline extraction."""
    dumper = AssetHistoryDumper({"disk": disk_storage})

    # Create versions at different times
    disk_storage.store_version(test_file, test_metadata)
    disk_storage.store_version(test_file, {
        **test_metadata,
        "description": "Updated version"
    })

    # Get references
    refs = dumper._collect_storage_references(test_file)

    # Extract timeline
    timeline = dumper._extract_timeline(refs)
    assert len(timeline) > 0
    for event in timeline:
        assert "timestamp" in event
        assert "storage_type" in event
        assert "reference_id" in event
        assert "metadata" in event

def test_dump_history(disk_storage, test_file, test_metadata):
    """Test full history dump."""
    dumper = AssetHistoryDumper({"disk": disk_storage})

    # Create versions
    disk_storage.store_version(test_file, test_metadata)
    disk_storage.store_version(test_file, {
        **test_metadata,
        "description": "Updated version"
    })

    # Dump history
    history = dumper.dump_history(
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
        first_event = history["timeline"][0]
        assert "timestamp" in first_event
        assert "storage_type" in first_event

    if "storage_versions" in history:
        assert len(history["storage_versions"]) > 0
        first_version = history["storage_versions"][0]
        assert "storage_type" in first_version
        assert "metadata" in first_version

def test_multiple_storage_history(disk_storage, git_storage, test_file, test_metadata):
    """Test history dump with multiple storage backends."""
    dumper = AssetHistoryDumper({
        "disk": disk_storage,
        "git": git_storage
    })

    # Create versions in both storages
    disk_storage.store_version(test_file, test_metadata)
    git_storage.store_version(test_file, test_metadata)

    # Dump history
    history = dumper.dump_history(test_file)

    assert "disk" in history["metadata"]["storage_summary"]
    assert "git" in history["metadata"]["storage_summary"]

def test_error_handling_in_history(disk_storage, test_file):
    """Test error handling during history collection."""
    dumper = AssetHistoryDumper({"disk": disk_storage})

    # Test with non-existent file
    history = dumper.dump_history(Path("non_existent.txt"))
    assert history["asset_path"] == "non_existent.txt"
    assert "metadata" in history
    assert "storage_summary" in history["metadata"]

    # Storage should exist but have no versions
    assert "disk" in history["metadata"]["storage_summary"]
    assert history["metadata"]["storage_summary"]["disk"]["versions"] == 0
