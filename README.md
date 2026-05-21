# dark-core-lib

SDK Python unificado para interactuar con dARK 2.0 en blockchain.

Este paquete concentra en una sola API:

- Operaciones de lectura: resolver ARKs, consultar existencia y recuperar estado on-chain
- Operaciones de escritura/administración: alta de autoridades, autorización de NAANs, creación y actualización de ARKs
- Modelos y utilidades compartidas de metadata: esquemas L1/L2, backends de storage y `MetadataService`

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
├── Authority service   (setup, autorización NAAN, consulta de autoridades)
└── Metadata helpers    (schemas, storage, MetadataService)

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

### Metadata compartida

```python
from dark_core_lib import MetadataService, get_metadata_storage

storage = get_metadata_storage(
    storage_type="filesystem",
    storage_path="./metadata_storage",
)
metadata = MetadataService(storage)

level1 = metadata.load_level1("internal-level1-cid")
level2 = metadata.load_level2(level1)

print(level1.title)
print(level2.content_type)
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

print(ark.ark_id)

updated = client.update_ark(
    "org-uuid-001",
    "12345",
    "document-001",
    "https://example.org/docs/1?v=2",
    "Qm...v2",
)

print(updated.url)
```

`create_ark()` and `update_ark()` are write calls. They submit the transaction, wait for confirmation, and return `ARKInfo` by default. They do not perform an automatic `exists()` read before the write. Worker-style callers that do not need the post-write read can pass `fetch_result=False`.

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

- `create_ark(uuid, naan, name, url, cid, fetch_result=True)`
- `update_ark(uuid, naan, name, url, cid, fetch_result=True)`
- `publish_ark_operations(uuid, operations, pipeline_size=20)`
- `resolve_ark(naan, name)`
- `resolve_ark_by_id(ark)`
- `get_ark(naan, name)`
- `get_ark_by_id(ark)`
- `ark_exists(naan, name)`
- `ark_exists_by_id(ark)`

Vía servicios:

- `client.arks.create(...)`
- `client.arks.update(...)`
- `client.arks.publish_operations(...)`
- `client.arks.resolve(...)`
- `client.arks.get(...)`
- `client.arks.exists(...)`

`create_ark` and `update_ark` return `ARKInfo` by default. With `fetch_result=False`, they return `None` after the transaction confirms and skip the post-write `get_ark()` read. Read methods return chain state and remain unchanged.

`publish_ark_operations` is the worker-oriented fast path. It accepts `ARKPublishOperation` items for one authority UUID, signs individual create/update transactions with sequential pending nonces, sends them in windows controlled by `pipeline_size`, waits for receipts, and returns `ARKPublishResult` values such as `confirmed`, `reverted`, `ambiguous`, `send_failed`, or `not_sent`. It does not expose transaction hashes to callers.

### Metadata compartida

- `parse_ark_id(raw)`
- `MetadataService(storage)`
- `get_metadata_storage(storage_type="store_api" | "filesystem", **kwargs)`
- `FileSystemMetadataStorage`
- `StoreApiMetadataStorage`
- `Level1Metadata`
- `OriginalMetadataRef`
- `StoredDocument`

## Modelos

- `AuthorityInfo`
  - `uuid`, `wallet_address`, `naans`, `active`
- `ARKInfo`
  - `naan`, `name`, `url`, `cid`, `owner`, `created_at`, `updated_at`, `ark_id`
- `TxReceiptInfo`
  - `tx_hash`, `status`, `gas_used`, `block_number`
- `Level1Metadata`
  - payload público mínimo que publica el minter y consume el resolver en `?info`
- `OriginalMetadataRef`
  - referencia interna a L2 con `schema`, `media_type` y `cid`
- `StoredDocument`
  - `content`, `content_type`, `schema`

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
│   ├── ark_id.py
│   ├── client.py
│   ├── config.py
│   ├── crypto.py
│   ├── models.py
│   ├── exceptions.py
│   ├── abi.py
│   ├── metadata/
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── storage/
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
