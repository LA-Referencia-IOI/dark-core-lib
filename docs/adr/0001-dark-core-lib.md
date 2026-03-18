# ADR 0001: dark-core-lib as Unified SDK

## Status
Accepted

## Context
The current stack has two separate libraries:

- `dark-core-orchestrator` for write/admin operations
- `dark-observer-lib` for read-only operations

This split creates duplicated models/config and cross-package coupling.

## Decision
Create a standalone package named `dark-core-lib` in a separate directory.

`dark-core-lib` must:

- be independent from orchestrator/observer imports
- provide one unified client for read and write operations
- support `read_only` mode to safely disable writes
- expose a migration-friendly API (service-based + convenience wrappers)

## Consequences
Positive:

- one package to version and distribute
- no runtime dependency between old libraries
- simpler migration path and clearer ownership

Trade-offs:

- larger surface area in a single package
- stricter test coverage needed for both read and write paths
