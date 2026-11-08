# dark-core-lib

Unified Python SDK to interact with dARK 2.0 on the blockchain.

This package gathers into one API:

- Read operations: resolve ARKs, check existence and retrieve on-chain state
- Write/administration operations: register authorities, authorize NAANs, create and update ARKs
- Shared metadata models and utilities: L1/L2 schemas, storage backends and `MetadataService`

## Summary

`dark-core-lib` offers a high-level layer over the smart contracts to work with ARK persistent identifiers.

It supports two modes of operation:

- `read_only=True`: queries only (no admin key required)
- `read_only=False`: queries + signed transactions (requires the authority configuration and the admin key)

## Architecture

```text
DARKCoreClient
├── Chain service       (connectivity and network state)
├── ARK service         (resolve, exists, get, create, update)
├── Authority service   (setup, NAAN authorization, authority queries)
└── Metadata helpers    (schemas, storage, MetadataService)

On-chain contracts:
- Authority contract (registry, NAANs, encrypted keys)
- dARK contract (ARK storage and resolution)
```

## Installation

```bash
cd dark-core-lib
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

With development dependencies:

```bash
pip install -e ".[dev]"
```

## Configuration

Start from `.env.example`, or use `.env.integration` for E2E tests.

### Variables required in every mode

- `DARK_RPC_URL`
- `DARK_CONTRACT_ADDRESS`

### Recommended

- `DARK_CHAIN_ID`
- `DARK_VALIDATE_CHAIN_ID` (`True`/`False`)

### Required only in write mode

- `DARK_AUTHORITY_ADDRESS`
- `DARK_ADMIN_PRIVATE_KEY`

### Optional

- `DARK_READ_ONLY`
- `DARK_GAS_LIMIT`
- `DARK_TX_TIMEOUT_SECONDS`

### ABI overrides

- `DARK_ABI_JSON`
- `AUTHORITY_ABI_JSON`

Optional JSON overrides for the bundled contract ABIs. When set, `CoreConfig.from_env()` parses the value with `json.loads` and uses it as the ABI for the dARK contract (`DARK_ABI_JSON`) or the Authority contract (`AUTHORITY_ABI_JSON`); if the value is not valid JSON, the library silently falls back to the bundled `DARK_ABI` / `AUTHORITY_ABI` constants in `dark_core_lib/abi.py`. When unset, the bundled ABIs are used so the library works standalone.

Example:

```env
DARK_RPC_URL=http://localhost:8545
DARK_CHAIN_ID=2025
DARK_CONTRACT_ADDRESS=0x...
DARK_AUTHORITY_ADDRESS=0x...
DARK_ADMIN_PRIVATE_KEY=0x...
DARK_READ_ONLY=False
DARK_VALIDATE_CHAIN_ID=True
DARK_GAS_LIMIT=550000
DARK_TX_TIMEOUT_SECONDS=120
```

## Quick start

### Read mode

```python
from dark_core_lib import DARKCoreClient

client = DARKCoreClient.from_env(read_only=True)

print(client.is_connected())
print(client.get_block_number())

exists = client.ark_exists("12345", "document-001")
if exists:
    url = client.resolve_ark("12345", "document-001")
    info = client.get_ark("12345", "document-001")
    print(url, info.cid)
```

### Shared metadata

```python
from dark_core_lib import MetadataService, get_metadata_storage

storage = get_metadata_storage(
    storage_type="filesystem",
    storage_path="./metadata_storage",
)
metadata = MetadataService(storage)

level1 = metadata.load_level1("internal-level1-cid")
level2 = metadata.load_level2(level1)

print(level1.title)
print(level2.content_type)
```

### Write mode

```python
from dark_core_lib import DARKCoreClient

client = DARKCoreClient.from_env(read_only=False)

authority = client.setup_authority("org-uuid-001", ["12345"])

ark = client.create_ark(
    "org-uuid-001",
    "12345",
    "document-001",
    "https://example.org/docs/1",
    "Qm...",
)

