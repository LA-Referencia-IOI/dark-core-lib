# Overview

`dark-core-lib` is a unified Python SDK for dARK 2.0. It combines:

- read operations on ARKs;
- write and administration operations for authorities and ARKs;
- shared metadata models and storage helpers used by the HTTP services.

## Goal

One library, in its own directory, with no runtime dependency on the earlier
separate read/write libraries.

## Modes

- `read_only=True`
  - Queries only.
  - No administrative key required.
- `read_only=False`
  - Queries plus signed transactions.
  - Requires the Authority contract address and the administrative key.

## Main components

- Main client: `DARKCoreClient`
- Services:
  - `AuthorityService`
  - `ARKService`
  - `ChainService`
- Support:
  - Configuration (`CoreConfig`)
  - Models (`AuthorityInfo`, `ARKInfo`, `TxReceiptInfo`)
  - AES-GCM encryption of authority keys
  - Embedded contract ABIs
  - Shared metadata (`Level1Metadata`, `MetadataService`, storage backends)
