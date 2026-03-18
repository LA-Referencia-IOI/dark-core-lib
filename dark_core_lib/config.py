"""Configuration model for dark-core-lib."""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

from dark_core_lib.abi import AUTHORITY_ABI, DARK_ABI
from dark_core_lib.exceptions import ConfigurationError


def _parse_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class CoreConfig:
    """Unified configuration for read and write operations."""

    rpc_url: str
    dark_contract_address: str
    chain_id: Optional[int] = None
    authority_contract_address: Optional[str] = None
    admin_private_key: Optional[str] = None
    read_only: bool = False
    validate_chain_id: bool = True
    default_gas_limit: int = 500000
    tx_timeout_seconds: int = 120
    dark_abi: list = field(default_factory=lambda: DARK_ABI)
    authority_abi: list = field(default_factory=lambda: AUTHORITY_ABI)

    @classmethod
    def from_env(
        cls,
        env_path: Optional[str] = None,
        read_only: Optional[bool] = None,
    ) -> "CoreConfig":
        """Build CoreConfig from environment variables."""
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        env_read_only = _parse_bool(os.getenv("DARK_READ_ONLY"), True)
        resolved_read_only = env_read_only if read_only is None else read_only

        chain_id_raw = os.getenv("DARK_CHAIN_ID")
        chain_id = int(chain_id_raw) if chain_id_raw else None

        gas_limit_raw = os.getenv("DARK_GAS_LIMIT")
        tx_timeout_raw = os.getenv("DARK_TX_TIMEOUT_SECONDS")

        config = cls(
            rpc_url=(os.getenv("DARK_RPC_URL") or "").strip(),
            dark_contract_address=(os.getenv("DARK_CONTRACT_ADDRESS") or "").strip(),
            chain_id=chain_id,
            authority_contract_address=(os.getenv("DARK_AUTHORITY_ADDRESS") or "").strip() or None,
            admin_private_key=(os.getenv("DARK_ADMIN_PRIVATE_KEY") or "").strip() or None,
            read_only=resolved_read_only,
            validate_chain_id=_parse_bool(os.getenv("DARK_VALIDATE_CHAIN_ID"), True),
            default_gas_limit=int(gas_limit_raw) if gas_limit_raw else 500000,
            tx_timeout_seconds=int(tx_timeout_raw) if tx_timeout_raw else 120,
        )

        config.validate()
        return config

    def validate(self) -> None:
        """Validate configuration according to operation mode."""
        missing = []
        if not self.rpc_url:
            missing.append("DARK_RPC_URL")
        if not self.dark_contract_address:
            missing.append("DARK_CONTRACT_ADDRESS")

        if not self.read_only:
            if not self.authority_contract_address:
                missing.append("DARK_AUTHORITY_ADDRESS")
            if not self.admin_private_key:
                missing.append("DARK_ADMIN_PRIVATE_KEY")

        if missing:
            raise ConfigurationError(f"Missing required environment variables: {', '.join(missing)}")

        if not self.rpc_url.startswith(("http://", "https://")):
            raise ConfigurationError(f"Invalid RPC URL: {self.rpc_url}")

        if not self.dark_contract_address.startswith("0x") or len(self.dark_contract_address) != 42:
            raise ConfigurationError(f"Invalid dARK address: {self.dark_contract_address}")

        if self.authority_contract_address:
            if not self.authority_contract_address.startswith("0x") or len(self.authority_contract_address) != 42:
                raise ConfigurationError(f"Invalid authority address: {self.authority_contract_address}")

        if self.admin_private_key:
            if not self.admin_private_key.startswith("0x") or len(self.admin_private_key) != 66:
                raise ConfigurationError("Invalid admin private key format")

        if self.default_gas_limit <= 0:
            raise ConfigurationError("DARK_GAS_LIMIT must be > 0")

        if self.tx_timeout_seconds <= 0:
            raise ConfigurationError("DARK_TX_TIMEOUT_SECONDS must be > 0")
