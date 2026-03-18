"""Transaction helpers for write operations."""

from dark_core_lib.exceptions import TransactionError
from dark_core_lib.models import TxReceiptInfo


def _get_signed_raw_tx(signed) -> bytes:
    """Return raw signed tx bytes for old/new eth-account objects."""
    raw = getattr(signed, "raw_transaction", None)
    if raw is not None:
        return raw

    raw = getattr(signed, "rawTransaction", None)
    if raw is not None:
        return raw

    raise TransactionError("Signed transaction object has no raw transaction bytes")


def send_contract_tx(w3, contract_func, account, gas_limit: int, timeout_seconds: int) -> TxReceiptInfo:
    """Build, sign, send and confirm a transaction against a contract."""
    try:
        tx = contract_func.build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gas": gas_limit,
                "gasPrice": w3.eth.gas_price,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, account.key)
        tx_hash = w3.eth.send_raw_transaction(_get_signed_raw_tx(signed))
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout_seconds)

        tx_hash_hex = tx_hash.hex()
        if receipt.get("status") == 0:
            raise TransactionError(
                "Transaction reverted",
                tx_hash=tx_hash_hex,
                gas_used=receipt.get("gasUsed"),
            )

        return TxReceiptInfo(
            tx_hash=tx_hash_hex,
            status=receipt.get("status", 0),
            gas_used=receipt.get("gasUsed"),
            block_number=receipt.get("blockNumber"),
        )
    except TransactionError:
        raise
    except Exception as exc:
        raise TransactionError(f"Transaction failed: {exc}") from exc


def send_native_transfer(w3, sender_account, to_address: str, amount_wei: int, timeout_seconds: int) -> TxReceiptInfo:
    """Send native token transfer (ETH) from sender to recipient."""
    try:
        tx = {
            "from": sender_account.address,
            "to": to_address,
            "value": amount_wei,
            "nonce": w3.eth.get_transaction_count(sender_account.address),
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
        }

        signed = w3.eth.account.sign_transaction(tx, sender_account.key)
        tx_hash = w3.eth.send_raw_transaction(_get_signed_raw_tx(signed))
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout_seconds)

        tx_hash_hex = tx_hash.hex()
        if receipt.get("status") == 0:
            raise TransactionError(
                "Transfer transaction reverted",
                tx_hash=tx_hash_hex,
                gas_used=receipt.get("gasUsed"),
            )

        return TxReceiptInfo(
            tx_hash=tx_hash_hex,
            status=receipt.get("status", 0),
            gas_used=receipt.get("gasUsed"),
            block_number=receipt.get("blockNumber"),
        )
    except TransactionError:
        raise
    except Exception as exc:
        raise TransactionError(f"Transfer failed: {exc}") from exc
