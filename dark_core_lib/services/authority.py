"""Authority service for registration and authorization flows."""

from eth_account import Account

from dark_core_lib.crypto import encrypt_private_key, decrypt_private_key
from dark_core_lib.exceptions import (
    ReadOnlyModeError,
    AuthorityNotFoundError,
    AuthorityAlreadyExistsError,
    AuthorityError,
    AuthorizationError,
)
from dark_core_lib.models import AuthorityInfo, TxReceiptInfo
from dark_core_lib.services.tx import send_contract_tx, send_native_transfer


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class AuthorityService:
    """Manage authority contract operations and authority wallets."""

    def __init__(self, w3, contract, config, admin_account=None):
        self.w3 = w3
        self.contract = contract
        self.config = config
        self.admin_account = admin_account

    def _ensure_write_mode(self) -> None:
        if self.config.read_only:
            raise ReadOnlyModeError("This operation requires write mode")
        if self.admin_account is None:
            raise ReadOnlyModeError("Admin account is not configured")

    def get(self, uuid: str) -> AuthorityInfo:
        """Get authority info by UUID."""
        try:
            wallet_address, naans, active = self.contract.functions.get_authority(uuid).call()
            if wallet_address == ZERO_ADDRESS:
                raise AuthorityNotFoundError(f"Authority not found: {uuid}")
            return AuthorityInfo(
                uuid=uuid,
                wallet_address=wallet_address,
                naans=list(naans),
                active=active,
            )
        except AuthorityNotFoundError:
            raise
        except Exception as exc:
            if "Authority not found" in str(exc):
                raise AuthorityNotFoundError(f"Authority not found: {uuid}") from exc
            raise AuthorityError(f"Failed to get authority: {exc}") from exc

    def get_by_wallet(self, wallet_address: str) -> AuthorityInfo:
        """Get authority info by wallet address."""
        try:
            uuid = self.contract.functions.get_uuid_by_wallet(wallet_address).call()
        except Exception as exc:
            raise AuthorityError(f"Failed to get UUID by wallet: {exc}") from exc

        if not uuid:
            raise AuthorityNotFoundError(f"Wallet not registered: {wallet_address}")

        return self.get(uuid)

    def get_authorized_naans(self, uuid: str) -> list[str]:
        """Get all authorized NAANs for an authority."""
        return self.get(uuid).naans

    def is_authorized_for_naan(self, uuid: str, naan: str) -> bool:
        """Check NAAN authorization for an authority UUID."""
        try:
            authority = self.get(uuid)
            return self.contract.functions.is_authorized(authority.wallet_address, naan).call()
        except AuthorityNotFoundError:
            return False

    def get_authority_key(self, uuid: str) -> str:
        """Get encrypted private key stored on-chain for an authority."""
        self._ensure_write_mode()
        try:
            return self.contract.functions.get_authority_key(uuid).call({"from": self.admin_account.address})
        except Exception as exc:
            if "Authority not found" in str(exc):
                raise AuthorityNotFoundError(f"Authority not found: {uuid}") from exc
            raise AuthorityError(f"Failed to get authority key: {exc}") from exc

    def get_signing_credentials(self, uuid: str) -> tuple[str, str]:
        """Get authority wallet address and decrypted private key."""
        self._ensure_write_mode()
        authority = self.get(uuid)
        encrypted_key = self.get_authority_key(uuid)
        private_key = decrypt_private_key(encrypted_key, self.config.admin_private_key)
        return authority.wallet_address, private_key

    def authorize_naan(self, uuid: str, naan: str) -> TxReceiptInfo:
        """Authorize one NAAN for a registered authority."""
        self._ensure_write_mode()
        wallet_address, private_key = self.get_signing_credentials(uuid)
        return self._authorize_naan_with_key(wallet_address, private_key, naan)

    def authorize_naans(self, uuid: str, naans: list[str]) -> list[TxReceiptInfo]:
        """Authorize multiple NAANs for an authority."""
        self._ensure_write_mode()
        wallet_address, private_key = self.get_signing_credentials(uuid)
        results = []
        for naan in naans:
            results.append(self._authorize_naan_with_key(wallet_address, private_key, naan))
        return results

    def _authorize_naan_with_key(self, wallet_address: str, private_key: str, naan: str) -> TxReceiptInfo:
        if self.contract.functions.is_authorized(wallet_address, naan).call():
            return TxReceiptInfo(tx_hash="", status=1, gas_used=None, block_number=None)

        if not self.contract.functions.is_active_authority(wallet_address).call():
            raise AuthorizationError(f"Wallet {wallet_address} is not an active authority")

        account = self.w3.eth.account.from_key(private_key)
        return send_contract_tx(
            self.w3,
            self.contract.functions.authorize_naan(naan),
            account,
            gas_limit=self.config.default_gas_limit,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

    def setup(self, uuid: str, naans: list[str], fund_amount_wei: int = None) -> AuthorityInfo:
        """Create wallet, fund it, register authority and authorize NAANs."""
        self._ensure_write_mode()

        try:
            existing = self.get(uuid)
            raise AuthorityAlreadyExistsError(
                f"Authority with UUID '{uuid}' already exists at wallet {existing.wallet_address}"
            )
        except AuthorityNotFoundError:
            pass

        account = Account.create()
        wallet_address = account.address
        private_key = account.key.hex()
        encrypted_key = encrypt_private_key(private_key, self.config.admin_private_key)

        if fund_amount_wei is None:
            fund_amount_wei = self.w3.to_wei(0.01, "ether")

        send_native_transfer(
            self.w3,
            sender_account=self.admin_account,
            to_address=wallet_address,
            amount_wei=fund_amount_wei,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

        send_contract_tx(
            self.w3,
            self.contract.functions.register_authority(uuid, wallet_address, encrypted_key),
            self.admin_account,
            gas_limit=self.config.default_gas_limit,
            timeout_seconds=self.config.tx_timeout_seconds,
        )

        if not self.contract.functions.is_active_authority(wallet_address).call():
            raise AuthorityError(f"Authority registration verification failed for wallet {wallet_address}")

        for naan in naans:
            self._authorize_naan_with_key(wallet_address, private_key, naan)

        return self.get(uuid)

    def get_wallet_balance(self, uuid: str):
        """Get authority wallet balance in ETH."""
        try:
            authority = self.get(uuid)
            balance_wei = self.w3.eth.get_balance(authority.wallet_address)
            return float(self.w3.from_wei(balance_wei, "ether"))
        except AuthorityNotFoundError:
            return None
