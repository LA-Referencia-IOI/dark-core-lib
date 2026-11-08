# API and wrappers

## Main client

- `DARKCoreClient.from_env(env_path=None, read_only=None)`
- `is_connected()`
- `get_block_number()`
- `get_admin_balance()`

## What the wrappers are

Wrappers are shortcuts on `DARKCoreClient` that delegate to the internal services.

Examples:

- `client.setup_authority(...)` -> `client.authorities.setup(...)`
- `client.resolve_ark(...)` -> `client.arks.resolve(...)`

Advantages:

- A fast API for common use.
- A shorter learning curve.
- A smoother migration from earlier code.

## Authorities

Wrappers:

- `setup_authority(uuid, naans, fund_amount_wei=None)`
- `get_authority_by_uuid(uuid)`
- `get_authority_by_wallet(wallet_address)`
- `get_authorized_naans(uuid)`
- `is_authorized_for_naan(uuid, naan)`
- `get_wallet_balance(uuid)`

Equivalent services:

- `client.authorities.setup(...)`
- `client.authorities.get(...)`
- `client.authorities.get_by_wallet(...)`
- `client.authorities.authorize_naan(...)`
- `client.authorities.authorize_naans(...)`

## ARKs

Wrappers:

- `create_ark(uuid, naan, name, url, cid, fetch_result=True)`
- `update_ark(uuid, naan, name, url, cid, fetch_result=True)`
- `publish_ark_operations(uuid, operations, pipeline_size=20)`
- `resolve_ark(naan, name)`
- `resolve_ark_by_id(ark)`
- `get_ark(naan, name)`
- `get_ark_by_id(ark)`
- `ark_exists(naan, name)`
- `ark_exists_by_id(ark)`
- `get_ark_count()`
- `get_recent_arks(limit=10)`

Equivalent services:

- `client.arks.create(...)`
- `client.arks.update(...)`
- `client.arks.publish_operations(...)`
- `client.arks.resolve(...)`
- `client.arks.get(...)`
- `client.arks.exists(...)`
- `client.arks.get_count()`
- `client.arks.get_recent(limit, max_lookback_blocks=None)`

`create_ark` and `update_ark` do not run `exists()` before the write. They return `ARKInfo` by default after confirmation. Pass `fetch_result=False` for write-only paths that should skip the post-write `get()` read and return `None`.

`publish_ark_operations` is intended for services such as the minter worker. It receives semantic ARK create/update operations for one authority, pipelines individual signed transactions with sequential pending nonces, waits for receipts, and returns one semantic result per operation without exposing transaction hashes.

`get_ark_count()` returns the total number of ARKs registered on-chain, read from the contract counter. `get_recent_arks(limit=10)` walks `ARKCreated` logs backwards from the chain tip in 512-block windows and returns up to `limit` ARK dictionaries with `pid`, `naan`, `name`, `owner`, `url`, and `cid`, newest first. The scan stops as soon as `limit` events are collected or 100,000 blocks have been scanned (the default lookback; override with `max_lookback_blocks` in the service call), and it short-circuits to an empty list when the on-chain count is zero.

## Shared metadata

Not everything in `dark-core-lib` is a blockchain wrapper. The package also exposes shared pieces for the HTTP services:

- `parse_ark_id(raw)`
- `MetadataService(storage)`
- `get_metadata_storage(...)`
- `FileSystemMetadataStorage`
- `StoreApiMetadataStorage`
- `Level1Metadata`
- `OriginalMetadataRef`
- `StoredDocument`
- `ReplicationStatus`

Typical use:

- the Minter uses `MetadataService` to persist L2, inject the internal CID into L1 and store the final L1
- the Resolver uses `MetadataService` to load L1 from the on-chain CID and then retrieve L2 for `?metadata`

### Store API replication status

`StoreApiMetadataStorage` exposes the replication observation methods used by the minter's replication worker; the `MetadataStorage` base class provides working defaults for backends without replication:

- `get_replication_status(cid) -> ReplicationStatus` — live per-CID snapshot from Store API (`GET /v1/status/{cid}`); a 404 maps to `status="unpinned"` with `total_replicas=0`. The base-class default returns a synthetic single-copy `pinned` status.
- `get_replication_statuses(cids) -> dict[str, ReplicationStatus]` — batch snapshot via `POST /v1/status/batch`; the CID list is deduplicated and the result is keyed by CID.
- `ensure_replication(cids, target_replicas, assigned_replicas=None) -> dict[str, str]` — requests higher pin allocations via `POST /v1/replication/ensure` and returns one status string per CID; the base-class default returns `"unsupported"` per CID.

`ReplicationStatus` carries `cid`, `status`, `total_replicas`, `queued_replicas`, `pinning_replicas`, `error_replicas`, `assigned_replicas`, and `checked_at`.

## Frequently used exceptions

- `ReadOnlyModeError`: a write was attempted in read mode.
- `ConfigurationError`: missing or invalid configuration.
- `ConnectionError`: network problem or `chain_id` mismatch.
- `Authority*` and `ARK*`: contract domain errors.
- `TransactionError`: a reverted or failed transaction.
