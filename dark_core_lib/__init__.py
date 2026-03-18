"""dark-core-lib public API."""

from dark_core_lib.client import DARKCoreClient
from dark_core_lib.config import CoreConfig
from dark_core_lib.models import ARKInfo, AuthorityInfo, TxReceiptInfo
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
    "DARKCoreClient",
    "CoreConfig",
    "ARKInfo",
    "AuthorityInfo",
    "TxReceiptInfo",
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
