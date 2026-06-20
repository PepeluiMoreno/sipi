# apps/sipi/api — API GraphQL de SIPI (expedientes)

API GraphQL (Strawberry + Starlette, async) de la aplicación de expedientes. **No
define modelos propios**: importa `sipi_core.models` (de `packages/sipi-core`) y
**autogenera** el esquema GraphQL por introspección.

## Arquitectura

- `app/graphql/schema.py` — generador: recorre `sipi_core.models`, crea tipos,
  queries (`getX`, `xs(limit,offset,filters,sort)` → `{items,total}`) y mutaciones.
- `app/graphql/app.py` — app Starlette (GraphQL en `/graphql`, `/health`, webhook
  `/odm_webhook`, endpoints `/api/notifications/*`).
- `app/db/sessions/` — engine/sesiones async (asyncpg). El modelo y la `Base` viven
  en `sipi-core` (no hay `Base` propia).

## Stack

Python ≥3.10 · Strawberry GraphQL · Starlette · SQLAlchemy 2.0 (asyncpg) · sipi-core.

## Ejecutar (local)

```bash
pip install -e ../../../packages/sipi-core          # núcleo
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://sipi:<pwd>@localhost:5433/sipi
export APP_SCHEMA=sipi GIS_SCHEMA=sipi DEFAULT_SCHEMA=sipi DATABASE_SCHEMA=sipi DEFINED_SCHEMAS=sipi
export PYTHONPATH=.:../../../packages/sipi-core/src
uvicorn app.graphql.app:application --host 0.0.0.0 --port 8040
# GraphiQL en http://localhost:8040/graphql
```

O vía el compose raíz: `docker compose up -d api` (monta `packages/sipi-core/src/sipi_core`).

## Notas

- Esquema de BD: **opción B** (todo en `sipi`).
- Las migraciones **no** viven aquí: están en `sipi-core` (`alembic`).
- Histórico de la consolidación de modelos: [docs/CONSOLIDACION_MODELOS.md](docs/CONSOLIDACION_MODELOS.md).
- Problema conocido de autogenerate (enums/naming): [docs/ALEMBIC_AUTOGENERATE_ISSUE.md](docs/ALEMBIC_AUTOGENERATE_ISSUE.md).
