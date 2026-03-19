"""Unified dark-core-lib client."""

from typing import Optional

from web3 import Web3

from dark_core_lib.config import CoreConfig
from dark_core_lib.exceptions import ConfigurationError, ConnectionError
from dark_core_lib.services import AuthorityService, ARKService, ChainService


class DARKCoreClient:
    """Unified dARK SDK client for read-only and read-write operations."""

    def __init__(self, config: Optional[CoreConfig] = None):
        self.config = config or CoreConfig.from_env()
        self.config.validate()

        self.w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {self.config.rpc_url}")

        if self.config.validate_chain_id and self.config.chain_id is not None:
            detected = self.w3.eth.chain_id
            if int(detected) != int(self.config.chain_id):
                raise ConnectionError(
                    f"Chain ID mismatch: expected {self.config.chain_id}, got {detected}"
                )

        self.admin_account = None
        if not self.config.read_only and self.config.admin_private_key:
            self.admin_account = self.w3.eth.account.from_key(self.config.admin_private_key)

        self.dark_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.config.dark_contract_address),
            abi=self.config.dark_abi,
        )

        self.authority_contract = None
        self.authorities = None
        if self.config.authority_contract_address:
            self.authority_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.config.authority_contract_address),
                abi=self.config.authority_abi,
            )
            self.authorities = AuthorityService(
                w3=self.w3,
                contract=self.authority_contract,
                config=self.config,
                admin_account=self.admin_account,
            )

        self.arks = ARKService(
            w3=self.w3,
            contract=self.dark_contract,
            config=self.config,
            authority_service=self.authorities,
        )
        self.chain = ChainService(self.w3, admin_account=self.admin_account)

    @classmethod
    def from_env(
        cls,
        env_path: Optional[str] = None,
        read_only: Optional[bool] = None,
    ) -> "DARKCoreClient":
        """Build client from environment values."""
        config = CoreConfig.from_env(env_path=env_path, read_only=read_only)
        return cls(config)

    def _require_authorities(self) -> AuthorityService:
        if self.authorities is None:
            raise ConfigurationError("Authority contract is not configured")
        return self.authorities

    # Backward-compatible convenience methods
    def setup_authority(self, uuid: str, naans: list[str], fund_amount_wei: int = None):
        return self._require_authorities().setup(uuid, naans, fund_amount_wei)

    def get_authority_by_uuid(self, uuid: str):
        return self._require_authorities().get(uuid)

    def get_authority_by_wallet(self, wallet_address: str):
        return self._require_authorities().get_by_wallet(wallet_address)

    def get_authorized_naans(self, uuid: str):
        return self._require_authorities().get_authorized_naans(uuid)

    def is_authorized_for_naan(self, uuid: str, naan: str):
        return self._require_authorities().is_authorized_for_naan(uuid, naan)

    def authorize_naan(self, uuid: str, naan: str):
        return self._require_authorities().authorize_naan(uuid, naan)

    def revoke_naan(self, uuid: str, naan: str):
        return self._require_authorities().revoke_naan(uuid, naan)

    def deactivate_authority(self, uuid: str):
        return self._require_authorities().deactivate(uuid)

    def fund_authority_wallet(self, uuid: str, amount_wei: int):
        return self._require_authorities().fund_wallet(uuid, amount_wei)

    def create_ark(self, uuid: str, naan: str, name: str, url: str, cid: str):
        return self.arks.create(uuid, naan, name, url, cid)

    def update_ark(self, uuid: str, naan: str, name: str, url: str, cid: str):
        return self.arks.update(uuid, naan, name, url, cid)

    def resolve_ark(self, naan: str, name: str):
        return self.arks.resolve(naan, name)

    def ark_exists(self, naan: str, name: str):
        return self.arks.exists(naan, name)

    def get_ark(self, naan: str, name: str):
        return self.arks.get(naan, name)

    def get_admin_balance(self):
        return self.chain.get_admin_balance()

    def get_wallet_balance(self, uuid: str):
        return self._require_authorities().get_wallet_balance(uuid)

    def get_block_number(self):
        return self.chain.get_block_number()

    def is_connected(self):
        return self.chain.is_connected()
