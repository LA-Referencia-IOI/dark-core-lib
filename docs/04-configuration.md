# Configuration and environments

## Environment variables

### Always required

- `DARK_RPC_URL`
- `DARK_CONTRACT_ADDRESS`

### Required in write mode

- `DARK_AUTHORITY_ADDRESS`
- `DARK_ADMIN_PRIVATE_KEY`

### Recommended

- `DARK_CHAIN_ID`
- `DARK_VALIDATE_CHAIN_ID`

### Optional

| Variable | Default | Description |
| --- | --- | --- |
| `DARK_READ_ONLY` | `true` | Read mode by default; use `false` for signed operations |
| `DARK_GAS_LIMIT` | `550000` | Gas limit per write transaction; the Minter uses double only in rescue |
| `DARK_TX_TIMEOUT_SECONDS` | `120` | Maximum time waiting for a receipt |

In the current deployer, Admin API, Minter API and Minter workers receive the
same `administration-env` secret containing `DARK_ADMIN_PRIVATE_KEY`. It is the
contract-deployment signer and is used by the SDK both for administrative calls
and to derive the key that decrypts authority wallet credentials. Resolver does
not receive this secret. Treat access to it as administrative access. See the
[deployer repository](https://github.com/LA-Referencia-IOI/dark-deployer).

### ABI overrides

| Variable | Default | Description |
| --- | --- | --- |
| `DARK_ABI_JSON` | unset | Optional JSON override for the bundled dARK ABI (`DARK_ABI` in `dark_core_lib/abi.py`) |
| `AUTHORITY_ABI_JSON` | unset | Optional JSON override for the bundled Authority ABI (`AUTHORITY_ABI` in `dark_core_lib/abi.py`) |

Semantics in `CoreConfig.from_env()` (`dark_core_lib/config.py`):

- dotenv loading uses `override=True`: values in the selected file can override existing process environment values

- when the variable is set, its value is parsed with `json.loads` and used as the contract ABI
- if the value is not valid JSON, the library silently falls back to the bundled ABI, so a bad override never breaks startup
- when the variable is unset, the bundled ABI is used and the library works standalone

## Recommended files

- `.env.example`: base template
- `.env.integration`: real configuration for local E2E tests

## Good practices

1. Keep `DARK_VALIDATE_CHAIN_ID=True` by default.
2. Use `read_only=True` for dashboards and query processes.
3. Do not reuse admin keys outside a controlled environment.
4. Avoid exposing secrets in notebooks or logs.

## Key finding in a local environment

During validation, an earlier `.env` expected `chain_id=1337` while the active
network ran on `2025`.

Result:

- With chain validation active, the tests were skipped because of the mismatch.
- After aligning the configuration with the real network, the E2E integration ran
  correctly.
