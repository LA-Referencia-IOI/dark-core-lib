# Migración desde Orchestrator y Observer a dark-core-lib

Este documento describe una migración práctica desde el esquema de dos librerías separadas (una para escritura/admin y otra para lectura) hacia `dark-core-lib`.

## Objetivo

- Unificar imports y cliente.
- Mantener compatibilidad funcional.
- Reducir riesgo con migración incremental.

## 1. Cambio de imports

Antes:

```python
from dark_orchestrator import DARKOrchestrator
from dark_observer import DARKObserver
```

Después:

```python
from dark_core_lib import DARKCoreClient
```

## 2. Inicialización

Antes:

```python
orchestrator = DARKOrchestrator()
observer = DARKObserver()
```

Después (dos opciones):

```python
# Cliente único con escritura + lectura
client = DARKCoreClient.from_env(read_only=False)
```

```python
# Cliente sólo lectura (equivalente a observer)
ro_client = DARKCoreClient.from_env(read_only=True)
```

## 3. Equivalencias de API

### Operaciones de autoridad

| Antes | Después (wrapper) | Después (servicio) |
|---|---|---|
| `orchestrator.setup_authority(uuid, naans)` | `client.setup_authority(uuid, naans)` | `client.authorities.setup(uuid, naans)` |
| `orchestrator.get_authority_by_uuid(uuid)` | `client.get_authority_by_uuid(uuid)` | `client.authorities.get(uuid)` |
| `orchestrator.get_authority_by_wallet(addr)` | `client.get_authority_by_wallet(addr)` | `client.authorities.get_by_wallet(addr)` |
| `orchestrator.get_authorized_naans(uuid)` | `client.get_authorized_naans(uuid)` | `client.authorities.get_authorized_naans(uuid)` |
| `orchestrator.is_authorized_for_naan(uuid, naan)` | `client.is_authorized_for_naan(uuid, naan)` | `client.authorities.is_authorized_for_naan(uuid, naan)` |
| `orchestrator.get_wallet_balance(uuid)` | `client.get_wallet_balance(uuid)` | `client.authorities.get_wallet_balance(uuid)` |

### Operaciones ARK

| Antes | Después (wrapper) | Después (servicio) |
|---|---|---|
| `orchestrator.create_ark(...)` | `client.create_ark(...)` | `client.arks.create(...)` |
| `orchestrator.update_ark(...)` | `client.update_ark(...)` | `client.arks.update(...)` |
| `orchestrator.resolve_ark(naan, name)` | `client.resolve_ark(naan, name)` | `client.arks.resolve(naan, name)` |
| `orchestrator.get_ark(naan, name)` | `client.get_ark(naan, name)` | `client.arks.get(naan, name)` |
| `orchestrator.ark_exists(naan, name)` | `client.ark_exists(naan, name)` | `client.arks.exists(naan, name)` |
| `observer.resolve(naan, name)` | `ro_client.resolve_ark(naan, name)` | `ro_client.arks.resolve(naan, name)` |
| `observer.get_ark(naan, name)` | `ro_client.get_ark(naan, name)` | `ro_client.arks.get(naan, name)` |
| `observer.ark_exists(naan, name)` | `ro_client.ark_exists(naan, name)` | `ro_client.arks.exists(naan, name)` |

### Utilidades

| Antes | Después |
|---|---|
| `orchestrator.get_block_number()` | `client.get_block_number()` |
| `observer.get_block_number()` | `ro_client.get_block_number()` |
| `orchestrator.is_connected()` | `client.is_connected()` |
| `observer.is_connected()` | `ro_client.is_connected()` |
| `orchestrator.get_admin_balance()` | `client.get_admin_balance()` |

## 4. Configuración

### Variables mínimas lectura

- `DARK_RPC_URL`
- `DARK_CONTRACT_ADDRESS`

### Variables adicionales escritura

- `DARK_AUTHORITY_ADDRESS`
- `DARK_ADMIN_PRIVATE_KEY`

### Recomendado

- `DARK_CHAIN_ID`
- `DARK_VALIDATE_CHAIN_ID=True`

## 5. Plan de migración por fases

1. **Fase 1 - Import único**
   - Sustituir imports por `DARKCoreClient`.
2. **Fase 2 - Modo dual controlado**
   - Lectura con `read_only=True`.
   - Escritura con `read_only=False`.
3. **Fase 3 - Wrappers primero**
   - Migrar llamadas usando wrappers para cambiar lo mínimo.
4. **Fase 4 - Servicios internos**
   - Refactor gradual a `client.authorities` y `client.arks` en módulos nuevos.
5. **Fase 5 - End-to-end**
   - Ejecutar tests unitarios + integración antes de retirar código antiguo.

## 6. Ejemplo completo (antes/después)

Antes:

```python
from dark_orchestrator import DARKOrchestrator
from dark_observer import DARKObserver

orchestrator = DARKOrchestrator()
observer = DARKObserver()

auth = orchestrator.setup_authority("org-1", ["12345"])
ark = orchestrator.create_ark("org-1", "12345", "doc-1", "https://x", "Qm...")
url = observer.resolve("12345", "doc-1")
```

Después:

```python
from dark_core_lib import DARKCoreClient

client = DARKCoreClient.from_env(read_only=False)
ro_client = DARKCoreClient.from_env(read_only=True)

auth = client.setup_authority("org-1", ["12345"])
ark = client.create_ark("org-1", "12345", "doc-1", "https://x", "Qm...")
url = ro_client.resolve_ark("12345", "doc-1")
```

`client.create_ark(...)` and `client.update_ark(...)` still return `ARKInfo` by default. They no longer perform a pre-write `exists()` read; the contract itself is the source of truth for duplicate or missing ARKs. Use `fetch_result=False` only for internal worker-style paths that do not need the resulting ARK data.

For worker pipelines, use `client.publish_ark_operations(...)` with operations for one authority UUID. It sends individual create/update transactions with sequential pending nonces and returns semantic per-ARK results without exposing transaction hashes.

## 7. Riesgos y mitigaciones

- `Chain ID mismatch`:
  - Alinear `DARK_CHAIN_ID` con la red activa.
- Contratos sin bytecode:
  - Verificar direcciones desplegadas antes de correr integración.
- Escritura en modo lectura:
  - Usar cliente `read_only=False` para transacciones.

## 8. Validación post-migración

```bash
python3 -m pytest -q

DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q -m integration tests/integration/test_e2e.py
```
