# Visión General

`dark-core-lib` es un SDK Python unificado para dARK 2.0 que combina:

- Operaciones de lectura de ARKs.
- Operaciones de escritura y administración de autoridades.

## Objetivo

Tener una sola librería, en un directorio separado, sin depender en runtime de librerías previas separadas para lectura/escritura.

## Modos de operación

- `read_only=True`
  - Solo consultas.
  - No requiere clave administrativa.
- `read_only=False`
  - Consultas + transacciones firmadas.
  - Requiere contrato de autoridad y clave administrativa.

## Componentes principales

- Cliente principal: `DARKCoreClient`
- Servicios:
  - `AuthorityService`
  - `ARKService`
  - `ChainService`
- Soporte:
  - Configuración (`CoreConfig`)
  - Modelos (`AuthorityInfo`, `ARKInfo`, `TxReceiptInfo`)
  - Cifrado AES-GCM de claves de autoridad
  - ABIs embebidas de contratos
