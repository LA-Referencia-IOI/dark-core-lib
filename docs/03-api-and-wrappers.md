# API y Wrappers

## Cliente principal

- `DARKCoreClient.from_env(env_path=None, read_only=None)`
- `is_connected()`
- `get_block_number()`
- `get_admin_balance()`

## Qué son los wrappers

Los wrappers son atajos en `DARKCoreClient` que delegan a servicios internos.

Ejemplos:

- `client.setup_authority(...)` -> `client.authorities.setup(...)`
- `client.resolve_ark(...)` -> `client.arks.resolve(...)`

Ventajas:

- API rápida para uso común.
- Menor curva de aprendizaje.
- Migración más suave desde código previo.

## Autoridades

Wrappers:

- `setup_authority(uuid, naans, fund_amount_wei=None)`
- `get_authority_by_uuid(uuid)`
- `get_authority_by_wallet(wallet_address)`
- `get_authorized_naans(uuid)`
- `is_authorized_for_naan(uuid, naan)`
- `get_wallet_balance(uuid)`

Servicios equivalentes:

- `client.authorities.setup(...)`
- `client.authorities.get(...)`
- `client.authorities.get_by_wallet(...)`
- `client.authorities.authorize_naan(...)`
- `client.authorities.authorize_naans(...)`

## ARKs

Wrappers:

- `create_ark(uuid, naan, name, url, cid)`
- `update_ark(uuid, naan, name, url, cid)`
- `resolve_ark(naan, name)`
- `resolve_ark_by_id(ark)`
- `get_ark(naan, name)`
- `get_ark_by_id(ark)`
- `ark_exists(naan, name)`
- `ark_exists_by_id(ark)`

Servicios equivalentes:

- `client.arks.create(...)`
- `client.arks.update(...)`
- `client.arks.resolve(...)`
- `client.arks.get(...)`
- `client.arks.exists(...)`

## Metadata compartida

No todo en `dark-core-lib` son wrappers de blockchain. El paquete también expone piezas compartidas para los servicios HTTP:

- `parse_ark_id(raw)`
- `MetadataService(storage)`
- `get_metadata_storage(...)`
- `FileSystemMetadataStorage`
- `StoreApiMetadataStorage`
- `Level1Metadata`
- `OriginalMetadataRef`
- `StoredDocument`

Uso típico:

- el minter usa `MetadataService` para persistir L2, inyectar el CID interno en L1 y almacenar el L1 final
- el resolver usa `MetadataService` para cargar L1 desde el CID on-chain y luego recuperar L2 para `?metadata`

## Excepciones de uso frecuente

- `ReadOnlyModeError`: intento de escritura en modo lectura.
- `ConfigurationError`: configuración faltante/inválida.
- `ConnectionError`: problema de red o mismatch de `chain_id`.
- `Authority*` y `ARK*`: errores de dominio de contratos.
- `TransactionError`: transacción revertida o fallida.
