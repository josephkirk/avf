from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AssetMetadata(BaseModel):
    """Metadata for asset versions"""

    creator: str = Field(..., description="Name of the creator")
    tool_version: str = Field(..., description="Version of the tool used")
    description: Optional[str] = Field(None, description="Optional description")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    creation_time: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "creator": "john_doe",
                "tool_version": "maya_2024",
                "description": "Updated character textures",
                "tags": ["character", "texture"],
                "custom_data": {"resolution": "4k", "format": "png"},
            }
        }
    }
