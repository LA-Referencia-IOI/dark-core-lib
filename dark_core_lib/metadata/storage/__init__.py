"""Shared metadata storage implementations."""

from dark_core_lib.metadata.storage.base import (
    FORMAT_TO_CONTENT_TYPE,
    MetadataStorage,
    StoredDocument,
)
from dark_core_lib.metadata.storage.exceptions import MetadataNotFoundError, StorageError
from dark_core_lib.metadata.storage.filesystem import FileSystemMetadataStorage
from dark_core_lib.metadata.storage.store_api import StoreApiMetadataStorage


def get_metadata_storage(storage_type: str = "filesystem", **kwargs) -> MetadataStorage:
    """Factory function for shared metadata storage backends."""
    storage_type_normalized = storage_type.lower()
    if storage_type_normalized == "filesystem":
        storage_path = kwargs.get("storage_path", "./metadata_storage")
        return FileSystemMetadataStorage(storage_path)
    if storage_type_normalized == "store_api":
        store_api_url = kwargs.get("store_api_url", "http://localhost:8002")
        timeout_seconds = kwargs.get("timeout_seconds", 10.0)
        return StoreApiMetadataStorage(store_api_url, timeout_seconds=timeout_seconds)
    raise ValueError(f"Unsupported storage type: {storage_type}")


__all__ = [
    "FORMAT_TO_CONTENT_TYPE",
    "MetadataNotFoundError",
    "MetadataStorage",
    "StorageError",
    "StoredDocument",
    "FileSystemMetadataStorage",
    "StoreApiMetadataStorage",
    "get_metadata_storage",
]
