# Architecture

## Logical map

```text
DARKCoreClient
├── ChainService
├── ARKService
└── AuthorityService (when configured)

Separate library modules: MetadataService / storage helpers

Contracts:
- Authority: authority registry, NAANs, encrypted key
- dARK: create/update/get/resolve ARKs
```

## Initialization flow

1. `CoreConfig.from_env(...)` loads and validates variables.
2. A `Web3.HTTPProvider` connection is created.
3. The connection is checked and, optionally, the `chain_id`.
4. Contract instances are built:
   - dARK (always)
   - Authority (if configured)
5. Services and client wrappers are initialized.

## Authority flow (write mode)

1. Verify that the UUID does not exist.
2. Create the authority wallet.
3. Encrypt the private key with AES-256-GCM.
4. Fund the wallet from the admin account.
5. Register the authority in the contract.
6. Authorize the NAANs.
7. Return the consolidated state (`AuthorityInfo`).

## ARK flow

- Read:
  - `exists`, `resolve`, `get`
- Write:
  - `create` and `update` sign with the authority credentials and do **not** run a
    pre-write `exists()` check: the contract is the source of truth for duplicate
    or missing ARKs.
  - `publish_operations` pipelines many signed transactions with sequential
    pending nonces for one authority (see the
    [platform architecture](https://github.com/LA-Referencia-IOI/dark-deployer/blob/main/docs/platform-architecture.md)).

## Shared metadata

- `dark_core_lib.metadata.schemas`
  - defines `Level1Metadata` and the references to Level 2.
- `dark_core_lib.metadata.storage`
  - abstracts the `filesystem` and `store_api` backends.
- `dark_core_lib.metadata.service.MetadataService`
  - encapsulates the shared flow `L2 -> inject cid -> L1` and the load path `L1 -> L2`.

This layer publishes nothing over HTTP; `dark-core-minter-api` and
`dark-core-resolver-api` use it to keep the same metadata contract.

## Relevant decisions

- Client wrappers simplify use and compatibility.
- Separate services improve clarity and testability.
- `read_only` is an explicit guard against accidental writes.
- Bytecode/contract validation in integration tests avoids false negatives.
