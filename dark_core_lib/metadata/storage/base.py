"""Abstract base classes for shared metadata storage backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


FORMAT_TO_CONTENT_TYPE = {
    "json": "application/json",
    "xml": "application/xml",
    "text": "text/plain",
}

CONTENT_TYPE_TO_FORMAT = {
    "application/json": "json",
    "application/xml": "xml",
    "text/xml": "xml",
    "text/plain": "text",
}


def infer_format_from_content_type(content_type: str) -> str:
    """Infer a legacy format label from a MIME type."""
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized in CONTENT_TYPE_TO_FORMAT:
        return CONTENT_TYPE_TO_FORMAT[normalized]
    if "json" in normalized:
        return "json"
    if "xml" in normalized:
        return "xml"
    if normalized.startswith("text/"):
        return "text"
    return "text"


@dataclass(frozen=True)
class StoredDocument:
    """Raw document fetched from metadata storage."""

    content: bytes
    content_type: str
    schema: Optional[str] = None

    @property
    def text(self) -> str:
        """Decode the content as UTF-8 text."""
        return self.content.decode("utf-8")

    @property
    def format(self) -> str:
        """Return the legacy format label for compatibility."""
        return infer_format_from_content_type(self.content_type)


class MetadataStorage(ABC):
    """Abstract interface for metadata persistence."""

    @abstractmethod
    def store_document(
        self,
        content: bytes,
        content_type: str,
        schema: Optional[str] = None,
    ) -> str:
        """Persist a raw document and return its CID."""

    @abstractmethod
    def get_document(self, cid: str) -> StoredDocument:
        """Fetch a previously stored raw document by CID."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check whether the backend is healthy."""

    def store_metadata(self, content: str, format: str) -> str:
        """Backward-compatible text storage wrapper."""
        content_type = FORMAT_TO_CONTENT_TYPE.get(format.lower(), "text/plain")
        return self.store_document(content.encode("utf-8"), content_type=content_type)

    def get_metadata(self, cid: str) -> tuple[str, str]:
        """Backward-compatible text retrieval wrapper."""
        document = self.get_document(cid)
        return document.text, document.format
