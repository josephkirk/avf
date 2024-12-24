"""
Database integration example showing version tracking and querying.

This example demonstrates:
- Setting up SQLite database
- Tracking versions in database
- Querying version history
- Finding versions by criteria
"""

from pathlib import Path

from avf import AssetVersion, DatabaseConnection, DiskStorage, SQLiteVersionRepository


def print_version_info(version):
    """Helper to print version information."""
    print(f"\nVersion {version['id']}:")
    print(f"- Creator: {version['creator']}")
    print(f"- Tool: {version['tool_version']}")
    print(f"- Description: {version['description']}")
    print(f"- Tags: {version['tags']}")
    print(f"- Created: {version['created_at']}")
    if version.get("custom_data"):
        print("- Custom Data:")
        for key, value in version["custom_data"].items():
            print(f"  {key}: {value}")


def main():
    # Set up database
    db = DatabaseConnection("sqlite:///versions.db")
    db.create_tables()

    # Create repository
    repo = SQLiteVersionRepository(db)

    # Set up storage
    storage = {"disk": DiskStorage(Path("./disk_storage"))}

    # Create version manager with repository
    version_manager = AssetVersion(storage_backends=storage, version_repository=repo)

    # Create some test files
    files = {"character": Path("character.fbx"), "texture": Path("texture.png")}

    # Create some versions
    print("Creating test versions...")

    # Character versions
    files["character"].write_text("Character mesh v1")
    version_manager.create_version(
        file_path=files["character"],
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Base character model",
            "tags": ["character", "model", "base"],
            "custom_data": {"polygon_count": 15000, "rig_type": "biped"},
        },
    )

    files["character"].write_text("Character mesh v2")
    version_manager.create_version(
        file_path=files["character"],
        metadata={
            "creator": "jane_doe",
            "tool_version": "maya_2024",
            "description": "Optimized character model",
            "tags": ["character", "model", "optimized"],
            "custom_data": {"polygon_count": 12000, "rig_type": "biped"},
        },
    )

    # Texture versions
    files["texture"].write_text("Texture data v1")
    version_manager.create_version(
        file_path=files["texture"],
        metadata={
            "creator": "john_doe",
            "tool_version": "substance_2024",
            "description": "Base textures",
            "tags": ["texture", "diffuse"],
            "custom_data": {"resolution": "2k", "format": "png"},
        },
    )

    # Query examples
    print("\nFinding versions by creator:")
    jane_versions = repo.find_versions(creator="jane_doe")
    for version in jane_versions:
        print_version_info(version)

    print("\nFinding versions by tag:")
    model_versions = repo.find_versions(tags=["model"])
    for version in model_versions:
        print_version_info(version)

    print("\nGetting version history for character:")
    character_versions = repo.find_versions(file_path=files["character"])
    for version in character_versions:
        print_version_info(version)
        # Get storage locations
        locations = repo.get_storage_locations(version["id"])
        print("- Storage Locations:")
        for loc in locations:
            print(f"  {loc['storage_type']}: {loc['storage_id']}")

    # Dump complete history
    print("\nDumping complete history for character:")
    history = version_manager.dump_asset_history(
        files["character"], include_storage_data=True, include_timeline=True
    )

    print("\nTimeline:")
    for event in history.get("timeline", []):
        print(f"{event['timestamp']}: {event['action']}")

    # Cleanup
    for file in files.values():
        if file.exists():
            file.unlink()


if __name__ == "__main__":
    main()
