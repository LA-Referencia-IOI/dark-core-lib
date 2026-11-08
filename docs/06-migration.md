# Migration guide

## Goal

Migrate from separate read/write code to a single API.

## Main changes

1. Single import:
   - New: `from dark_core_lib import DARKCoreClient`
2. Initialization:
   - New: `DARKCoreClient.from_env(read_only=True|False)`
3. Methods:
   - Wrappers are kept to minimize changes.
   - `create_ark` and `update_ark` still return `ARKInfo` by default. For fast
     internal paths use `fetch_result=False`.
   - For high-volume workers, `publish_ark_operations` sends individual
     create/update operations with consecutive nonces and returns one semantic
     result per ARK.
4. Configuration:
   - Unified `DARK_*` variable scheme.

## Quick mapping table

- `setup_authority` -> `setup_authority` (wrapper) or `client.authorities.setup`
- `create_ark` -> `create_ark` (wrapper) or `client.arks.create`
- `update_ark` -> `update_ark` (wrapper) or `client.arks.update`
- `resolve_ark` -> `resolve_ark` (wrapper) or `client.arks.resolve`
- `get_ark` -> `get_ark` (wrapper) or `client.arks.get`
- `ark_exists` -> `ark_exists` (wrapper) or `client.arks.exists`

## Suggested strategy

1. Change the import and initialization.
2. Keep wrappers for a quick migration.
3. Gradually move to the services (`client.authorities` / `client.arks`) in new code.
4. Run the E2E integration suite at each stage.

## Common risks

- `chain_id` misaligned between `.env` and the active network.
- Old contract addresses.
- An admin key that does not match the Authority contract.

Mitigation:

- Use an `.env.integration` generated from a real deployment.

See also the detailed
[Orchestrator and Observer migration](./09-migrate-from-orchestrator-observer.md).
