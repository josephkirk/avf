"""
Asset history analysis example showing how to track and analyze version history.

This example demonstrates:
- Collecting version history across storage types
- Analyzing version metadata
- Tracking asset changes
- Generating history reports
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

from avf import AssetVersion, DatabaseConnection, DiskStorage, GitStorage, SQLiteVersionRepository


def print_history_summary(history):
    """Helper to print history summary."""
    print("\nHistory Summary:")
    print(f"Asset: {history['asset_path']}")

    if 'metadata' in history:
        meta = history['metadata']
        print("\nMetadata:")
        if 'first_version' in meta:
            print(f"First Version: {meta['first_version']}")
        if 'latest_version' in meta:
            print(f"Latest Version: {meta['latest_version']}")
        if 'total_references' in meta:
            print(f"Total References: {meta['total_references']}")

        if 'storage_summary' in meta:
            print("\nStorage Summary:")
            for storage_type, summary in meta['storage_summary'].items():
                print(f"\n{storage_type}:")
                for key, value in summary.items():
                    print(f"- {key}: {value}")

def print_timeline(history):
    """Helper to print version timeline."""
    if 'timeline' not in history:
        return

    print("\nVersion Timeline:")
    for event in history['timeline']:
        timestamp = event.get('timestamp', 'Unknown')
        action = event.get('action', 'Unknown')
        storage = event.get('storage_type', 'Unknown')
        print(f"{timestamp}: {action} in {storage}")
        if 'metadata' in event:
            print("  Metadata:")
            for key, value in event['metadata'].items():
                print(f"  - {key}: {value}")

def analyze_version_patterns(history):
    """Analyze version creation patterns."""
    if 'timeline' not in history:
        return

    print("\nVersion Pattern Analysis:")

    # Analyze version frequency
    events = history['timeline']
    if len(events) > 1:
        intervals = []
        for i in range(1, len(events)):
            try:
                t1 = datetime.fromisoformat(events[i-1]['timestamp'])
                t2 = datetime.fromisoformat(events[i]['timestamp'])
                intervals.append((t2 - t1).total_seconds())
            except (ValueError, KeyError):
                continue

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            print(f"Average time between versions: {timedelta(seconds=avg_interval)}")

    # Analyze storage usage
    storage_counts = {}
    for event in events:
        storage = event.get('storage_type')
        if storage:
            storage_counts[storage] = storage_counts.get(storage, 0) + 1

    print("\nStorage Usage:")
    for storage, count in storage_counts.items():
        print(f"- {storage}: {count} versions")

def main():
    # Set up storage backends
    storage = {
        "disk": DiskStorage(Path("./disk_storage")),
        "git": GitStorage(Path("./git_storage"))
    }

    # Set up database
    db = DatabaseConnection("sqlite:///versions.db")
    db.create_tables()
    repo = SQLiteVersionRepository(db)

    # Create version manager
    version_manager = AssetVersion(
        storage_backends=storage,
        version_repository=repo
    )

    # Create test asset with multiple versions
    test_file = Path("test_asset.ma")

    print("Creating test versions...")

    # Version 1
    test_file.write_text("Initial content")
    version_manager.create_version(
        test_file,
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Initial version",
            "tags": ["model", "character"],
            "custom_data": {
                "polygon_count": 15000
            }
        }
    )

    # Version 2 (after a day)
    test_file.write_text("Updated content")
    version_manager.create_version(
        test_file,
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Optimized model",
            "tags": ["model", "character", "optimized"],
            "custom_data": {
                "polygon_count": 12000
            }
        }
    )

    # Version 3 (minor update)
    test_file.write_text("Final content")
    version_manager.create_version(
        test_file,
        metadata={
            "creator": "john_doe",
            "tool_version": "maya_2024",
            "description": "Fixed UVs",
            "tags": ["model", "character", "uv_fix"],
            "custom_data": {
                "polygon_count": 12000,
                "uv_shells": 12
            }
        }
    )

    # Get and analyze history
    print("\nCollecting version history...")
    history = version_manager.dump_asset_history(
        test_file,
        include_storage_data=True,
        include_timeline=True
    )

    # Print basic summary
    print_history_summary(history)

    # Print timeline
    print_timeline(history)

    # Analyze patterns
    analyze_version_patterns(history)

    # Analyze metadata changes
    if 'storage_versions' in history:
        print("\nMetadata Evolution:")
        versions = history['storage_versions']
        for version in versions:
            print(f"\nVersion in {version['storage_type']}:")
            metadata = version['metadata']
            print(f"- Creator: {metadata.get('creator', 'Unknown')}")
            print(f"- Description: {metadata.get('description', 'Unknown')}")
            if 'custom_data' in metadata:
                print("- Custom Data:")
                for key, value in metadata['custom_data'].items():
                    print(f"  {key}: {value}")

    # Save history to file
    history_file = Path("asset_history.json")
    print(f"\nSaving history to {history_file}...")
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    # Cleanup
    print("\nCleaning up...")
    cleanup_paths = [
        test_file,
        history_file,
        Path("./disk_storage"),
        Path("./git_storage"),
        Path("versions.db")
    ]
    for path in cleanup_paths:
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
        except Exception as e:
            print(f"Error cleaning up {path}: {e}")

if __name__ == "__main__":
    main()
