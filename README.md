# sipi-etl

Procesos **ETL** del ecosistema SIPI (Sistema de Información del Patrimonio
Inmatriculado, proyecto de Europa Laica). Extrae y carga datos de fuentes
abiertas para construir y enriquecer el inventario de inmuebles candidatos.

> Extraído del repositorio [`sipi-survey`](https://github.com/PepeluiMoreno/sipi-survey).
> Los modelos de dominio viven en [`sipi-core`](https://github.com/PepeluiMoreno/sipi-core)
> y la API GraphQL en [`sipi-api`](https://github.com/PepeluiMoreno/sipi-api).

## Módulos

- **`src/modules/osmwikidata/`** — extracción desde OpenStreetMap (Overpass) y
  Wikidata, con consultas Overpass para iglesias (`churches.overpassql`,
  `national_churches.overpassql`) y carga de extensiones de inmuebles
  (`load/inmuebles_ext.py`).
- **`src/modules/census/`** — carga y mapeo de datos de censo (`loader.py`,
  `mapper.py`).
- **`src/db/models/`** — modelos de apoyo del ETL: `osmwikidata`, `regions`,
  `matching`, `idealista`, `notification`.

## Stack

Python 3 · asyncpg · SQLAlchemy · Redis · Selenium + BeautifulSoup/lxml ·
Overpass (OSM) · WDQS (Wikidata).

## Puesta en marcha

```bash
# Variables de entorno (NO se versionan)
cp .env.example .env 2>/dev/null || true   # crear .env con las credenciales

# Dependencias
pip install -r requirements.txt

# Cargas / scripts
python scripts/load_census.py
python scripts/populate_master_data.py
```

## Estructura

```
src/
├── config/        # settings y conexión a base de datos
├── db/            # conexión y modelos de apoyo del ETL
└── modules/
    ├── osmwikidata/   # extract (osm_client, wikidata_client, queries) + load
    └── census/        # loader y mapper de censo
scripts/           # load_census, populate_master_data, refactor_survey
```

## Notas

- `.env`, `data/` y `logs/` no se versionan (ver `.gitignore`).
- Las consultas Overpass están documentadas en
  `src/modules/osmwikidata/extract/queries/README.md`.
