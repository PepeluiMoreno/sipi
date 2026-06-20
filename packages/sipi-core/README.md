# sipi-core

Núcleo de dominio de SIPI: **única fuente de verdad** de los modelos (SQLAlchemy),
mixins y acceso a datos. Lo consumen las dos apps (`apps/sipi`, `apps/sipi-survey`) y
los servicios de descubrimiento, en lugar de duplicarlos.

## Layout (src/)

```
packages/sipi-core/
├── pyproject.toml          name = "sipi-core"  (distribución)
└── src/sipi_core/          paquete importable: import sipi_core
    ├── modules/<dominio>/   modelos agrupados por dominio (estilo SIGA)
    ├── models/__init__.py   FACHADA — re-exporta todos los modelos
    ├── mixins/              UUIDPKMixin, AuditMixin, Identificacion/Contacto/…
    └── db/                  registry (Base, APP_SCHEMA), metadata, sessions, alembic
```

`import sipi_core.models` registra todas las tablas en `Base.metadata` (la API
introspecta esa fachada para autogenerar el esquema GraphQL).

## Dominios (`modules/`)

`geografia`, `catalogos`, `actores`, `entidades_religiosas`, `inmuebles`,
`transmisiones`, `intervenciones`, `documentos`, `expedientes`, `discovery`,
`notificaciones`, `usuarios`, y los módulos transversales **`acceso`** (RBAC por
transacción), **`comunicacion`** (notificaciones de dominio + router ODMGR) y
**`configuracion`** (parámetros tipados por ámbito). Ver
[../../docs/DISENO_MODULOS_NUEVOS.md](../../docs/DISENO_MODULOS_NUEVOS.md).

## Esquema (opción B)

Todo en el esquema `sipi`, configurable por entorno. `db/registry.py`:

```python
APP_SCHEMA     = os.getenv("APP_SCHEMA", "app")    # en SIPI: sipi
GIS_SCHEMA     = os.getenv("GIS_SCHEMA", "gis")    # en SIPI: sipi
DEFAULT_SCHEMA = os.getenv("DEFAULT_SCHEMA", APP_SCHEMA)
```

En desarrollo/producción se exporta `APP_SCHEMA=GIS_SCHEMA=DEFAULT_SCHEMA=DEFINED_SCHEMAS=sipi`.

## Stack

Python ≥3.10 · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL + PostGIS · GeoAlchemy2 ·
Strawberry (tipos GraphQL).

## Instalación y migraciones

```bash
pip install -e .                       # editable (src layout)
cd src/sipi_core
export DATABASE_URL=postgresql://sipi:<pwd>@localhost:5433/sipi
export DEFINED_SCHEMAS=sipi APP_SCHEMA=sipi GIS_SCHEMA=sipi DEFAULT_SCHEMA=sipi
alembic upgrade head
alembic current
```

## Seeds (RBAC / configuración / comunicación)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import sipi_core.models  # carga la fachada
from sipi_core.modules.acceso.services.seed import seed as seed_acceso
from sipi_core.modules.configuracion.services.seed import seed as seed_config
from sipi_core.modules.comunicacion.services.seed import seed as seed_comu

with Session(create_engine(DATABASE_URL)) as s:
    seed_acceso(s); seed_config(s); seed_comu(s)
```

> **Nota de integridad**: el `MetaData` aún no tiene `naming_convention`, por lo que
> `alembic check` reporta FKs como "drift" (falso positivo). Ver
> [src/sipi_core/docs/INTEGRIDAD_DIFERIDA_FASE1.md](src/sipi_core/docs/INTEGRIDAD_DIFERIDA_FASE1.md).
