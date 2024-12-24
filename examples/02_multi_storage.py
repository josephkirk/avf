"""
Multi-storage example showing how to use multiple storage backends.

This example demonstrates:
- Setting up multiple storage backends (Disk and Git)
- Creating versions across all storages
- Retrieving versions from specific storage
- Comparing versions across storages
"""
from pathlib import Path

from avf import AssetVersion, DiskStorage, GitStorage


def main():
    # Set up storage backends
    storage = {
        "disk": DiskStorage(Path("./disk_storage")),
        "git": GitStorage(
            Path("./git_storage"),
            branch_prefix="assets"
        )
    }

    # Create version manager
    version_manager = AssetVersion(storage)

    # Create a sample file
    test_file = Path("test_model.fbx")
    test_file.write_text("Model data v1")

    # Create version across all storages
    print("Creating version 1...")
    v1_ids = version_manager.create_version(
        file_path=test_file,
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Initial model",
            "tags": ["character", "model"],
            "custom_data": {
                "polygon_count": 1500,
                "texture_size": "2k"
            }
        }
    )

    # Print storage locations
    print("\nVersion 1 locations:")
    for storage_type, version_id in v1_ids.items():
        print(f"{storage_type}: {version_id.storage_id}")
        info = version_manager.get_version_info(storage_type, version_id.storage_id)
        print(f"Metadata in {storage_type}:")
        print(f"- Description: {info.description}")
        print(f"- Tags: {info.tags}")

    # Update file
    test_file.write_text("Model data v2")

    # Create second version
    print("\nCreating version 2...")
    v2_ids = version_manager.create_version(
        file_path=test_file,
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Optimized model",
            "tags": ["character", "model", "optimized"],
            "custom_data": {
                "polygon_count": 1200,
                "texture_size": "2k"
            }
        }
    )

    # Compare versions from different storages
    print("\nComparing versions across storages:")

    # Get v1 from disk
    v1_disk = version_manager.get_version(
        "disk",
        v1_ids["disk"].storage_id,
        Path("v1_from_disk.fbx")
    )

    # Get v2 from git
    v2_git = version_manager.get_version(
        "git",
        v2_ids["git"].storage_id,
        Path("v2_from_git.fbx")
    )

    print(f"V1 from disk: {v1_disk.read_text()}")
    print(f"V2 from git: {v2_git.read_text()}")

    # Dump version history
    print("\nDumping version history...")
    history = version_manager.dump_asset_history(
        test_file,
        include_storage_data=True
    )

    print("\nStorage summary:")
    for storage_type, summary in history["metadata"]["storage_summary"].items():
        print(f"\n{storage_type}:")
        print(f"- Total versions: {summary['versions']}")

    # Cleanup
    cleanup_files = [test_file, v1_disk, v2_git]
    for file in cleanup_files:
        if file.exists():
            file.unlink()

if __name__ == "__main__":
    main()
