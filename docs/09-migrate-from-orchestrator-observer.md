# Migrating from Orchestrator and Observer to dark-core-lib

This document describes a practical migration from the two-library scheme (one for write/admin and one for read) to `dark-core-lib`.

## Goal

- Unify imports and client.
- Keep functional compatibility.
- Reduce risk with an incremental migration.

## 1. Import change

Before:

```python
from dark_orchestrator import DARKOrchestrator
from dark_observer import DARKObserver
```

After:

```python
from dark_core_lib import DARKCoreClient
```

## 2. Initialization

Before:

```python
orchestrator = DARKOrchestrator()
observer = DARKObserver()
```

After (two options):

```python
# Single client with write + read
client = DARKCoreClient.from_env(read_only=False)
```

```python
# Read-only client (equivalent to observer)
ro_client = DARKCoreClient.from_env(read_only=True)
```

## 3. API equivalences

### Authority operations

| Before | After (wrapper) | After (service) |
|---|---|---|
| `orchestrator.setup_authority(uuid, naans)` | `client.setup_authority(uuid, naans)` | `client.authorities.setup(uuid, naans)` |
| `orchestrator.get_authority_by_uuid(uuid)` | `client.get_authority_by_uuid(uuid)` | `client.authorities.get(uuid)` |
| `orchestrator.get_authority_by_wallet(addr)` | `client.get_authority_by_wallet(addr)` | `client.authorities.get_by_wallet(addr)` |
| `orchestrator.get_authorized_naans(uuid)` | `client.get_authorized_naans(uuid)` | `client.authorities.get_authorized_naans(uuid)` |
| `orchestrator.is_authorized_for_naan(uuid, naan)` | `client.is_authorized_for_naan(uuid, naan)` | `client.authorities.is_authorized_for_naan(uuid, naan)` |
| `orchestrator.get_wallet_balance(uuid)` | `client.get_wallet_balance(uuid)` | `client.authorities.get_wallet_balance(uuid)` |

### ARK operations

| Before | After (wrapper) | After (service) |
|---|---|---|
| `orchestrator.create_ark(...)` | `client.create_ark(...)` | `client.arks.create(...)` |
| `orchestrator.update_ark(...)` | `client.update_ark(...)` | `client.arks.update(...)` |
| `orchestrator.resolve_ark(naan, name)` | `client.resolve_ark(naan, name)` | `client.arks.resolve(naan, name)` |
| `orchestrator.get_ark(naan, name)` | `client.get_ark(naan, name)` | `client.arks.get(naan, name)` |
| `orchestrator.ark_exists(naan, name)` | `client.ark_exists(naan, name)` | `client.arks.exists(naan, name)` |
| `observer.resolve(naan, name)` | `ro_client.resolve_ark(naan, name)` | `ro_client.arks.resolve(naan, name)` |
| `observer.get_ark(naan, name)` | `ro_client.get_ark(naan, name)` | `ro_client.arks.get(naan, name)` |
| `observer.ark_exists(naan, name)` | `ro_client.ark_exists(naan, name)` | `ro_client.arks.exists(naan, name)` |

### Utilities

| Before | After |
|---|---|
| `orchestrator.get_block_number()` | `client.get_block_number()` |
| `observer.get_block_number()` | `ro_client.get_block_number()` |
| `orchestrator.is_connected()` | `client.is_connected()` |
| `observer.is_connected()` | `ro_client.is_connected()` |
| `orchestrator.get_admin_balance()` | `client.get_admin_balance()` |

## 4. Configuration

### Minimum read variables

- `DARK_RPC_URL`
- `DARK_CONTRACT_ADDRESS`

### Additional write variables

- `DARK_AUTHORITY_ADDRESS`
- `DARK_ADMIN_PRIVATE_KEY`

### Recommended

- `DARK_CHAIN_ID`
- `DARK_VALIDATE_CHAIN_ID=True`

## 5. Phased migration plan

1. **Phase 1 - Single import**
   - Replace imports with `DARKCoreClient`.
2. **Phase 2 - Controlled dual mode**
   - Reads with `read_only=True`.
   - Writes with `read_only=False`.
3. **Phase 3 - Wrappers first**
   - Migrate calls using wrappers to change as little as possible.
4. **Phase 4 - Internal services**
   - Gradually refactor to `client.authorities` and `client.arks` in new modules.
5. **Phase 5 - End to end**
   - Run unit + integration tests before removing the old code.

## 6. Complete example (before/after)

Before:

```python
from dark_orchestrator import DARKOrchestrator
from dark_observer import DARKObserver

orchestrator = DARKOrchestrator()
observer = DARKObserver()

auth = orchestrator.setup_authority("org-1", ["12345"])
ark = orchestrator.create_ark("org-1", "12345", "doc-1", "https://x", "Qm...")
url = observer.resolve("12345", "doc-1")
```

After:

```python
from dark_core_lib import DARKCoreClient

client = DARKCoreClient.from_env(read_only=False)
ro_client = DARKCoreClient.from_env(read_only=True)

auth = client.setup_authority("org-1", ["12345"])
ark = client.create_ark("org-1", "12345", "doc-1", "https://x", "Qm...")
url = ro_client.resolve_ark("12345", "doc-1")
```

`client.create_ark(...)` and `client.update_ark(...)` still return `ARKInfo` by default. They no longer perform a pre-write `exists()` read; the contract itself is the source of truth for duplicate or missing ARKs. Use `fetch_result=False` only for internal worker-style paths that do not need the resulting ARK data.

For worker pipelines, use `client.publish_ark_operations(...)` with operations for one authority UUID. It sends individual create/update transactions with sequential pending nonces and returns semantic per-ARK results without exposing transaction hashes.

## 7. Risks and mitigations

- `Chain ID mismatch`:
  - Align `DARK_CHAIN_ID` with the active network.
- Contracts without bytecode:
  - Check the deployed addresses before running integration.
- Writing in read mode:
  - Use a `read_only=False` client for transactions.

## 8. Post-migration validation

```bash
python3 -m pytest -q

DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q -m integration tests/integration/test_e2e.py
```
