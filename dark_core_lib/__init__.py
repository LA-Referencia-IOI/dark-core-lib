"""dark-core-lib public API."""

from dark_core_lib.ark_id import ARKIdentifier, parse_ark_id
from dark_core_lib.client import DARKCoreClient
from dark_core_lib.config import CoreConfig
from dark_core_lib.metadata import (
    AlternateIdentifierL1,
    FileSystemMetadataStorage,
    Level1Metadata,
    MetadataService,
    MetadataNotFoundError,
    MetadataSchemaType,
    MetadataStorage,
    ReplicationStatus,
    OriginalMetadataRef,
    StorageError,
    StoreApiMetadataStorage,
    StoredDocument,
    get_metadata_storage,
)
from dark_core_lib.models import (
    ARKInfo,
    ARKPublishOperation,
    ARKPublishResult,
    AuthorityInfo,
    ChainCapacityInfo,
    TxReceiptInfo,
)
from dark_core_lib.exceptions import (
    DarkCoreError,
    ConfigurationError,
    ConnectionError,
    ReadOnlyModeError,
    TransactionError,
    AuthorityError,
    AuthorityNotFoundError,
    AuthorityAlreadyExistsError,
    AuthorizationError,
    ARKError,
    ARKNotFoundError,
    ARKAlreadyExistsError,
)

__version__ = "0.1.0"

__all__ = [
    "ARKIdentifier",
    "DARKCoreClient",
    "CoreConfig",
    "ARKInfo",
    "ARKPublishOperation",
    "ARKPublishResult",
    "AuthorityInfo",
    "ChainCapacityInfo",
    "TxReceiptInfo",
    "AlternateIdentifierL1",
    "Level1Metadata",
    "MetadataSchemaType",
    "MetadataService",
    "MetadataStorage",
    "ReplicationStatus",
    "OriginalMetadataRef",
    "StorageError",
    "MetadataNotFoundError",
    "StoredDocument",
    "FileSystemMetadataStorage",
    "StoreApiMetadataStorage",
    "get_metadata_storage",
    "parse_ark_id",
    "DarkCoreError",
    "ConfigurationError",
    "ConnectionError",
    "ReadOnlyModeError",
    "TransactionError",
    "AuthorityError",
    "AuthorityNotFoundError",
    "AuthorityAlreadyExistsError",
    "AuthorizationError",
    "ARKError",
    "ARKNotFoundError",
    "ARKAlreadyExistsError",
]
