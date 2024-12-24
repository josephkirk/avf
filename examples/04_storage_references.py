"""
Storage reference example showing how to create versions from existing content.

This example demonstrates:
- Creating versions from existing files
- Creating versions from Git commits
- Listing available references
- Cross-referencing versions
"""

from pathlib import Path

from avf import AssetVersion, DiskStorage, GitStorage, ReferenceType, StorageReference


def print_reference_info(ref):
    """Helper to print reference information."""
    print("\nReference:")
    print(f"- Storage Type: {ref.storage_type}")
    print(f"- Storage ID: {ref.storage_id}")
    print(f"- Path: {ref.path}")
    print(f"- Type: {ref.reference_type}")
    print("- Metadata:")
    for key, value in ref.metadata.items():
        print(f"  {key}: {value}")


def main():
    # Set up storage backends
    storage = {
        "disk": DiskStorage(Path("./disk_storage")),
        "git": GitStorage(Path("./git_storage")),
    }

    # Create version manager
    AssetVersion(storage)

    # Create some existing files
    base_path = Path("./existing_files")
    base_path.mkdir(exist_ok=True)

    model_file = base_path / "existing_model.fbx"
    model_file.write_text("Existing model data")

    texture_file = base_path / "existing_texture.png"
    texture_file.write_text("Existing texture data")

    # Create storage references
    print("Creating storage references...")

    # Reference for existing model
    model_ref = StorageReference(
        storage_type="disk",
        storage_id="existing_model",
        path=model_file,
        reference_type=ReferenceType.FILE,
        metadata={"size": len(model_file.read_bytes()), "original_path": str(model_file)},
    )

    # Create version from model reference
    print("\nCreating version from model reference...")
    storage["disk"].create_version_from_reference(
        reference=model_ref,
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Imported existing model",
            "tags": ["model", "imported"],
            "custom_data": {"source": "external", "import_date": "2024-01-15"},
        },
    )

    # List all references in disk storage
    print("\nListing all disk references:")
    disk_refs = storage["disk"].list_references()
    for ref in disk_refs:
        print_reference_info(ref)

    # Create Git commit and reference it
    git_storage = storage["git"]
    base_repo = Path("./git_storage")
    asset_file = base_repo / "asset.fbx"
    asset_file.parent.mkdir(parents=True, exist_ok=True)
    asset_file.write_text("Git asset content")

    # Create Git commit
    print("\nCreating Git version...")
    git_version = git_storage.store_version(
        asset_file,
        {
            "creator": "john_doe",
            "tool_version": "git_1.0",
            "description": "Initial commit",
        },
    )

    # List Git references
    print("\nListing Git references:")
    git_refs = storage["git"].list_references()
    for ref in git_refs:
        print_reference_info(ref)

    # Create version from Git reference
    git_ref = StorageReference(
        storage_type="git",
        storage_id=git_version,  # Use commit hash
        path=asset_file,
        reference_type=ReferenceType.COMMIT,
        metadata={"commit_hash": git_version, "branch": "main"},
    )

    print("\nCreating version from Git reference...")
    new_git_version = git_storage.create_version_from_reference(
        reference=git_ref,
        metadata={
            "creator": "john_doe",
            "tool_version": "git_1.0",
            "description": "Version from existing commit",
            "tags": ["imported", "git"],
            "custom_data": {"source_commit": git_version, "import_date": "2024-01-15"},
        },
    )

    # Demonstrate cross-storage referencing
    print("\nDemonstrating cross-storage version creation...")

    # Create version in disk storage from Git content
    disk_from_git = storage["disk"].store_version(
        asset_file,
        {
            "creator": "jane_doe",
            "tool_version": "git_1.0",
            "description": "Imported from Git",
            "tags": ["imported", "cross-storage"],
            "custom_data": {"source_storage": "git", "source_id": git_version},
        },
    )

    # Print version information
    print("\nVersion Information:")
    print("\nGit Version:")
    git_info = git_storage.get_version_info(new_git_version)
    for key, value in git_info.items():
        print(f"- {key}: {value}")

    print("\nDisk Version (from Git):")
    disk_info = storage["disk"].get_version_info(disk_from_git)
    for key, value in disk_info.items():
        print(f"- {key}: {value}")

    # Cleanup
    print("\nCleaning up...")
    cleanup_paths = [base_path, Path("./disk_storage"), Path("./git_storage")]
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
