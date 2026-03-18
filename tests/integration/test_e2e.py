import os
import uuid
from pathlib import Path

import pytest

from dark_core_lib import DARKCoreClient


def _enabled() -> bool:
    return os.getenv("DARK_CORE_LIB_RUN_INTEGRATION", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def _default_env_path() -> Path:
    # Repository root from: tests/integration/test_e2e.py
    repo_root = Path(__file__).resolve().parents[5]
    return repo_root / "components" / "orchestrator" / "dark-core-orchestrator" / ".env"


def _env_path() -> Path:
    raw = os.getenv("DARK_CORE_LIB_ENV_PATH", "").strip()
    return Path(raw) if raw else _default_env_path()


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def env_path() -> Path:
    if not _enabled():
        pytest.skip(
            "Integration tests are disabled. Set DARK_CORE_LIB_RUN_INTEGRATION=1 to run them."
        )

    path = _env_path()
    if not path.exists():
        pytest.skip(f"Integration .env file not found: {path}")

    return path


@pytest.fixture(scope="module")
def ro_client(env_path: Path) -> DARKCoreClient:
    try:
        client = DARKCoreClient.from_env(env_path=str(env_path), read_only=True)
    except Exception as exc:
        pytest.skip(f"Cannot initialize read-only client from {env_path}: {exc}")
    code = client.w3.eth.get_code(client.dark_contract.address)
    if not code:
        pytest.skip(
            f"No contract bytecode found at DARK_CONTRACT_ADDRESS {client.dark_contract.address}."
        )
    return client


@pytest.fixture(scope="module")
def rw_client(env_path: Path) -> DARKCoreClient:
    try:
        client = DARKCoreClient.from_env(env_path=str(env_path), read_only=False)
    except Exception as exc:
        pytest.skip(f"Cannot initialize read-write client from {env_path}: {exc}")
    dark_code = client.w3.eth.get_code(client.dark_contract.address)
    if not dark_code:
        pytest.skip(
            f"No contract bytecode found at DARK_CONTRACT_ADDRESS {client.dark_contract.address}."
        )
    authority_code = client.w3.eth.get_code(client.authority_contract.address)
    if not authority_code:
        pytest.skip(
            "No contract bytecode found at "
            f"DARK_AUTHORITY_ADDRESS {client.authority_contract.address}."
        )
    return client


def test_read_only_client_basics(ro_client: DARKCoreClient):
    assert ro_client.is_connected() is True
    assert isinstance(ro_client.get_block_number(), int)
    assert ro_client.get_block_number() >= 0

    # Query a random ARK to validate read-only path returns a boolean and does not crash.
    random_name = f"nonexistent-{uuid.uuid4().hex}"
    exists = ro_client.ark_exists("12345", random_name)
    assert isinstance(exists, bool)


def test_full_authority_and_ark_flow(rw_client: DARKCoreClient, ro_client: DARKCoreClient):
    suffix = uuid.uuid4().hex[:10]
    authority_uuid = f"it-org-{suffix}"
    naan = "12345"
    ark_name = f"it-doc-{suffix}"

    initial_url = f"https://integration.example.org/{suffix}/v1"
    updated_url = f"https://integration.example.org/{suffix}/v2"
    initial_cid = f"Qm{suffix}cidv1"
    updated_cid = f"Qm{suffix}cidv2"

    authority = rw_client.setup_authority(authority_uuid, [naan])
    assert authority.uuid == authority_uuid
    assert authority.active is True
    assert naan in authority.naans

    created = rw_client.create_ark(authority_uuid, naan, ark_name, initial_url, initial_cid)
    assert created.naan == naan
    assert created.name == ark_name
    assert created.url == initial_url
    assert created.cid == initial_cid

    resolved_after_create = rw_client.resolve_ark(naan, ark_name)
    assert resolved_after_create == initial_url

    updated = rw_client.update_ark(authority_uuid, naan, ark_name, updated_url, updated_cid)
    assert updated.url == updated_url
    assert updated.cid == updated_cid

    resolved_after_update = rw_client.resolve_ark(naan, ark_name)
    assert resolved_after_update == updated_url

    # Validate read-only client can resolve and fetch the same updated ARK.
    resolved_ro = ro_client.resolve_ark(naan, ark_name)
    assert resolved_ro == updated_url

    fetched_ro = ro_client.get_ark(naan, ark_name)
    assert fetched_ro.naan == naan
    assert fetched_ro.name == ark_name
    assert fetched_ro.url == updated_url
    assert fetched_ro.cid == updated_cid
