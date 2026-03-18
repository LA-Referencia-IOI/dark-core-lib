# dark-core-lib

SDK Python unificado para interactuar con dARK 2.0 en blockchain.

Este paquete concentra en una sola API:

- Operaciones de lectura: resolver ARKs, consultar existencia, obtener metadatos
- Operaciones de escritura/administración: alta de autoridades, autorización de NAANs, creación y actualización de ARKs

## Resumen

`dark-core-lib` ofrece una capa de alto nivel sobre contratos inteligentes para trabajar con identificadores persistentes ARK.

Soporta dos modos de operación:

- `read_only=True`: solo consultas (no requiere clave de admin)
- `read_only=False`: consultas + transacciones firmadas (requiere configuración de autoridad y clave de admin)

## Arquitectura

```text
DARKCoreClient
├── Chain service       (conectividad y estado de red)
├── ARK service         (resolve, exists, get, create, update)
└── Authority service   (setup, autorización NAAN, consulta de autoridades)

Contratos on-chain:
- Contrato de autoridades (registro, NAANs, claves cifradas)
- Contrato dARK (almacenamiento y resolución de ARKs)
```

## Instalación

```bash
cd dark-core-lib
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Con dependencias de desarrollo:

```bash
pip install -e ".[dev]"
```

## Configuración

Puedes partir de `.env.example` o usar `.env.integration` para pruebas E2E.

### Variables requeridas en todos los modos

- `DARK_RPC_URL`
- `DARK_CONTRACT_ADDRESS`

### Recomendadas

- `DARK_CHAIN_ID`
- `DARK_VALIDATE_CHAIN_ID` (`True`/`False`)

### Requeridas solo para modo escritura

- `DARK_AUTHORITY_ADDRESS`
- `DARK_ADMIN_PRIVATE_KEY`

### Opcionales

- `DARK_READ_ONLY`
- `DARK_GAS_LIMIT`
- `DARK_TX_TIMEOUT_SECONDS`

Ejemplo:

```env
DARK_RPC_URL=http://localhost:8545
DARK_CHAIN_ID=2025
DARK_CONTRACT_ADDRESS=0x...
DARK_AUTHORITY_ADDRESS=0x...
DARK_ADMIN_PRIVATE_KEY=0x...
DARK_READ_ONLY=False
DARK_VALIDATE_CHAIN_ID=True
DARK_GAS_LIMIT=500000
DARK_TX_TIMEOUT_SECONDS=120
```

## Inicio rápido

### Modo lectura

```python
from dark_core_lib import DARKCoreClient

client = DARKCoreClient.from_env(read_only=True)

print(client.is_connected())
print(client.get_block_number())

exists = client.ark_exists("12345", "document-001")
if exists:
    url = client.resolve_ark("12345", "document-001")
    info = client.get_ark("12345", "document-001")
    print(url, info.cid)
```

### Modo escritura

```python
from dark_core_lib import DARKCoreClient

client = DARKCoreClient.from_env(read_only=False)

authority = client.setup_authority("org-uuid-001", ["12345"])

ark = client.create_ark(
    "org-uuid-001",
    "12345",
    "document-001",
    "https://example.org/docs/1",
    "Qm...",
)

updated = client.update_ark(
    "org-uuid-001",
    "12345",
    "document-001",
    "https://example.org/docs/1?v=2",
    "Qm...v2",
)
```

## API pública

### Cliente principal

- `DARKCoreClient.from_env(env_path=None, read_only=None)`
- `is_connected()`
- `get_block_number()`
- `get_admin_balance()`

### Autoridades

Vía wrappers del cliente:

- `setup_authority(uuid, naans, fund_amount_wei=None)`
- `get_authority_by_uuid(uuid)`
- `get_authority_by_wallet(wallet_address)`
- `get_authorized_naans(uuid)`
- `is_authorized_for_naan(uuid, naan)`
- `get_wallet_balance(uuid)`

Vía servicios:

- `client.authorities.setup(...)`
- `client.authorities.get(...)`
- `client.authorities.authorize_naan(...)`
- `client.authorities.authorize_naans(...)`

### ARKs

Vía wrappers del cliente:

- `create_ark(uuid, naan, name, url, cid)`
- `update_ark(uuid, naan, name, url, cid)`
- `resolve_ark(naan, name)`
- `get_ark(naan, name)`
- `ark_exists(naan, name)`

Vía servicios:

- `client.arks.create(...)`
- `client.arks.update(...)`
- `client.arks.resolve(...)`
- `client.arks.get(...)`
- `client.arks.exists(...)`

## Modelos

- `AuthorityInfo`
  - `uuid`, `wallet_address`, `naans`, `active`
- `ARKInfo`
  - `naan`, `name`, `url`, `cid`, `owner`, `created_at`, `updated_at`, `ark_id`
- `TxReceiptInfo`
  - `tx_hash`, `status`, `gas_used`, `block_number`

## Manejo de errores

Excepciones principales:

- `DarkCoreError`
- `ConfigurationError`
- `ConnectionError`
- `ReadOnlyModeError`
- `TransactionError`
- `AuthorityError`, `AuthorityNotFoundError`, `AuthorityAlreadyExistsError`, `AuthorizationError`
- `ARKError`, `ARKNotFoundError`, `ARKAlreadyExistsError`

## Seguridad

Para operaciones de autoridad, las claves privadas de wallets de autoridades se cifran con AES-256-GCM antes de almacenarse on-chain.

Recomendaciones:

- Usa esta librería en redes privadas/permissionadas
- No expongas `DARK_ADMIN_PRIVATE_KEY`
- Evita logs con secretos

## Notebooks

- End-to-end (alta autoridad + create/update/resolve ARK):
  - `notebooks/dark_core_lib_e2e_demo.ipynb`
- Solo lectura (consulta y resolución):
  - `notebooks/dark_core_lib_read_only_demo.ipynb`

## Testing

### Unit tests

```bash
python3 -m pytest -q
```

### Integración E2E

```bash
DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q -m integration tests/integration/test_e2e.py
```

## Estructura del proyecto

```text
dark-core-lib/
├── dark_core_lib/
│   ├── client.py
│   ├── config.py
│   ├── crypto.py
│   ├── models.py
│   ├── exceptions.py
│   ├── abi.py
│   └── services/
│       ├── authority.py
│       ├── ark.py
│       ├── chain.py
│       └── tx.py
├── notebooks/
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## Licencia

AGPL-3.0-only. Ver `LICENSE` para detalles.

## Documentación extendida

Ver documentación técnica completa en `docs/`:

- Índice: `docs/README.md`