print(ark.ark_id)

updated = client.update_ark(
    "org-uuid-001",
    "12345",
    "document-001",
    "https://example.org/docs/1?v=2",
    "Qm...v2",
)

print(updated.url)
```

`create_ark()` and `update_ark()` are write calls. They submit the transaction, wait for confirmation, and return `ARKInfo` by default. They do not perform an automatic `exists()` read before the write. Worker-style callers that do not need the post-write read can pass `fetch_result=False`.

## Public API

### Main client

- `DARKCoreClient.from_env(env_path=None, read_only=None)`
- `is_connected()`
- `get_block_number()`
- `get_chain_capacity(max_page_size=20)`
- `get_admin_balance()`

### Authorities

Through client wrappers:

- `setup_authority(uuid, naans, fund_amount_wei=None)`
- `get_authority_by_uuid(uuid)`
- `get_authority_by_wallet(wallet_address)`
- `get_authorized_naans(uuid)`
- `is_authorized_for_naan(uuid, naan)`
- `get_wallet_balance(uuid)`

Through services:

- `client.authorities.setup(...)`
- `client.authorities.get(...)`
- `client.authorities.authorize_naan(...)`
- `client.authorities.authorize_naans(...)`

### ARKs

Through client wrappers:

- `create_ark(uuid, naan, name, url, cid, fetch_result=True)`
- `update_ark(uuid, naan, name, url, cid, fetch_result=True)`
- `publish_ark_operations(uuid, operations, pipeline_size=20)`
- `estimate_ark_operation_gas(uuid, operation)`
- `publish_ark_operation(uuid, operation, gas_limit, gas_estimate=None)`
- `resolve_ark(naan, name)`
- `resolve_ark_by_id(ark)`
- `get_ark(naan, name)`
- `get_ark_by_id(ark)`
- `ark_exists(naan, name)`
- `ark_exists_by_id(ark)`
- `get_ark_count()`
- `get_recent_arks(limit=10)`

Through services:

- `client.arks.create(...)`
- `client.arks.update(...)`
- `client.arks.publish_operations(...)`
- `client.arks.estimate_operation_gas(...)`
- `client.arks.publish_operation(...)`
- `client.arks.resolve(...)`
- `client.arks.get(...)`
- `client.arks.exists(...)`
- `client.arks.get_count()`
- `client.arks.get_recent(limit, max_lookback_blocks=None)`

`create_ark` and `update_ark` return `ARKInfo` by default. With `fetch_result=False`, they return `None` after the transaction confirms and skip the post-write `get_ark()` read. Read methods return chain state and remain unchanged.

`get_ark_count()` returns the total number of ARKs registered on-chain, read from the contract counter. `get_recent_arks(limit=10)` walks `ARKCreated` logs backwards from the chain tip in 512-block windows and returns up to `limit` ARK dictionaries with `pid`, `naan`, `name`, `owner`, `url`, and `cid`, newest first. The scan stops as soon as `limit` events are collected or 100,000 blocks have been scanned (the default lookback; override with `max_lookback_blocks` in the service call), and it short-circuits to an empty list when the on-chain count is zero.

`publish_ark_operations` is the worker-oriented fast path. It accepts `ARKPublishOperation` items for one authority UUID, signs individual create/update transactions with sequential pending nonces, sends them in windows controlled by `pipeline_size`, waits for receipts, and returns `ARKPublishResult` values such as `confirmed`, `reverted`, `ambiguous`, `send_failed`, or `not_sent`. It does not expose transaction hashes to callers.

`estimate_ark_operation_gas` and `publish_ark_operation` are the single-operation rescue path used by the minter. They use the same semantic `ARKPublishOperation` shape, allow the caller to pass an explicit gas limit, and return semantic status plus gas metadata without exposing transaction hashes.

`get_chain_capacity` returns a semantic `ChainCapacityInfo` snapshot for worker pacing. It reads block progress and, when available, Besu txpool statistics through the core-lib web3 client, then recommends a temporary page size without exposing raw RPC details to callers.

### Shared metadata

- `parse_ark_id(raw)`
- `MetadataService(storage)`
- `get_metadata_storage(storage_type="store_api" | "filesystem", **kwargs)`
- `FileSystemMetadataStorage`
- `StoreApiMetadataStorage`
- `Level1Metadata`
- `OriginalMetadataRef`
- `StoredDocument`
- `ReplicationStatus`

#### Store API replication status

`StoreApiMetadataStorage` exposes the replication observation methods used by the minter's replication worker; the `MetadataStorage` base class provides working defaults for backends without replication:

- `get_replication_status(cid) -> ReplicationStatus` — live per-CID snapshot from Store API (`GET /v1/status/{cid}`); a 404 maps to `status="unpinned"` with `total_replicas=0`. The base-class default returns a synthetic single-copy `pinned` status.
- `get_replication_statuses(cids) -> dict[str, ReplicationStatus]` — batch snapshot via `POST /v1/status/batch`; the CID list is deduplicated and the result is keyed by CID.
- `ensure_replication(cids, target_replicas, assigned_replicas=None) -> dict[str, str]` — requests higher pin allocations via `POST /v1/replication/ensure` and returns one status string per CID; the base-class default returns `"unsupported"` per CID.

`ReplicationStatus` carries `cid`, `status`, `total_replicas`, `queued_replicas`, `pinning_replicas`, `error_replicas`, `assigned_replicas`, and `checked_at`.

## Models

- `AuthorityInfo`
  - `uuid`, `wallet_address`, `naans`, `active`
- `ARKInfo`
  - `naan`, `name`, `url`, `cid`, `owner`, `created_at`, `updated_at`, `ark_id`
- `TxReceiptInfo`
  - `tx_hash`, `status`, `gas_used`, `block_number`
- `Level1Metadata`
  - minimal public payload published by the Minter and consumed by the Resolver in `?info`
- `OriginalMetadataRef`
  - internal reference to L2 with `schema`, `media_type` and `cid`
- `StoredDocument`
  - `content`, `content_type`, `schema`
- `ReplicationStatus`
  - `cid`, `status`, `total_replicas`, `queued_replicas`, `pinning_replicas`, `error_replicas`, `assigned_replicas`, `checked_at`

## Error handling

Main exceptions:

- `DarkCoreError`
- `ConfigurationError`
- `ConnectionError`
- `ReadOnlyModeError`
- `TransactionError`
- `AuthorityError`, `AuthorityNotFoundError`, `AuthorityAlreadyExistsError`, `AuthorizationError`
- `ARKError`, `ARKNotFoundError`, `ARKAlreadyExistsError`

## Security

For authority operations, the private keys of authority wallets are encrypted with AES-256-GCM before being stored on-chain.

Recommendations:

- Use this library on private/permissioned networks
- Do not expose `DARK_ADMIN_PRIVATE_KEY`
- Avoid logs that contain secrets

## Notebooks

- End to end (authority setup + create/update/resolve ARK):
  - `notebooks/dark_core_lib_e2e_demo.ipynb`
- Read only (queries and resolution):
  - `notebooks/dark_core_lib_read_only_demo.ipynb`

## Testing

### Unit tests

```bash
python3 -m pytest -q
```

### E2E integration

```bash
DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q -m integration tests/integration/test_e2e.py
```

## Project structure

```text
dark-core-lib/
├── dark_core_lib/
│   ├── ark_id.py
│   ├── client.py
│   ├── config.py
│   ├── crypto.py
│   ├── models.py
│   ├── exceptions.py
│   ├── abi.py
│   ├── metadata/
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── storage/
│   └── services/
│       ├── authority.py
│       ├── ark.py
│       ├── chain.py
│       └── tx.py
├── notebooks/
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## License

AGPL-3.0-only. See `LICENSE` for details.

## Extended documentation

See the complete technical documentation in `docs/`:

- Index: `docs/README.md`
