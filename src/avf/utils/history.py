"""Utilities for asset version history management."""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..storage.base import StorageBackend
from ..storage.reference import StorageReference


class AssetHistoryDumper:
    """Utility class to dump asset version history."""

    def __init__(self, storage_backends: Dict[str, StorageBackend]):
        """Initialize dumper with storage backends.

        Args:
            storage_backends: Dictionary of storage backends
        """
        self.storage_backends = storage_backends

    def _collect_storage_references(
        self,
        path: Optional[Path] = None
    ) -> Dict[str, List[StorageReference]]:
        """Collect references from all storage backends.

        Args:
            path: Optional path to filter references

        Returns:
            Dictionary mapping storage type to list of references
        """
        refs: Dict[str, List[StorageReference]] = {}

        for storage_type, backend in self.storage_backends.items():
            try:
                backend_refs = backend.list_references(
                    path_pattern=str(path) if path else None
                )
                refs[storage_type] = backend_refs
            except Exception:
                refs[storage_type] = []

        return refs

    def _build_storage_summary(
        self,
        references: Dict[str, List[StorageReference]]
    ) -> Dict[str, Dict[str, Any]]:
        """Build storage summary from references.

        Args:
            references: Dictionary of storage references

        Returns:
            Storage summary data
        """
        summary: Dict[str, Dict[str, Any]] = {}

        for storage_type, refs in references.items():
            storage_data = {
                "versions": len(refs),
                "references": [
                    {
                        "id": ref.storage_id,
                        "path": str(ref.path),
                        "type": ref.reference_type,
                        "metadata": ref.metadata
                    }
                    for ref in refs
                ]
            }

            # Calculate storage type specific stats
            metadata_keys = set()
            for ref in refs:
                metadata_keys.update(ref.metadata.keys())

            for key in metadata_keys:
                values = [
                    ref.metadata.get(key)
                    for ref in refs
                    if key in ref.metadata
                ]
                if values:
                    storage_data[f"unique_{key}"] = len(set(values))

            summary[storage_type] = storage_data

        return summary

    def _extract_timeline(
        self,
        references: Dict[str, List[StorageReference]]
    ) -> List[Dict[str, Any]]:
        """Extract timeline from references.

        Args:
            references: Dictionary of storage references

        Returns:
            List of timeline events
        """
        events = []

        for storage_type, refs in references.items():
            for ref in refs:
                event = {
                    "storage_type": storage_type,
                    "reference_id": ref.storage_id,
                    "path": str(ref.path),
                    "type": ref.reference_type,
                    "timestamp": ref.metadata.get(
                        "timestamp",
                        ref.metadata.get("time", ref.metadata.get("date"))
                    ),
                    "action": ref.metadata.get("action", "unknown"),
                    "metadata": ref.metadata
                }
                events.append(event)

        # Sort by timestamp
        events.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "")
        return events

    def dump_history(
        self,
        file_path: Path,
        include_storage_data: bool = True,
        include_timeline: bool = True,
        version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Dump complete version history of an asset.

        Args:
            file_path: Asset file path
            include_storage_data: Include backend-specific data
            include_timeline: Include history timeline
            version_id: Optional specific version to dump

        Returns:
            Complete version history as dictionary
        """
        data = {
            "asset_path": str(file_path),
            "metadata": {},
            "versions": []
        }

        # Get references from all storage backends
        references = self._collect_storage_references(file_path)

        # Build storage summary
        data["metadata"]["storage_summary"] = self._build_storage_summary(references)

        # Add timeline if requested
        if include_timeline:
            data["timeline"] = self._extract_timeline(references)

        # Add basic metadata
        if references:
            first_event = min(
                (
                    ref.metadata.get("timestamp", datetime.max.isoformat())
                    for refs in references.values()
                    for ref in refs
                ),
                default=None
            )
            last_event = max(
                (
                    ref.metadata.get("timestamp", datetime.min.isoformat())
                    for refs in references.values()
                    for ref in refs
                ),
                default=None
            )

            if first_event and last_event:
                data["metadata"].update({
                    "first_version": first_event,
                    "latest_version": last_event,
                    "total_references": sum(len(refs) for refs in references.values())
                })

        # Add comprehensive storage data if requested
        if include_storage_data:
            storage_versions = []

            for storage_type, refs in references.items():
                backend = self.storage_backends[storage_type]

                for ref in refs:
                    try:
                        version_info = backend.get_version_info(ref.storage_id)
                        version_data = {
                            "storage_type": storage_type,
                            "storage_id": ref.storage_id,
                            "path": str(ref.path),
                            "reference_type": ref.reference_type,
                            "metadata": version_info
                        }
                        storage_versions.append(version_data)
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error getting version info: {e}")

            data["storage_versions"] = storage_versions

        return data
