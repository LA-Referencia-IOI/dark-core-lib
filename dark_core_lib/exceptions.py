"""Custom exceptions for dark-core-lib."""


class DarkCoreError(Exception):
    """Base error for dark-core-lib."""


class ConfigurationError(DarkCoreError):
    """Raised on invalid/missing configuration."""


class ConnectionError(DarkCoreError):
    """Raised when blockchain connection fails."""


class ReadOnlyModeError(DarkCoreError):
    """Raised when a write operation is called in read-only mode."""


class TransactionError(DarkCoreError):
    """Raised when a blockchain transaction fails."""

    def __init__(
        self,
        message: str,
        tx_hash: str = None,
        gas_used: int = None,
        status: int = None,
        block_number: int = None,
    ):
        super().__init__(message)
        self.tx_hash = tx_hash
        self.gas_used = gas_used
        self.status = status
        self.block_number = block_number


class AuthorityError(DarkCoreError):
    """Raised on authority contract operations failures."""


class AuthorityNotFoundError(AuthorityError):
    """Raised when an authority is not found."""


class AuthorityAlreadyExistsError(AuthorityError):
    """Raised when attempting to create an already existing authority."""


class AuthorizationError(AuthorityError):
    """Raised when NAAN authorization fails."""


class ARKError(DarkCoreError):
    """Raised on dARK contract operations failures."""


class ARKNotFoundError(ARKError):
    """Raised when ARK is not found."""


class ARKAlreadyExistsError(ARKError):
    """Raised when ARK already exists."""
