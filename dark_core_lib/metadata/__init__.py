"""Shared metadata models and storage helpers."""

from dark_core_lib.metadata.schemas import (
    AlternateIdentifierL1,
    Level1Metadata,
    MetadataSchemaType,
    OriginalMetadataRef,
)
from dark_core_lib.metadata.service import MetadataService
from dark_core_lib.metadata.storage import (
    FORMAT_TO_CONTENT_TYPE,
    MetadataNotFoundError,
    MetadataStorage,
    StorageError,
    StoredDocument,
    FileSystemMetadataStorage,
    StoreApiMetadataStorage,
    get_metadata_storage,
)

__all__ = [
    "AlternateIdentifierL1",
    "Level1Metadata",
    "MetadataSchemaType",
    "OriginalMetadataRef",
    "MetadataService",
    "FORMAT_TO_CONTENT_TYPE",
    "MetadataNotFoundError",
    "MetadataStorage",
    "StorageError",
    "StoredDocument",
    "FileSystemMetadataStorage",
    "StoreApiMetadataStorage",
    "get_metadata_storage",
]
