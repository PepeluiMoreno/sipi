# SIPI — Sistema de Información del Patrimonio Inmobiliario

Monorepo único de SIPI: dos aplicaciones que comparten un mismo núcleo de dominio.

- **SIPI** (`apps/sipi`) — gestión y mantenimiento de **expedientes** del patrimonio
  inmobiliario (inmuebles, entidades religiosas, ciclo de vida, validación de hallazgos).
- **SIPI-Survey** (`apps/sipi-survey`) — aplicación técnica de **vigilancia**:
  establecimiento y control de los *dispositivos de vigilancia* (watchers/scrapers que
  vigilan portales y fuentes: Idealista, Fotocasa, OSM/Wikidata, BOE, BDNS…).

Ambas se construyen sobre **`packages/sipi-core`** (modelos de dominio = única fuente
de verdad).

## Estructura

```
packages/
└── sipi-core/              Núcleo de dominio (modelos SQLAlchemy, mixins, acceso a datos)
    └── src/sipi_core/
        ├── modules/<dominio>/   actores, catalogos, geografia, inmuebles, expedientes,
        │                        entidades_religiosas, transmisiones, intervenciones,
        │                        documentos, discovery, notificaciones, usuarios,
        │                        acceso (RBAC), comunicacion, configuracion
        ├── models/__init__.py   FACHADA: re-exporta todos los modelos (import sipi_core.models)
        ├── db/                  registry, metadata, alembic (migraciones)
        └── mixins/
apps/
├── sipi/                   Aplicación de expedientes
│   ├── api/                GraphQL (Strawberry/Starlette), autogenerado desde sipi-core
│   └── frontend/           Vue 3 + Pinia + Apollo + Leaflet
└── sipi-survey/            Aplicación de vigilancia (control de dispositivos)
services/
└── discovery/             Pipelines de descubrimiento (los "dispositivos")
    ├── etl/                Carga (ODM/loaders ORM sobre sipi-core), census, fusión
    ├── survey/             Geocoders, RegionMonitor, orquestador de portales, scoring
    └── osm/                Sincronización OSM/Wikidata
docs/                       Documentación viva del monorepo
docker-compose.yml          Orquestación raíz (db + api + frontend)
pyproject.toml              Workspace uv
_legacy/                    Repos antiguos preservados (gitignored, pre-monorepo)
```

## Decisiones de arquitectura

- **Modelo único en `sipi-core`.** API, ETL y survey lo importan; no hay modelos
  duplicados. La API GraphQL se autogenera por introspección de `sipi_core.models`.
- **Esquema de BD: opción B** — todo en el esquema `sipi` de PostgreSQL, configurable
  por entorno (`APP_SCHEMA=GIS_SCHEMA=DEFAULT_SCHEMA=DEFINED_SCHEMAS=sipi`). Las FKs/PKs
  de los modelos están parametrizadas con `APP_SCHEMA`.
- **PostgreSQL local** (sin Supabase). Contenedor `db` del compose, volumen `sipi_pgdata`.
- **Expediente** es la bitácora del ciclo de vida del inmueble con flujo de validación
  (`propuesto → ratificado/descartado`) y dimensión de confianza (`certeza` CIERTO/DUDOSO,
  `confianza` 0–1). Las detecciones del descubrimiento se materializan como Expediente.
- **RBAC por transacción** (`modules/acceso`, estilo SIGA): ratificar/descartar un
  expediente es una *transacción* sujeta a permiso.
- **Eventos ODMGR como backbone** (`modules/comunicacion/services/odmgr_router`): una
  actualización de dataset (OpenDataManager) bifurca, según política configurable, en
  (a) notificación a los roles implicados y/o (b) disparo del pipeline de
  descubrimiento (extracción → análisis → scoring → Expediente). Ver
  [docs/DISENO_MODULOS_NUEVOS.md](docs/DISENO_MODULOS_NUEVOS.md) §2bis.

## Puesta en marcha (desarrollo)

```bash
# 1) Base de datos (reusa el volumen de datos existente sipi_pgdata)
docker compose up -d db

# 2) Núcleo instalable (editable) para herramientas locales
pip install -e packages/sipi-core

# 3) Migraciones (esquema sipi)
cd packages/sipi-core/src/sipi_core
export DATABASE_URL=postgresql://sipi:<pwd>@localhost:5433/sipi
export DEFINED_SCHEMAS=sipi APP_SCHEMA=sipi GIS_SCHEMA=sipi DEFAULT_SCHEMA=sipi
alembic upgrade head

# 4) Stack completo
docker compose up -d        # db + api (GraphQL en :8040/graphql) + frontend (:5173)
```

### Acceso vía Traefik (dev, estilo SIGA)

```bash
docker compose -f docker-compose.dev.yml up -d
```
Expone el frontend tras el Traefik compartido (red `traefik_public`) en
**https://sipi.optiplex-790** (HTTP y HTTPS con cert auto-firmado). La API y la BD
quedan en la red interna; el frontend reenvía `/graphql` a `api:8040` (proxy de
Vite, mismo origen, sin CORS). El dominio es configurable:

```bash
# .env (raíz)
APP_DEV_DOMAIN=sipi.optiplex-790   # debe resolver al host (Traefik enruta por Host)
APP_PREFIX=sipi
```

## Documentación

- [docs/DISENO_MODULOS_NUEVOS.md](docs/DISENO_MODULOS_NUEVOS.md) — diseño de los módulos
  acceso / comunicación / configuración (+ §2bis ODMGR).
- [packages/sipi-core/src/sipi_core/docs/INTEGRIDAD_DIFERIDA_FASE1.md](packages/sipi-core/src/sipi_core/docs/INTEGRIDAD_DIFERIDA_FASE1.md)
  — estado de integridad de esquema y el problema de `naming_convention`.
- [apps/sipi/api/docs/CONSOLIDACION_MODELOS.md](apps/sipi/api/docs/CONSOLIDACION_MODELOS.md)
  — histórico de la consolidación de modelos API → sipi-core.

> Los documentos de diseño previos al monorepo y los repos originales se conservan en
> `_legacy/` (no versionado) y en el historial de git.
