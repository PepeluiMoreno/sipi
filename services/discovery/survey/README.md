# services/discovery/survey

Subsistema de **descubrimiento** del patrimonio: descubre, extrae, geolocaliza y
coteja inmuebles candidatos a partir de fuentes abiertas y portales (Idealista,
Fotocasa, OSM/Wikidata). Es uno de los "dispositivos de vigilancia" que controla la
app **`apps/sipi-survey`**; persiste sobre el modelo único de `packages/sipi-core`.

> Parte de un monorepo. El ETL de carga vive en `services/discovery/etl`, la
> sincronización OSM en `services/discovery/osm`, los modelos en
> `packages/sipi-core` y las apps en `apps/`.

## Qué aporta

- **Extracción de portales** (`src/modules/portals/`): clientes/scraping (Idealista…)
  síncronos y asíncronos, con scoring y matching configurables.
- **Geo** (`src/core/geo/`): geocoding híbrido (Nominatim/Photon) con caché, y
  construcción/monitorización de regiones.
- **Pipeline + scheduler**: ejecución puntual o como demonio.
- **Eventos/detecciones** (`src/api/etl_detections.py`): las detecciones se escriben
  hacia el dominio (`sipi_core.models.discovery` → y, materializadas, como `Expediente`
  propuesto para que la app SIPI las valide).

## Integración con el dominio

Las detecciones relevantes se convierten en `Expediente` (estado `propuesto`, con
`certeza`/`confianza` del scoring). El disparo del pipeline puede venir de un evento
ODMGR a través del `odmgr_router` de `modules/comunicacion` (ver §2bis del diseño).

## Stack

Python 3 · SQLAlchemy/sipi-core · PostgreSQL/PostGIS **local** (esquema `sipi`) ·
Redis · Overpass (OSM) · WDQS (Wikidata).

> `.env` no se versiona. Esquema único `sipi` (opción B). *Nota: este README y el
> código pueden contener todavía referencias del estado pre-monorepo; la fusión
> lógica de discovery (extract/geo/fusion/sink) es una tarea pendiente.*
