from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..database.connection import DatabaseConnection
from .base import VersionRepository
from .models import Tag, Version, VersionStorage


class SQLiteVersionRepository(VersionRepository):
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize SQLite repository

        Args:
            db_connection: Database connection
        """
        self.db = db_connection

    def create_version(
        self,
        file_path: Path,
        creator: str,
        tool_version: str,
        description: Optional[str],
        tags: List[str],
        custom_data: Dict[str, Any]
    ) -> int:
        with self.db.session() as session:
            # Create or get tags
            tag_objects = []
            for tag_name in tags:
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                tag_objects.append(tag)

            # Create version
            version = Version(
                file_path=str(file_path),
                creator=creator,
                tool_version=tool_version,
                description=description,
                custom_data=custom_data,
                tags=tag_objects
            )
            session.add(version)
            session.commit()
            return version.id

    def add_storage_location(
        self,
        version_id: int,
        storage_type: str,
        storage_id: str
    ) -> None:
        with self.db.session() as session:
            storage = VersionStorage(
                version_id=version_id,
                storage_type=storage_type,
                storage_id=storage_id
            )
            session.add(storage)

    def get_version_info(self, version_id: int) -> Dict[str, Any]:
        with self.db.session() as session:
            version = session.query(Version).get(version_id)
            if not version:
                raise KeyError(f"Version {version_id} not found")
            return version.to_dict()

    def get_storage_locations(self, version_id: int) -> List[Dict[str, Any]]:
        with self.db.session() as session:
            locations = session.query(VersionStorage).filter_by(version_id=version_id).all()
            return [loc.to_dict() for loc in locations]

    def find_versions(
        self,
        file_path: Optional[Path] = None,
        tags: Optional[List[str]] = None,
        creator: Optional[str] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        with self.db.session() as session:
            query = session.query(Version)

            # Apply filters
            if file_path:
                query = query.filter(Version.file_path == str(file_path))
            if creator:
                query = query.filter(Version.creator == creator)
            if after:
                query = query.filter(Version.created_at >= after)
            if before:
                query = query.filter(Version.created_at <= before)

            # Apply tag filters
            if tags:
                for tag in tags:
                    query = query.filter(Version.tags.any(name=tag))

            versions = query.all()
            return [v.to_dict() for v in versions]

    def get_all_tags(self) -> List[str]:
        """Get all unique tags in the system

        Returns:
            List of tag names
        """
        with self.db.session() as session:
            tags = session.query(Tag.name).distinct().all()
            return [tag[0] for tag in tags]

    def get_versions_by_creator(self, creator: str) -> List[Dict[str, Any]]:
        """Get all versions by a specific creator

        Args:
            creator: Creator name

        Returns:
            List of versions
        """
        with self.db.session() as session:
            versions = session.query(Version).filter_by(creator=creator).all()
            return [v.to_dict() for v in versions]

    def delete_version(self, version_id: int) -> None:
        """Delete a version and its storage locations

        Args:
            version_id: Version ID to delete
        """
        with self.db.session() as session:
            version = session.query(Version).get(version_id)
            if version:
                session.delete(version)

    def update_version_metadata(
        self,
        version_id: int,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update version metadata

        Args:
            version_id: Version ID to update
            description: New description (optional)
            tags: New tags (optional)
            custom_data: New custom data (optional)

        Returns:
            Updated version information
        """
        with self.db.session() as session:
            version = session.query(Version).get(version_id)
            if not version:
                raise KeyError(f"Version {version_id} not found")

            if description is not None:
                version.description = description

            if tags is not None:
                # Create or get tags
                tag_objects = []
                for tag_name in tags:
                    tag = session.query(Tag).filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                    tag_objects.append(tag)
                version.tags = tag_objects

            if custom_data is not None:
                version.custom_data = custom_data

            session.commit()
            return version.to_dict()

    def get_version_history(self, file_path: Path) -> List[Dict[str, Any]]:
        """Get version history for a specific file

        Args:
            file_path: Path to the file

        Returns:
            List of versions ordered by creation date
        """
        with self.db.session() as session:
            versions = (
                session.query(Version)
                .filter_by(file_path=str(file_path))
                .order_by(Version.created_at.desc())
                .all()
            )
            return [v.to_dict() for v in versions]
