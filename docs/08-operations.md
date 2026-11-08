# Operational notes

## Checklist for a healthy local environment

1. RPC reachable at `DARK_RPC_URL`.
2. `DARK_CHAIN_ID` aligned with the active chain.
3. Bytecode present at:
   - `DARK_CONTRACT_ADDRESS`
   - `DARK_AUTHORITY_ADDRESS` (write mode)
4. A valid admin key for the Authority contract.

## Useful quick checks

- Connectivity:
  - `client.is_connected()`
- Chain:
  - `client.get_block_number()`
- Admin balance (write mode):
  - `client.get_admin_balance()`

## Symptoms and diagnosis

- Chain error:
  - `Chain ID mismatch`
  - Action: check `DARK_CHAIN_ID` or temporarily disable validation.
- Contract error:
  - `Could not transact with/call contract function`
  - Action: check addresses and deployment.
- Mode error:
  - `ReadOnlyModeError`
  - Action: initialize the client with `read_only=False`.

## Operating recommendations

1. Keep `.env.integration` in sync with the latest deployment.
2. Avoid hardcoding addresses in code.
3. Run the E2E integration before changing the ABI or configuration.
