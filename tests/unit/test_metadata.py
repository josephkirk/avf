"""Tests for metadata models."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from avf.metadata import AssetMetadata


def test_create_valid_metadata(test_metadata, valid_metadata):
    """Test creating metadata with valid data."""
    # Test dictionary to model conversion
    metadata = AssetMetadata(**test_metadata)

    assert metadata.creator == test_metadata["creator"]
    assert metadata.tool_version == test_metadata["tool_version"]
    assert metadata.description == test_metadata["description"]
    assert metadata.tags == test_metadata["tags"]
    assert metadata.custom_data == test_metadata["custom_data"]
    assert isinstance(metadata.creation_time, datetime)

    # Test fixture
    assert valid_metadata.creator == test_metadata["creator"]
    assert valid_metadata.tool_version == test_metadata["tool_version"]

def test_metadata_required_fields():
    """Test that required fields are enforced."""
    with pytest.raises(ValidationError) as exc_info:
        AssetMetadata()
    assert "creator" in str(exc_info.value)
    assert "tool_version" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        AssetMetadata(creator="test_user")
    assert "tool_version" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        AssetMetadata(tool_version="test_1.0")
    assert "creator" in str(exc_info.value)

def test_metadata_optional_fields():
    """Test optional fields handling."""
    metadata = AssetMetadata(
        creator="test_user",
        tool_version="test_1.0"
    )

    assert metadata.description is None
    assert metadata.tags == []
    assert metadata.custom_data == {}
    assert isinstance(metadata.creation_time, datetime)

def test_metadata_field_types():
    """Test metadata field type validation."""
    with pytest.raises(ValidationError) as exc_info:
        AssetMetadata(
            creator=123,  # Should be string
            tool_version="test_1.0"
        )
    assert "creator" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        AssetMetadata(
            creator="test_user",
            tool_version="test_1.0",
            tags="not_a_list"  # Should be list
        )
    assert "tags" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        AssetMetadata(
            creator="test_user",
            tool_version="test_1.0",
            custom_data=["not_a_dict"]  # Should be dict
        )
    assert "custom_data" in str(exc_info.value)

def test_metadata_model_methods(valid_metadata):
    """Test metadata model methods."""
    # Test model_dump (dict conversion)
    data = valid_metadata.model_dump()
    assert isinstance(data, dict)
    assert data["creator"] == valid_metadata.creator
    assert data["tool_version"] == valid_metadata.tool_version
    assert "creation_time" in data

    # Test model_dump_json (JSON serialization)
    json_str = valid_metadata.model_dump_json()
    assert isinstance(json_str, str)
    assert valid_metadata.creator in json_str
    assert valid_metadata.tool_version in json_str

def test_metadata_examples():
    """Test metadata model example configuration."""
    example = AssetMetadata.model_config["json_schema_extra"]["example"]
    assert isinstance(example, dict)

    # Test example is valid
    metadata = AssetMetadata(**example)
    assert metadata.creator == example["creator"]
    assert metadata.tool_version == example["tool_version"]
