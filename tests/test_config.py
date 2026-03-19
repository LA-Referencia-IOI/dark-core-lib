import pytest

from dark_core_lib.config import CoreConfig
from dark_core_lib.exceptions import ConfigurationError


def test_read_only_config_validation():
    cfg = CoreConfig(
        rpc_url="http://localhost:8545",
        dark_contract_address="0x" + "a" * 40,
        read_only=True,
    )
    cfg.validate()


def test_write_config_requires_admin_fields():
    cfg = CoreConfig(
        rpc_url="http://localhost:8545",
        dark_contract_address="0x" + "a" * 40,
        read_only=False,
    )

    try:
        cfg.validate()
        raise AssertionError("Expected ConfigurationError")
    except ConfigurationError:
        pass


def test_from_env_overrides_existing_process_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "DARK_RPC_URL=http://localhost:8545",
                f"DARK_CONTRACT_ADDRESS={'0x' + 'a' * 40}",
                f"DARK_AUTHORITY_ADDRESS={'0x' + 'b' * 40}",
                f"DARK_ADMIN_PRIVATE_KEY={'0x' + '2' * 64}",
                "DARK_READ_ONLY=False",
            ]
        )
    )

    monkeypatch.setenv("DARK_ADMIN_PRIVATE_KEY", "0x" + "1" * 64)

    cfg = CoreConfig.from_env(env_path=str(env_file), read_only=False)

    assert cfg.admin_private_key == "0x" + "2" * 64
