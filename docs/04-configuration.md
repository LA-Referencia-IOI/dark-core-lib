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

- `DARK_READ_ONLY`
- `DARK_GAS_LIMIT`
- `DARK_TX_TIMEOUT_SECONDS`

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
