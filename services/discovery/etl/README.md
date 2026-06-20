# services/discovery/etl

Procesos **ETL** de SIPI: extrae y carga datos de fuentes abiertas para construir y
enriquecer el inventario. Persiste sobre el modelo único de `packages/sipi-core`
(loaders ORM), esquema `sipi` (opción B). Forma parte del servicio de descubrimiento.

## Estructura

```
load/                Loaders ORM sobre sipi_core (cargar_*, enriquecer_*) por DATABASE_URL
extract/             Extractores (OSM/Overpass, Wikidata, INE, registradores…)
transform/           Transformaciones (DIR3, INE nomenclátor, registros…)
src/modules/
├── osmwikidata/      extract (overpass/WDQS) + load de extensiones de inmueble
└── census/           loader + mapper de censo (CEE)
tools/                utilidades
fuentes.env           URLs de fuentes (no secretos)
```

## Puesta en marcha

```bash
pip install -e ../../../packages/sipi-core
export DATABASE_URL=postgresql://sipi:<pwd>@localhost:5433/sipi
export APP_SCHEMA=sipi GIS_SCHEMA=sipi DEFAULT_SCHEMA=sipi DEFINED_SCHEMAS=sipi
python load/cargar_entidades_religiosas.py     # ejemplo de loader ORM
```

## Consumo de ODM (suscripción por colección)

SIPI consume los recursos versionados de **OpenDataManager** por webhook
(`app_webhook.py`) en vez de re-extraer. El enrutado es **por colección**
(`COLLECTION_MAP`) con `RESOURCE_MAP` de respaldo: un recurso nuevo en una
colección a la que SIPI está suscrito se procesa **sin tocar SIPI**. Contrato y
configuración en **[docs/CONSUMO_ODM.md](docs/CONSUMO_ODM.md)**.

## Notas

- Los modelos de dominio viven en `sipi-core`; aquí no se duplican (los stubs vacíos
  `db/models/*` se eliminaron en la consolidación).
- Consultas Overpass: `src/modules/osmwikidata/extract/queries/README.md`.
- `.env`, `data/`, `logs/` no se versionan.
