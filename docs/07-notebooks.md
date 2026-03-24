# Notebooks

## Disponibles en este proyecto

- `notebooks/dark_core_lib_e2e_demo.ipynb`
  - Demo completo: alta de autoridad, creación/actualización/resolución de ARK.
- `notebooks/dark_core_lib_read_only_demo.ipynb`
  - Demo de solo lectura para consultas y resolución.

## Recomendación de uso

1. Ejecutar desde el directorio raíz de `dark-core-lib`.
2. Tener disponible `../.env.integration` o `../.env`.
3. Verificar antes que la red y contratos estén desplegados.
4. Para un flujo HTTP completo entre admin, minter y resolver, usar el notebook del monorepo en `dark-developer/notebooks/dark_e2e_authority_to_resolver.ipynb`.

## Qué se adaptó

- Imports y cliente a la API unificada.
- Carga de entorno con prioridad a `.env.integration`.
- Eliminación de referencias a API antigua.
