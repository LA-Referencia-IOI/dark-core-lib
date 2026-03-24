"""Metadata storage specific exceptions."""


class StorageError(Exception):
    """Base exception for metadata storage operations."""


class MetadataNotFoundError(StorageError):
    """Raised when a content identifier does not exist."""
