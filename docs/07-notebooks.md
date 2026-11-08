# Notebooks

## Available in this project

- `notebooks/dark_core_lib_e2e_demo.ipynb`
  - Full demo: authority setup, ARK creation/update/resolution.
- `notebooks/dark_core_lib_read_only_demo.ipynb`
  - Read-only demo for queries and resolution.

## Recommended use

1. Run from the root directory of `dark-core-lib`.
2. Have `../.env.integration` or `../.env` available.
3. Check beforehand that the network and contracts are deployed.
4. For a complete HTTP flow across Admin, Minter and Resolver, use the end-to-end
   notebook in the dark-deployer repository (`notebooks/`).

## What was adapted

- Imports and client moved to the unified API.
- Environment loading gives priority to `.env.integration`.
- References to the old API were removed.
