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

    def get_count(self) -> int:
        """Get the total number of ARKs registered on the blockchain."""
        return self.contract.functions.get_ark_count().call()

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Get the most recent ARKs registered on the blockchain."""
        latest_block = self.w3.eth.block_number
        chunk_size = 10000
        events = []
        
        current_to_block = latest_block
        
        while current_to_block >= 0 and len(events) < limit:
            current_from_block = max(0, current_to_block - chunk_size)
            try:
                chunk_events = self.contract.events.ARKCreated.get_logs(
                    fromBlock=current_from_block, 
                    toBlock=current_to_block
                )
                events = chunk_events + events
            except Exception:
                # If chunking still fails, break to avoid infinite loop
                break
            
            # Move backwards
            current_to_block = current_from_block - 1
            
        recent_events = events[-limit:] if events else []
        
        result = []
        for event in recent_events:
            args = event.get('args', {})
            result.append({
                "pid": f"ark:/{args.get('naan')}/{args.get('name')}",
                "naan": args.get("naan"),
                "name": args.get("name"),
                "owner": args.get("owner"),
                "url": args.get("url"),
                "cid": args.get("cid"),
            })
            
        return result[::-1]
