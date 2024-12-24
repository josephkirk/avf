"""
Basic usage example showing how to set up AVF and create versions.

This example demonstrates:
- Setting up a basic disk storage
- Creating versions
- Retrieving versions
- Getting version info
"""

from pathlib import Path

from avf import AssetVersion, DiskStorage


def main():
    # Set up storage directory
    storage_dir = Path("./storage")
    storage = {"disk": DiskStorage(storage_dir)}

    # Create version manager
    version_manager = AssetVersion(storage)

    # Create a sample file
    test_file = Path("test_asset.txt")
    test_file.write_text("This is version 1")

    # Create first version
    print("Creating version 1...")
    v1_ids = version_manager.create_version(
        file_path=test_file,
        metadata={
            "creator": "john_doe",
            "tool_version": "1.0",
            "description": "Initial version",
            "tags": ["test"],
            "custom_data": {"version": 1},
        },
    )

    # Update file content
    test_file.write_text("This is version 2")

    # Create second version
    print("Creating version 2...")
    v2_ids = version_manager.create_version(
        file_path=test_file,
        metadata={
            "creator": "john_doe",
            "tool_version": "1.0",
            "description": "Updated content",
            "tags": ["test", "updated"],
            "custom_data": {"version": 2},
        },
    )

    # Get info about versions
    print("\nVersion 1 info:")
    v1_info = version_manager.get_version_info("disk", v1_ids["disk"].storage_id)
    print(f"Description: {v1_info.description}")
    print(f"Creator: {v1_info.creator}")
    print(f"Tags: {v1_info.tags}")

    print("\nVersion 2 info:")
    v2_info = version_manager.get_version_info("disk", v2_ids["disk"].storage_id)
    print(f"Description: {v2_info.description}")
    print(f"Creator: {v2_info.creator}")
    print(f"Tags: {v2_info.tags}")

    # Retrieve an old version
    v1_path = version_manager.get_version(
        "disk", v1_ids["disk"].storage_id, Path("restored_v1.txt")
    )
    print(f"\nRestored version 1 content: {v1_path.read_text()}")

    # Cleanup
    test_file.unlink()
    v1_path.unlink()
    storage_dir.rmdir()


if __name__ == "__main__":
    main()
