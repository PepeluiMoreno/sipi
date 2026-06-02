# SIPI-Survey

Orquestador de **ETL y monitorización** del ecosistema SIPI (Sistema de
Información del Patrimonio Inmatriculado). Descubre, extrae, geolocaliza y
coteja información de inmuebles candidatos a partir de fuentes abiertas y
portales externos, alimentando la base de datos compartida.

> Parte del ETL inicial se ha extraído al repositorio independiente
> [`sipi-etl`](https://github.com/PepeluiMoreno/sipi-etl). Los modelos de
> dominio viven en [`sipi-core`](https://github.com/PepeluiMoreno/sipi-core)
> y la API GraphQL en [`sipi-api`](https://github.com/PepeluiMoreno/sipi-api).

## Qué hace

- **Extracción de portales** (`src/modules/portals/`): scraping/cliente para
  portales inmobiliarios (Idealista) con extractores síncronos y asíncronos,
  selectores, scoring y matching configurables por portal.
- **OSM + Wikidata** (`src/core/geo/`): construcción y monitorización de
  regiones, geocoding híbrido y caché en Redis.
- **Pipeline y scheduler** (`src/core/pipeline.py`, `src/core/scheduler.py`):
  ejecución puntual o como demonio en intervalos configurables.
- **Eventos y notificaciones** (`src/core/etl_event_system.py`,
  `src/core/notification_service.py`, `src/api/notifications.py`): alertas vía
  Slack/email y endpoints FastAPI de monitorización del ETL.

## Stack

Python 3 · FastAPI · SQLAlchemy · PostgreSQL/PostGIS (Supabase) · Redis ·
Overpass (OSM) · WDQS (Wikidata) · Docker.

## Puesta en marcha

```bash
# 1. Variables de entorno
cp .env.example .env   # rellenar los valores marcados como CHANGEME

# 2. Dependencias
pip install -r requirements.txt

# 3a. Ejecución puntual del pipeline
python -m src.main --country ES

# 3b. Modo demonio (re-ejecuta cada --interval horas)
python -m src.main --daemon --interval 24

# 3c. Solo API de notificaciones/monitorización
python -m src.main --api
```

Con Docker: `docker compose up` (incluye perfil Jupyter en `Dockerfile.jupyter`).

## Estructura

```
src/
├── main.py                 # CLI: pipeline puntual | --daemon | --api
├── api/                    # endpoints FastAPI (notificaciones, monitor ETL, regiones)
├── core/
│   ├── pipeline.py         # OSMWikidataPipeline
│   ├── scheduler.py        # ETLScheduler
│   ├── differ.py           # detección de cambios
│   ├── etl_event_system.py # bus de eventos del ETL
│   ├── notification_service.py
│   └── geo/                # geocoding híbrido, regiones, caché Redis
├── modules/portals/        # extracción/carga por portal (Idealista, ...)
└── db/                     # modelos y conexión

sql/                        # esquemas SQL (matching, notifications, regions, portals, osm)
scripts/run_daily_scraping.sh
```

## Notas

- `.env` **no** se versiona (contiene credenciales). Usa `.env.example`.
- Los esquemas SQL de referencia están en `sql/`.
