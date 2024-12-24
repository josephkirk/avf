from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

# Many-to-many relationship for version tags
version_tags = Table(
    'version_tags',
    Base.metadata,
    Column('version_id', Integer, ForeignKey('versions.id', ondelete='CASCADE')),
    Column('tag', String)
)

class Version(Base):
    """Model representing a version of an asset"""
    __tablename__ = 'versions'

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    creator: Mapped[str] = mapped_column(String, nullable=False)
    tool_version: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    custom_data: Mapped[Dict[str, Any]] = mapped_column(JSON)

    # Relationship with storage locations
    storage_locations: Mapped[List["VersionStorage"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship(secondary=version_tags)

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary representation"""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "creator": self.creator,
            "tool_version": self.tool_version,
            "description": self.description,
            "created_at": self.created_at,
            "custom_data": self.custom_data,
            "tags": [tag.name for tag in self.tags]
        }

class VersionStorage(Base):
    """Model representing storage location for a version"""
    __tablename__ = 'version_storage'

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey('versions.id', ondelete='CASCADE'))
    storage_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., 'disk', 'git'
    storage_id: Mapped[str] = mapped_column(String, nullable=False)    # backend-specific identifier
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    version: Mapped["Version"] = relationship(back_populates="storage_locations")

    def to_dict(self) -> Dict[str, Any]:
        """Convert storage location to dictionary representation"""
        return {
            "storage_type": self.storage_type,
            "storage_id": self.storage_id,
            "created_at": self.created_at
        }

class Tag(Base):
    """Model representing a tag that can be applied to versions"""
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
