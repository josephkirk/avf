"""Storage reference types for version creation from existing storage."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field


class ReferenceType(str, Enum):
    """Types of storage references."""

    FILE = "file"  # Direct file reference
    COMMIT = "commit"  # Git commit
    CHANGELIST = "changelist"  # Perforce changelist
    SNAPSHOT = "snapshot"  # Generic point-in-time reference


class StorageReference(BaseModel):
    """Reference to content that exists in a storage backend."""

    storage_type: str = Field(..., description="Type of storage backend")
    storage_id: str = Field(..., description="Identifier in the storage system")
    path: Path = Field(..., description="Path in the storage system")
    reference_type: ReferenceType = Field(..., description="Type of reference")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional reference metadata"
    )
