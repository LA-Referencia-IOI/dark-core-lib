# Guía de Migración

## Objetivo

Migrar desde código separado de lectura/escritura a una API única.

## Cambios principales

1. Import único:
   - Nuevo: `from dark_core_lib import DARKCoreClient`
2. Inicialización:
   - Nuevo: `DARKCoreClient.from_env(read_only=True|False)`
3. Métodos:
   - Se mantienen wrappers para minimizar cambios.
4. Configuración:
   - Esquema unificado de variables `DARK_*`.

## Tabla de mapeo rápido

- `setup_authority` -> `setup_authority` (wrapper) o `client.authorities.setup`
- `create_ark` -> `create_ark` (wrapper) o `client.arks.create`
- `update_ark` -> `update_ark` (wrapper) o `client.arks.update`
- `resolve_ark` -> `resolve_ark` (wrapper) o `client.arks.resolve`
- `get_ark` -> `get_ark` (wrapper) o `client.arks.get`
- `ark_exists` -> `ark_exists` (wrapper) o `client.arks.exists`

## Estrategia sugerida

1. Cambiar import e inicialización.
2. Mantener wrappers para migración rápida.
3. Mover gradualmente a servicios (`client.authorities` / `client.arks`) en código nuevo.
4. Ejecutar suite de integración E2E en cada etapa.

## Riesgos comunes

- `chain_id` desalineado entre `.env` y red activa.
- Direcciones de contratos antiguas.
- Clave admin no correspondiente al contrato de autoridad.

Mitigación:

- Usar `.env.integration` generado desde despliegue real.
