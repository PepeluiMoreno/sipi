# sipi-core

Paquete Python con el **núcleo de dominio** del ecosistema SIPI (Sistema de
Información del Patrimonio Inmatriculado, proyecto de Europa Laica). Centraliza
los modelos de datos, mixins, la capa de acceso a base de datos y las
migraciones, de modo que el resto de componentes los consuman como dependencia
en lugar de duplicarlos.

## Componentes del ecosistema

| Repo | Rol |
|------|-----|
| **sipi-core** (este) | Modelos SQLAlchemy, mixins, sesiones y migraciones Alembic |
| [sipi-api](https://github.com/PepeluiMoreno/sipi-api) | API GraphQL (Strawberry) sobre estos modelos |
| [sipi-frontend](https://github.com/PepeluiMoreno/sipi-frontend) | SPA Vue 3 + Apollo + Leaflet |
| [sipi-survey](https://github.com/PepeluiMoreno/sipi-survey) | Orquestador de ETL y monitorización |
| [sipi-etl](https://github.com/PepeluiMoreno/sipi-etl) | ETL (censo, OSM/Wikidata, matching) |

## Arquitectura multi-esquema

Los modelos se reparten en dos esquemas PostgreSQL para separar dominio de
datos geoespaciales (ver `sipi_core/docs/MULTI_SCHEMA_ARCHITECTURE.md`):

- **`app`** — dominio de negocio: actores (administraciones, agencias,
  notarios, registradores, técnicos, entidades religiosas, privados),
  inmuebles, documentos, transmisiones, intervenciones, subvenciones,
  figuras de protección, tipologías, historiografía, usuarios y discovery.
- **`gis`** — geografía y datos espaciales (PostGIS): geografía administrativa
  e integración con OpenStreetMap.

## Estructura

```
sipi_core/
├── models/        # modelos de dominio (inmuebles, actores_base, geografia, ...)
├── mixins/        # mixins reutilizables: base, identificacion, direccion,
│                  #   contacto, documento, titularidad
├── db/
│   ├── metadata.py    # MetaData / esquemas
│   ├── registry.py    # registro de modelos
│   ├── sessions/      # gestor de sesiones (async/sync)
│   └── alembic/       # entorno y versiones de migración
├── config.py
├── alembic.ini
└── docker/        # Dockerfiles, compose, nginx, init-db
```

## Stack

Python 3.12 · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL + PostGIS ·
GeoAlchemy2.

## Configuración

Las variables de entorno **no** se versionan. Usa las plantillas:

```bash
cp sipi_core/.env.development.example sipi_core/.env.development   # desarrollo
cp sipi_core/.env.production.example  sipi_core/.env.production    # producción
# rellenar los valores marcados como CHANGEME (DB_PASSWORD, DATABASE_URL, SSL_*)
```

## Migraciones

```bash
cd sipi_core
alembic upgrade head        # aplicar migraciones
alembic revision --autogenerate -m "descripcion"
```

> Las extensiones PostGIS se inicializan vía `db/alembic/init_postgis.sql`.

## Uso como dependencia

Una vez publicado/instalable, `sipi-api` y demás componentes importan los
modelos desde aquí (`from sipi_core.models import ...`) en lugar de mantener
copias propias.
