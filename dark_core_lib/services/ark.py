"""ARK service for read and write operations."""

from datetime import datetime, timezone

from dark_core_lib.exceptions import (
    ReadOnlyModeError,
    ARKError,
    ARKNotFoundError,
    ARKAlreadyExistsError,
)
from dark_core_lib.models import ARKInfo
from dark_core_lib.services.tx import send_contract_tx


class ARKService:
    """Manage dARK contract ARK operations."""

    def __init__(self, w3, contract, config, authority_service=None):
        self.w3 = w3
        self.contract = contract
        self.config = config
        self.authority_service = authority_service

    def _ensure_write_mode(self) -> None:
        if self.config.read_only:
            raise ReadOnlyModeError("This operation requires write mode")
        if self.authority_service is None:
            raise ReadOnlyModeError("Authority service is not configured")

    def resolve(self, naan: str, name: str) -> str:
        """Resolve ARK identifier to URL."""
        try:
            return self.contract.functions.resolve(naan, name).call()
        except Exception as exc:
            if "ARK not found" in str(exc):
                raise ARKNotFoundError(f"ARK not found: ark:/{naan}/{name}") from exc
            raise ARKError(f"Failed to resolve ARK: {exc}") from exc

    def exists(self, naan: str, name: str) -> bool:
        """Check if an ARK exists."""
        return self.contract.functions.ark_exists(naan, name).call()

    def get(self, naan: str, name: str) -> ARKInfo:
        """Get full ARK metadata."""
        try:
            result = self.contract.functions.get_ark(naan, name).call()
            ark_name, ark_naan, url, cid, owner, created_at, updated_at = result
            return ARKInfo(
                naan=ark_naan,
                name=ark_name,
                url=url,
                cid=cid,
                owner=owner,
                created_at=datetime.fromtimestamp(created_at, tz=timezone.utc),
                updated_at=datetime.fromtimestamp(updated_at, tz=timezone.utc),
            )
        except Exception as exc:
            if "ARK not found" in str(exc):
                raise ARKNotFoundError(f"ARK not found: ark:/{naan}/{name}") from exc
            raise ARKError(f"Failed to get ARK: {exc}") from exc

    def create(self, uuid: str, naan: str, name: str, url: str, cid: str) -> ARKInfo:
        """Create a new ARK owned by an authority UUID."""
        self._ensure_write_mode()
        if self.exists(naan, name):
            raise ARKAlreadyExistsError(f"ARK already exists: ark:/{naan}/{name}")

        _, private_key = self.authority_service.get_signing_credentials(uuid)
        account = self.w3.eth.account.from_key(private_key)

        send_contract_tx(
            self.w3,
            self.contract.functions.create_ark(naan, name, url, cid),
            account,
            gas_limit=self.config.default_gas_limit,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

        return self.get(naan, name)

    def update(self, uuid: str, naan: str, name: str, url: str, cid: str) -> ARKInfo:
        """Update an existing ARK using authority UUID credentials."""
        self._ensure_write_mode()
        if not self.exists(naan, name):
            raise ARKNotFoundError(f"ARK not found: ark:/{naan}/{name}")

        _, private_key = self.authority_service.get_signing_credentials(uuid)
        account = self.w3.eth.account.from_key(private_key)

        send_contract_tx(
            self.w3,
            self.contract.functions.update_ark(naan, name, url, cid),
            account,
            gas_limit=self.config.default_gas_limit,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

        return self.get(naan, name)
