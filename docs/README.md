# dark-core-lib documentation

Technical documentation of `dark-core-lib`, the unified Python SDK for dARK 2.0.
Start with the [README](../README.md) for installation and a quick start.

## Index

- [Overview](./01-overview.md): purpose, modes, main components.
- [Architecture](./02-architecture.md): logical map, initialization, authority and ARK flows, shared metadata.
- [API and wrappers](./03-api-and-wrappers.md): client, wrappers, services, metadata helpers, exceptions.
- [Configuration and environments](./04-configuration.md): environment variables, ABI overrides, good practices.
- [Testing and end-to-end integration](./05-testing.md): unit and integration commands, skip rules.
- [Migration guide](./06-migration.md): moving from separate read/write libraries.
- [Migration from Orchestrator and Observer](./09-migrate-from-orchestrator-observer.md): detailed before/after mapping.
- [Notebooks](./07-notebooks.md): available notebooks.
- [Operational notes](./08-operations.md): health checklist and diagnosis.
- [ADR 0001](./adr/0001-dark-core-lib.md): decision to create a unified SDK.

## Scope

These documents are based on the analysis of the earlier read and write libraries,
the current `dark-core-lib` implementation, and local validation with unit and
end-to-end integration tests.

## Platform context

`dark-core-lib` is used by the Minter, Admin and Resolver APIs for all blockchain
and metadata access. See the dark-deployer
[architecture](https://github.com/LA-Referencia-IOI/dark-deployer/blob/main/docs/architecture.md)
and [SDK guide](https://github.com/LA-Referencia-IOI/dark-deployer/blob/main/docs/sdk-guide.md).
