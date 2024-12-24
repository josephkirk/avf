from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Many-to-many relationship for version tags
version_tags = Table(
    'version_tags',
    Base.metadata,
    Column('version_id', Integer, ForeignKey('versions.id')),
    Column('tag', String)
)

class Version(Base):
    __tablename__ = 'versions'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)
    creator = Column(String, nullable=False)
    tool_version = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    custom_data = Column(JSON)
    
    # Relationship with storage locations
    storage_locations = relationship("VersionStorage", back_populates="version")
    tags = relationship("Tag", secondary=version_tags)
    
    def to_dict(self):
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
    __tablename__ = 'version_storage'
    
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('versions.id'))
    storage_type = Column(String, nullable=False)  # e.g., 'disk', 'git'
    storage_id = Column(String, nullable=False)    # backend-specific identifier
    created_at = Column(DateTime, default=datetime.utcnow)
    
    version = relationship("Version", back_populates="storage_locations")
    
    def to_dict(self):
        return {
            "storage_type": self.storage_type,
            "storage_id": self.storage_id,
            "created_at": self.created_at
        }

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
