# Arquitectura

## Mapa lógico

```text
DARKCoreClient
├── ChainService
├── ARKService
├── AuthorityService
└── MetadataService / storage helpers

Contratos:
- Authority: registro de autoridad, NAANs, clave cifrada
- dARK: create/update/get/resolve ARKs
```

## Flujo de inicialización

1. `CoreConfig.from_env(...)` carga y valida variables.
2. Se crea conexión `Web3.HTTPProvider`.
3. Se valida conexión y opcionalmente `chain_id`.
4. Se construyen instancias de contrato:
   - dARK (siempre)
   - Authority (si está configurado)
5. Se inicializan servicios y wrappers de cliente.

## Flujo de autoridad (write mode)

1. Verificar que UUID no exista.
2. Crear wallet de autoridad.
3. Cifrar private key con AES-256-GCM.
4. Financiar wallet desde admin.
5. Registrar autoridad en contrato.
6. Autorizar NAANs.
7. Devolver estado consolidado (`AuthorityInfo`).

## Flujo ARK

- Lectura:
  - `exists`, `resolve`, `get`
- Escritura:
  - `create`: valida no existencia, firma con credenciales de autoridad
  - `update`: valida existencia, firma con credenciales de autoridad

## Metadata compartida

- `dark_core_lib.metadata.schemas`
  - define `Level1Metadata` y referencias a Level-2.
- `dark_core_lib.metadata.storage`
  - abstrae `filesystem` y `store_api`.
- `dark_core_lib.metadata.service.MetadataService`
  - encapsula el flujo compartido `L2 -> inject cid -> L1` y la carga `L1 -> L2`.

Esta capa no publica nada por HTTP; la usan `dark-core-minter-api` y `dark-core-resolver-api` para mantener el mismo contrato de metadata.

## Decisiones relevantes

- Wrappers en cliente para simplificar uso y compatibilidad.
- Servicios separados para claridad y testabilidad.
- `read_only` como guardia explícita para evitar escrituras accidentales.
- Validación de bytecode/contratos en tests de integración para evitar falsos negativos.
