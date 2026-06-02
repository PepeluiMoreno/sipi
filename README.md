# SIPI — monorepo

**Sistema de Información del Patrimonio Inmatriculado** (proyecto de Europa Laica).
Inventario, geolocalización y seguimiento de inmuebles del patrimonio
inmatriculado, a partir de fuentes abiertas (catastro/inmatriculaciones, OSM,
Wikidata) y portales inmobiliarios.

Este repositorio reúne, con su historial preservado, los componentes que antes
vivían en repos separados (`sipi-core`, `sipi-api`, `sipi-frontend`,
`sipi-survey`, `sipi-etl`).

## Estructura

```
sipi/
├── packages/
│   └── sipi-core/     # Núcleo de dominio: modelos SQLAlchemy, mixins,
│                      #   sesiones y migraciones Alembic (única fuente de verdad)
├── apps/
│   ├── api/           # API GraphQL (Strawberry + SQLAlchemy async + PostGIS)
│   └── frontend/      # SPA Vue 3 + Pinia + Apollo + Leaflet
├── services/
│   ├── survey/        # Orquestador de ETL y monitorización (scraping, eventos)
│   └── etl/           # ETL: censo, OSM/Wikidata, matching
├── pyproject.toml     # workspace uv (miembro: packages/sipi-core)
└── .gitignore
```

## Relación entre componentes

```
                    packages/sipi-core  (modelos + esquema + migraciones)
                      ▲        ▲       ▲
                      │        │       │
            apps/api ─┘  services/etl ─┘  services/survey
                │
        apps/frontend ── GraphQL ──> apps/api
```

Todos comparten la **misma base de datos PostgreSQL/PostGIS** y los modelos de
`packages/sipi-core`.

## Stack por componente

| Componente | Stack | Build |
|------------|-------|-------|
| `packages/sipi-core` | Python 3.12, SQLAlchemy 2.0 (async), Alembic, GeoAlchemy2 | `uv` / `pyproject.toml` |
| `apps/api` | Strawberry GraphQL, Starlette, asyncpg, PostGIS | `requirements.txt` |
| `apps/frontend` | Vue 3, Pinia, Vue Router, Apollo, Leaflet, Tailwind, Vite | `pnpm` / `package.json` |
| `services/survey` | FastAPI, SQLAlchemy, Redis, Selenium, Overpass/WDQS | `requirements.txt` |
| `services/etl` | asyncpg, SQLAlchemy, Selenium, Overpass/WDQS | `requirements.txt` |

## Desarrollo

Cada componente conserva su propio arranque (ver el README de cada carpeta):

```bash
# Núcleo de dominio (paquete instalable)
cd packages/sipi-core && uv sync       # o: pip install -e .

# API
cd apps/api && pip install -r requirements.txt
#   y, en el monorepo, el núcleo por ruta en lugar de dependencia git:
#   pip install -e ../../packages/sipi-core

# Frontend
cd apps/frontend && pnpm install && pnpm dev

# ETL / Survey
cd services/etl && pip install -r requirements.txt
```

Las variables de entorno **no** se versionan: cada componente trae su
`.env.example` (o `.env.*.example`) como plantilla.

## Notas / pendientes

- **Consolidación de modelos**: `apps/api` todavía mantiene su propia copia de
  los modelos en `app/db/models`. Migrarlos para que consuma
  `packages/sipi-core` (por ruta) está planificado en
  `apps/api/docs/CONSOLIDACION_MODELOS.md` — implica decidir la estrategia de
  esquema (`sipi` único vs `app`/`gis`) y regenerar la línea base de Alembic, y
  debe validarse contra una base de datos.
- **Fusión survey + etl**: `services/survey` y `services/etl` comparten parte de
  `src/` (modelos de apoyo, OSM/Wikidata). Quedan co-localizados; la
  deduplicación efectiva de su código es un paso posterior.
- Un `docker-compose` unificado en la raíz queda pendiente; por ahora cada
  componente trae su propio compose/Dockerfile.

## Migración desde los repos antiguos

Los cinco repos originales se integraron con `git subtree` preservando su
historial. Una vez validado este monorepo, los repos
`sipi-core`/`sipi-api`/`sipi-frontend`/`sipi-survey`/`sipi-etl` pueden
**archivarse** en GitHub.
