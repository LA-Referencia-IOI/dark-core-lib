"""ARK service for read and write operations."""

from datetime import datetime, timezone
from typing import Optional, Sequence

from dark_core_lib.exceptions import (
    ReadOnlyModeError,
    ARKError,
    ARKNotFoundError,
)
from dark_core_lib.models import ARKInfo, ARKPublishOperation, ARKPublishResult
from dark_core_lib.services.tx import _get_signed_raw_tx, send_contract_tx


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

    def create(
        self,
        uuid: str,
        naan: str,
        name: str,
        url: str,
        cid: str,
        fetch_result: bool = True,
    ) -> Optional[ARKInfo]:
        """Create a new ARK owned by an authority UUID."""
        self._ensure_write_mode()

        _, private_key = self.authority_service.get_signing_credentials(uuid)
        account = self.w3.eth.account.from_key(private_key)

        send_contract_tx(
            self.w3,
            self.contract.functions.create_ark(naan, name, url, cid),
            account,
            gas_limit=self.config.default_gas_limit,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

        if fetch_result:
            return self.get(naan, name)
        return None

    def update(
        self,
        uuid: str,
        naan: str,
        name: str,
        url: str,
        cid: str,
        fetch_result: bool = True,
    ) -> Optional[ARKInfo]:
        """Update an existing ARK using authority UUID credentials."""
        self._ensure_write_mode()

        _, private_key = self.authority_service.get_signing_credentials(uuid)
        account = self.w3.eth.account.from_key(private_key)

        send_contract_tx(
            self.w3,
            self.contract.functions.update_ark(naan, name, url, cid),
            account,
            gas_limit=self.config.default_gas_limit,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

        if fetch_result:
            return self.get(naan, name)
        return None

    def publish_operations(
        self,
        uuid: str,
        operations: Sequence[ARKPublishOperation],
        pipeline_size: int = 20,
    ) -> list[ARKPublishResult]:
        """Publish ARK create/update operations with sequential nonce pipelining."""
        self._ensure_write_mode()
        if pipeline_size <= 0:
            raise ValueError("pipeline_size must be > 0")
        if not operations:
            return []

        _, private_key = self.authority_service.get_signing_credentials(uuid)
        account = self.w3.eth.account.from_key(private_key)
        nonce = self.w3.eth.get_transaction_count(account.address, "pending")

        results: list[ARKPublishResult] = []
        stop_pipeline = False

        for start in range(0, len(operations), pipeline_size):
            window = list(operations[start : start + pipeline_size])
            if stop_pipeline:
                results.extend(
                    ARKPublishResult(
                        ref=operation.ref,
                        action=operation.action,
                        status="not_sent",
                        error="Skipped after an earlier pipeline uncertainty",
                    )
                    for operation in window
                )
                continue

            signed_items = []
            for operation in window:
                try:
                    contract_func = self._contract_func_for_operation(operation)
                    tx_payload = {
                        "from": account.address,
                        "nonce": nonce,
                        "gas": self.config.default_gas_limit,
                        "gasPrice": self.w3.eth.gas_price,
                    }
                    chain_id = getattr(self.config, "chain_id", None)
                    if chain_id is not None:
                        tx_payload["chainId"] = chain_id

                    tx = contract_func.build_transaction(tx_payload)
                    signed = self.w3.eth.account.sign_transaction(tx, account.key)
                    signed_items.append((operation, signed))
                    nonce += 1
                except Exception as exc:
                    for signed_operation, _ in signed_items:
                        results.append(
                            ARKPublishResult(
                                ref=signed_operation.ref,
                                action=signed_operation.action,
                                status="not_sent",
                                error="Skipped because window build/sign failed before send",
                            )
                        )
                    results.append(
                        ARKPublishResult(
                            ref=operation.ref,
                            action=operation.action,
                            status="send_failed",
                            error=f"Failed to build/sign transaction: {exc}",
                        )
                    )
                    self._append_not_sent(results, window, operation)
                    stop_pipeline = True
                    break

            if stop_pipeline:
                continue

            sent_items = []
            send_failure = None
            for index, (operation, signed) in enumerate(signed_items):
                try:
                    tx_hash = self.w3.eth.send_raw_transaction(_get_signed_raw_tx(signed))
                    sent_items.append((operation, tx_hash))
                except Exception as exc:
                    send_failure = (index, operation, exc)
                    stop_pipeline = True
                    break

            receipt_failed = False
            for index, (operation, tx_hash) in enumerate(sent_items):
                if receipt_failed:
                    results.append(
                        ARKPublishResult(
                            ref=operation.ref,
                            action=operation.action,
                            status="ambiguous",
                            error="Receipt not checked after earlier receipt uncertainty",
                        )
                    )
                    continue

                try:
                    receipt = self.w3.eth.wait_for_transaction_receipt(
                        tx_hash,
                        timeout=self.config.tx_timeout_seconds,
                    )
                except Exception as exc:
                    results.append(
                        ARKPublishResult(
                            ref=operation.ref,
                            action=operation.action,
                            status="ambiguous",
                            error=f"Failed waiting for receipt: {exc}",
                        )
                    )
                    receipt_failed = True
                    stop_pipeline = True
                    continue

                status = receipt.get("status", 0)
                if status == 1:
                    results.append(
                        ARKPublishResult(
                            ref=operation.ref,
                            action=operation.action,
                            status="confirmed",
                        )
                    )
                else:
                    results.append(
                        ARKPublishResult(
                            ref=operation.ref,
                            action=operation.action,
                            status="reverted",
                            error="Transaction reverted",
                        )
                    )

            if send_failure is not None:
                failed_index, failed_operation, exc = send_failure
                results.append(
                    ARKPublishResult(
                        ref=failed_operation.ref,
                        action=failed_operation.action,
                        status="send_failed",
                        error=f"Failed to send transaction: {exc}",
                    )
                )
                for not_sent_operation, _ in signed_items[failed_index + 1 :]:
                    results.append(
                        ARKPublishResult(
                            ref=not_sent_operation.ref,
                            action=not_sent_operation.action,
                            status="not_sent",
                            error="Skipped to avoid a nonce gap after send failure",
                        )
                    )

        return results

    def _contract_func_for_operation(self, operation: ARKPublishOperation):
        """Return the contract function for a semantic ARK operation."""
        if operation.action == "create":
            return self.contract.functions.create_ark(
                operation.naan,
                operation.name,
                operation.url,
                operation.cid,
            )
        if operation.action == "update":
            return self.contract.functions.update_ark(
                operation.naan,
                operation.name,
                operation.url,
                operation.cid,
            )
        raise ValueError(f"Unsupported ARK publish action: {operation.action}")

    def _append_not_sent(
        self,
        results: list[ARKPublishResult],
        window: list[ARKPublishOperation],
        failed_operation: ARKPublishOperation,
    ) -> None:
        """Mark remaining operations in a window as not sent after an early failure."""
        failed_seen = False
        for operation in window:
            if operation is failed_operation:
                failed_seen = True
                continue
            if failed_seen:
                results.append(
                    ARKPublishResult(
                        ref=operation.ref,
                        action=operation.action,
                        status="not_sent",
                        error="Skipped after an earlier pipeline failure",
                    )
                )

    def get_count(self) -> int:
        """Get the total number of ARKs registered on the blockchain."""
        return self.contract.functions.get_ark_count().call()

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Get the most recent ARKs registered on the blockchain."""
        latest_block = self.w3.eth.block_number
        chunk_size = 5000
        events = []
        
        current_to_block = latest_block
        
        while current_to_block >= 0 and len(events) < limit:
            current_from_block = max(0, current_to_block - chunk_size)
            try:
                chunk_events = self.contract.events.ARKCreated.get_logs(
                    fromBlock=current_from_block, 
                    toBlock=current_to_block
                )
                events = list(chunk_events) + events
            except Exception as e:
                import logging
                logging.error(f"Error fetching logs from {current_from_block} to {current_to_block}: {e}")
                if chunk_size > 1000:
                    chunk_size = 1000
                    continue
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
