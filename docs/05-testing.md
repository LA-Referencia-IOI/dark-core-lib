# Testing e Integración E2E

## Tipos de tests

- Unitarios:
  - Configuración
  - Modelos
- Integración:
  - Conexión real a red
  - Contratos desplegados
  - Flujo completo autoridad + ARK

## Comandos

### Unit tests

```bash
python3 -m pytest -q
```

### Solo integración

```bash
DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q -m integration tests/integration/test_e2e.py
```

### Todo (unit + integración)

```bash
DARK_CORE_LIB_RUN_INTEGRATION=1 \
DARK_CORE_LIB_ENV_PATH=./.env.integration \
python3 -m pytest -q
```

## Lógica de seguridad en integración

Los tests E2E hacen `skip` si:

- No se habilitan explícitamente (`DARK_CORE_LIB_RUN_INTEGRATION`).
- Falta archivo de entorno.
- No hay bytecode desplegado en direcciones de contrato configuradas.
- No se puede inicializar cliente de lectura/escritura.

Esto evita fallos falsos en máquinas sin stack local completo.

## Estado validado

En el entorno local analizado:

- Unit tests: OK
- Integración E2E completa: OK con `.env.integration` correcto
