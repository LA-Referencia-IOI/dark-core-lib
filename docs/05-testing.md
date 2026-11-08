# Testing and E2E integration

## Test types

- Unit:
  - Configuration
  - Models
- Integration:
  - Real network connection
  - Deployed contracts
  - Full authority + ARK flow

## Commands

### Unit tests

```bash
python3 -m pytest -q
```

### Integration only

```bash
DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q -m integration tests/integration/test_e2e.py
```

### Everything (unit + integration)

```bash
DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q
```

## Safety logic in integration tests

The E2E tests `skip` if:

- They are not explicitly enabled (`DARK_CORE_LIB_RUN_INTEGRATION`).
- The environment file is missing.
- There is no deployed bytecode at the configured contract addresses.
- The read/write client cannot be initialized.

This avoids false failures on machines without a complete local stack.

## Validated state

In the analyzed local environment:

- Unit tests: OK
- Full E2E integration: OK with a correct `.env.integration`
