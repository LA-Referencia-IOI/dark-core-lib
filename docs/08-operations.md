# Notas Operativas

## Checklist para entorno local sano

1. RPC accesible en `DARK_RPC_URL`.
2. `DARK_CHAIN_ID` alineado con la cadena activa.
3. Bytecode presente en:
   - `DARK_CONTRACT_ADDRESS`
   - `DARK_AUTHORITY_ADDRESS` (si write mode)
4. Clave admin válida para el contrato de autoridad.

## Verificaciones rápidas útiles

- Conectividad:
  - `client.is_connected()`
- Cadena:
  - `client.get_block_number()`
- Balance admin (write mode):
  - `client.get_admin_balance()`

## Síntomas y diagnóstico

- Error de cadena:
  - `Chain ID mismatch`
  - Acción: revisar `DARK_CHAIN_ID` o desactivar validación temporalmente.
- Error de contrato:
  - `Could not transact with/call contract function`
  - Acción: revisar direcciones y despliegue.
- Error en modo:
  - `ReadOnlyModeError`
  - Acción: inicializar cliente con `read_only=False`.

## Recomendaciones de operación

1. Mantener `.env.integration` sincronizado con último despliegue.
2. Evitar hardcodear direcciones en código.
3. Ejecutar integración E2E antes de cambios de ABI o configuración.
