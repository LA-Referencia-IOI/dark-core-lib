from __future__ import annotations

"""Shared metadata orchestration helpers."""

import json
from typing import Mapping, Optional, Union

from dark_core_lib.metadata.schemas import Level1Metadata
from dark_core_lib.metadata.storage import MetadataStorage, StoredDocument


class MetadataService:
    """Read and write Level-1 / Level-2 metadata through a shared storage backend."""

    def __init__(self, storage: MetadataStorage):
        self.storage = storage

    def load_level1(self, level1_cid: str) -> Level1Metadata:
        """Load and validate a Level-1 JSON document."""
        document = self.storage.get_document(level1_cid)
        return self._decode_level1_document(document)

    def load_level2(self, level1: Level1Metadata) -> StoredDocument:
        """Load the raw Level-2 document referenced by a Level-1 payload."""
        level2_cid = level1.original_metadata.cid
        if not level2_cid:
            raise ValueError("Level-1 metadata does not contain an original metadata CID")
        return self.storage.get_document(level2_cid)

    def store_level2(self, content: bytes, content_type: str, schema: Optional[str] = None) -> str:
        """Persist the original Level-2 document and return its CID."""
        return self.storage.store_document(content=content, content_type=content_type, schema=schema)

    def with_level2_reference(
        self,
        level1: Union[Level1Metadata, Mapping[str, object]],
        level2_cid: str,
    ) -> Level1Metadata:
        """Return a validated Level-1 payload with the internal L2 CID injected."""
        if isinstance(level1, Level1Metadata):
            level1_data = level1.model_dump(mode="json", by_alias=True)
        else:
            level1_data = dict(level1)

        original_metadata = dict(level1_data.get("original_metadata") or {})
        original_metadata["cid"] = level2_cid
        level1_data["original_metadata"] = original_metadata
        return Level1Metadata.model_validate(level1_data)

    def store_level1(self, level1: Union[Level1Metadata, Mapping[str, object]]) -> str:
        """Persist a Level-1 document as canonical JSON and return its CID."""
        level1_model = level1 if isinstance(level1, Level1Metadata) else Level1Metadata.model_validate(level1)
        payload = level1_model.model_dump(mode="json", by_alias=True)
        return self.storage.store_document(
            content=json.dumps(payload).encode("utf-8"),
            content_type="application/json",
        )

    def store_level1_with_level2_reference(
        self,
        level1: Union[Level1Metadata, Mapping[str, object]],
        level2_cid: str,
    ) -> tuple[Level1Metadata, str]:
        """Inject the Level-2 CID into Level-1, store it, and return both model and CID."""
        level1_model = self.with_level2_reference(level1, level2_cid)
        level1_cid = self.store_level1(level1_model)
        return level1_model, level1_cid

    @staticmethod
    def _decode_level1_document(document: StoredDocument) -> Level1Metadata:
        """Decode and validate a Level-1 JSON document."""
        if "json" not in document.content_type:
            raise ValueError("Level-1 metadata must be stored as JSON")
        return Level1Metadata.model_validate_json(document.content)
