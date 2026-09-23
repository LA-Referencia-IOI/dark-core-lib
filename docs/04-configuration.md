# Configuración y Entornos

## Variables de entorno

### Requeridas siempre

- `DARK_RPC_URL`
- `DARK_CONTRACT_ADDRESS`

### Requeridas en modo escritura

- `DARK_AUTHORITY_ADDRESS`
- `DARK_ADMIN_PRIVATE_KEY`

### Recomendadas

- `DARK_CHAIN_ID`
- `DARK_VALIDATE_CHAIN_ID`

### Opcionales

| Variable | Default | Descripcion |
| --- | --- | --- |
| `DARK_READ_ONLY` | `true` | Modo lectura por defecto; usar `false` para operaciones firmadas |
| `DARK_GAS_LIMIT` | `550000` | Limite de gas por transaccion de escritura; el minter usa el doble solo en rescue |
| `DARK_TX_TIMEOUT_SECONDS` | `120` | Tiempo maximo esperando receipt |

### ABI overrides

| Variable | Default | Description |
| --- | --- | --- |
| `DARK_ABI_JSON` | unset | Optional JSON override for the bundled dARK ABI (`DARK_ABI` in `dark_core_lib/abi.py`) |
| `AUTHORITY_ABI_JSON` | unset | Optional JSON override for the bundled Authority ABI (`AUTHORITY_ABI` in `dark_core_lib/abi.py`) |

Semantics in `CoreConfig.from_env()` (`dark_core_lib/config.py`):

- when the variable is set, its value is parsed with `json.loads` and used as the contract ABI
- if the value is not valid JSON, the library silently falls back to the bundled ABI, so a bad override never breaks startup
- when the variable is unset, the bundled ABI is used and the library works standalone

## Archivos recomendados

- `.env.example`: plantilla base
- `.env.integration`: configuración real para tests E2E locales

## Buenas prácticas

1. Mantener `DARK_VALIDATE_CHAIN_ID=True` por defecto.
2. Usar `read_only=True` para dashboards y procesos de consulta.
3. No reutilizar claves de admin fuera de entorno controlado.
4. Evitar exponer secretos en notebooks o logs.

## Hallazgo clave en entorno local

Durante validación se detectó que un `.env` previo esperaba `chain_id=1337` pero la red activa corría en `2025`.

Resultado:

- Con validación de cadena activa, los tests se saltaban por mismatch.
- Al alinear configuración con red real, la integración E2E se ejecutó correctamente.
