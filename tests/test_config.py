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
