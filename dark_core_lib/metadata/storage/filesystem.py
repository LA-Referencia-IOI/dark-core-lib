"""Filesystem-backed metadata storage."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from dark_core_lib.metadata.storage.base import (
    MetadataStorage,
    StoredDocument,
    infer_format_from_content_type,
)
from dark_core_lib.metadata.storage.exceptions import MetadataNotFoundError, StorageError


logger = logging.getLogger(__name__)

FORMAT_EXTENSIONS = {
    "json": ".json",
    "xml": ".xml",
    "text": ".txt",
}


class FileSystemMetadataStorage(MetadataStorage):
    """Content-addressed metadata storage on a shared filesystem."""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()

    def _ensure_storage_directory(self) -> None:
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise StorageError(f"Failed to create storage directory: {exc}") from exc

    def _calculate_md5(self, content: bytes) -> str:
        return hashlib.md5(content).hexdigest()

    def _sanitize_cid(self, cid: str) -> str:
        safe_cid = Path(cid).name
        if safe_cid != cid:
            raise StorageError(f"Invalid CID format: {cid}")
        return safe_cid

    def _get_meta_path(self, cid: str) -> Path:
        return self.storage_path / f"{self._sanitize_cid(cid)}.meta"

    def _get_content_path(self, cid: str, content_type: str) -> Path:
        ext = FORMAT_EXTENSIONS.get(infer_format_from_content_type(content_type), ".bin")
        return self.storage_path / f"{self._sanitize_cid(cid)}{ext}"

    def store_document(
        self,
        content: bytes,
        content_type: str,
        schema: Optional[str] = None,
    ) -> str:
        try:
            cid = self._calculate_md5(content)
            content_path = self._get_content_path(cid, content_type)
            meta_path = self._get_meta_path(cid)

            temp_content = content_path.with_suffix(".tmp")
            temp_content.write_bytes(content)
            temp_content.replace(content_path)

            temp_meta = meta_path.with_suffix(".tmp")
            temp_meta.write_text(
                json.dumps(
                    {
                        "content_type": content_type,
                        "format": infer_format_from_content_type(content_type),
                        "schema": schema,
                    }
                ),
                encoding="utf-8",
            )
            temp_meta.replace(meta_path)
            return cid
        except Exception as exc:
            raise StorageError(f"Metadata storage failed: {exc}") from exc

    def get_document(self, cid: str) -> StoredDocument:
        try:
            meta_path = self._get_meta_path(cid)
            if not meta_path.exists():
                raise MetadataNotFoundError(f"Metadata not found for CID: {cid}")

            meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
            content_type = meta_data.get("content_type")
            if not content_type:
                format_name = meta_data.get("format", "json")
                if format_name == "json":
                    content_type = "application/json"
                elif format_name == "xml":
                    content_type = "application/xml"
                else:
                    content_type = "text/plain"

            content_path = self._get_content_path(cid, content_type)
            if not content_path.exists():
                raise MetadataNotFoundError(f"Content file not found for CID: {cid}")

            return StoredDocument(
                content=content_path.read_bytes(),
                content_type=content_type,
                schema=meta_data.get("schema"),
            )
        except MetadataNotFoundError:
            raise
        except Exception as exc:
            raise StorageError(f"Metadata retrieval failed: {exc}") from exc

    def health_check(self) -> bool:
        try:
            if not self.storage_path.exists():
                return False
            test_file = self.storage_path / ".health_check"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception as exc:
            logger.error(f"Storage health check failed: {exc}")
            return False
