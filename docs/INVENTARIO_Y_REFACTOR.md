# Inventario de estado real y propuesta de refactorización total

Documento basado en lectura directa del código (no en supuestos). Objetivo:
dejar el monorepo **coherente y sin nada a medio terminar**. Primero el
inventario con evidencia; después la propuesta y su secuenciación por fases.

> Nota de método: lo marcado como "roto" es análisis **estático** (imports,
> wiring); no se ha ejecutado nada contra una base de datos. Donde infiero, lo
> digo.

---

## 1. Inventario de estado real

### packages/sipi-core
- Modelos ORM del dominio (**63 clases**), esquemas `app`/`gis`, mixins propios,
  `Base` con `MetaData(schema="app")`.
- Es el modelo **canónico y más evolucionado** (incluye ya el nuevo `Expediente`).
- **Pero no lo consume nadie**: ni la API, ni etl, ni survey lo importan.

### apps/api
- Mantiene **sus propios modelos** en `app/db/models/` (**51 clases**), esquema
  `sipi` (`DB_SCHEMA`, `app/db/base.py`). Duplicado del dominio de sipi-core.
- GraphQL: hay un **generador propio** (`app/graphql/schema.py::create_schema`)
  que es lo **realmente cableado** (`app/graphql/app.py`), y produce
  `getX`/`listXs`/`searchXs` + `createX`/`deleteX`.
- A la vez, `requirements` incluye **`strawberry-sqlalchemy-mapper~=0.8.0`** y
  hay un `test_mapper.py`: la API está **a medio camino** entre el generador
  propio y un auto-mapper.
- Alembic crea el esquema con `Base.metadata.create_all(checkfirst=True)` sobre
  el metadata de `app.db` (esquema `sipi`).

### apps/frontend
- Vue 3 + Pinia + Apollo + Leaflet. Apollo apunta a
  **`http://localhost:4000/graphql` hardcodeado** (`src/main.js`).
- Varios módulos corren sobre **mocks** (`useInmueble.js`, `usuarios`,
  documentos…), no contra la API.
- Las queries GraphQL están escritas en **estilo filtro** (`x(filter:{...})`,
  `createX(data:)`, `deleteXs(filter:)`) — que **no coincide** con el generador
  vivo de la API (`listXs`/`getX`). El frontend va por delante del backend.

### services/etl
- Contiene: el OSM/Wikidata reubicado (`modules/osmwikidata/extract|load`), el
  cargador de censo CEE (`modules/census`), **mi módulo de fusión**
  (`modules/fusion`), y scripts (`load_census`, `populate_master_data`,
  `seed_inmuebles_fusion`, **`refactor_survey.py`**).
- `db/connection.py` ofrece **psycopg2 crudo** y **SQLAlchemy ORM**; cadena por
  defecto `postgresql://sipi:sipi@db:5432/sipi` (esquema `sipi`).
- `db/models/` son los **mismos stubs vacíos** que survey.
- Sin servidor; se opera por **scripts CLI**.
- `refactor_survey.py` es un **codemod regex a medio hacer** que reescribe
  `from app.db` → `from sipi_core.db`: prueba de una migración **iniciada y no
  terminada**.

### services/survey
- Código **sustancial y real**: geocoders (`NominatimGeocoder`,
  `PhotonGeocoder`, `HybridGeocoder` con caché), `RegionBuilder`/`RegionMonitor`
  (con `_score_inmueble`), `MultiPortalOrchestrator` async, `ETLEventBus`
  (pub/sub), `DatasetDiffer` (pandas), `ReligiousPropertyScorer`
  (`modules/portals/transform`), scraping Idealista (sync/async), scheduler.
- **Pero incoherente / a medio migrar:**
  - El pipeline cableado en `main.py` (`OSMWikidataPipeline`, en
    `core/pipeline.py`) **tiene imports rotos**: importa
    `modules.portals.osmwikidata.*`, que **ya no existe** (ese código se movió a
    `services/etl/src/modules/osmwikidata/`).
  - Hay **dos** pipelines: `core/pipeline.py` (OSM/WD, roto) y
    `orchestation/pipeline.py` (portales, async).
  - Modelos ORM (`db/models/`) **vacíos (0 líneas)**: persiste en **SQL crudo**
    sobre esquemas propios (`osmwikidata`, `portals`, `matching`, `osm_staging`,
    `notifications`).
  - Sus "notificaciones" son de **monitorización del ETL** (tabla
    `notifications.events`), no notificaciones de dominio al usuario.
  - Inconsistencias de nomenclatura (`transform/Idealista` vs
    `extract/idealista`).

### Raíz / composición
- `pyproject.toml`: workspace `uv` con **un solo miembro** (`sipi-core`). El
  comentario declara que "api/etl/survey dependen de sipi-core", pero **ninguno
  lo importa** todavía.
- `docker-compose` **por componente** (api, frontend, survey, sipi-core); **no
  hay orquestación raíz** única.

---

## 2. Problemas de fondo

1. **Triplicación del modelo.** El dominio existe en sipi-core (63, canónico,
   sin usar), en la API (51, duplicado, en uso) y como stubs vacíos en
   etl/survey. Fuente histórica de bugs.
2. **Fragmentación de esquemas.** `app`/`gis` (sipi-core) frente a `sipi` (API,
   survey, etl) y los ad-hoc del descubrimiento (`osmwikidata`, `portals`,
   `matching`, `osm_staging`, `notifications`). El canónico no es el que corre.
3. **Descubrimiento a medio migrar (survey → etl).** Mucho código real, pero
   wiring roto, stubs vacíos, SQL crudo y un codemod sin terminar. Dos pipelines.
4. **GraphQL en transición + frontend adelantado + mocks.** Generador propio vs
   `strawberry-sqlalchemy-mapper`; el frontend asume el estilo filtro y a la vez
   tira de mocks y de un endpoint hardcodeado.
5. **Sin composición unificada** ni dependencia efectiva de sipi-core.
6. El nuevo `Expediente` está bien situado (en sipi-core) pero **desconectado**
   de lo que corre, porque la consolidación está pendiente.

---

## 3. Propuesta de refactorización total

Principio: **una sola fuente de verdad por responsabilidad**, y cada fase
termina en un estado coherente y funcionando (nada a medio).

### Decisiones de destino
- **Modelos:** `sipi-core` es la **única** definición (esquemas `app`/`gis`). La
  API, etl y survey lo **importan**; se borran los modelos de la API y los stubs
  de etl/survey.
- **Esquema:** unificar en `app`/`gis`; un único esquema `staging` (definido en
  código, no ad-hoc) para datos crudos de descubrimiento. Se retira `sipi` y los
  esquemas sueltos. **Regenerar la línea base de Alembic** (una sola, en
  sipi-core o en la API consumiendo sipi-core).
- **GraphQL:** elegir **una** vía — adoptar el auto-mapper (estilo filtro que el
  frontend ya espera) y **eliminar el generador propio**. Un solo contrato.
- **Descubrimiento:** **un solo servicio** (fusionar `survey` + `etl` en
  `services/discovery`), que **importe sipi-core** y persista vía ORM. Se
  conservan los subsistemas reales de survey (geocoders, `RegionMonitor`,
  `MultiPortalOrchestrator`, `ETLEventBus`, `DatasetDiffer`,
  `ReligiousPropertyScorer`) + el módulo de fusión; se **elimina** el pipeline
  roto y se deja **un entrypoint** + scheduler.
- **Hallazgos → dominio:** las detecciones se escriben como **`Expediente`
  (estado "propuesto")**, no en tablas ad-hoc `portals.detecciones`.
- **Notificaciones:** separar responsabilidades — módulo **comunicación** del
  dominio para notificaciones al usuario (hallazgos); el `ETLEventBus`/eventos de
  survey quedan **solo** como monitorización del ETL.
- **Frontend:** quitar mocks, endpoint por **variable de entorno** (no
  `localhost:4000` fijo), y alinear las queries al contrato elegido.
- **Composición:** un **docker-compose raíz** (db + api + frontend +
  discovery), configuración por entorno, y `uv` con todos los miembros que
  dependan de sipi-core.
- **Extracción (destino mayor):** migrar los extractores directos (scraping,
  Overpass, WDQS) a **suscripciones a datasets de OpenDataManager**.

### Estructura objetivo
```
packages/sipi-core         # modelos + dominio (única verdad), esquema app/gis
apps/api                   # GraphQL (auto-mapper) sobre sipi-core
apps/frontend              # Vue, sin mocks, endpoint por env, contrato único
services/discovery         # survey+etl fusionados; importa sipi-core; 1 entrypoint
  ├─ extract/ (osm, wikidata, portales → luego OpenDataManager)
  ├─ geo/      (geocoders, regiones)
  ├─ fusion/   (normalize, matcher, geo-blocking, scorer religioso)
  └─ sink/     (escribe Expediente "propuesto" + staging)
docker-compose.yml         # orquestación raíz
```

---

## 4. Secuenciación por fases (cada una deja el repo coherente)

**Fase 0 — Congelar decisiones.** Esquema destino `app`/`gis`; API = auto-mapper;
descubrimiento = un servicio. Sin código aún.

**Fase 1 — Modelo único.** La API importa `sipi-core`; se borran sus modelos y
los stubs de etl/survey; baseline de Alembic regenerada sobre `app`/`gis`;
script de migración de datos `sipi` → `app`/`gis`. *Validar contra BD.* Fin de
fase: la API arranca sobre sipi-core.

**Fase 2 — GraphQL coherente.** Cablear el auto-mapper, borrar el generador
propio, regenerar el esquema. Frontend: fuera mocks, endpoint por env, alinear
queries. *Validar de punta a punta* en 2-3 entidades (incl. `Expediente`).

**Fase 3 — Un solo descubrimiento.** Crear `services/discovery` importando
sipi-core; portar los subsistemas reales de survey + la fusión; eliminar el
pipeline roto y el codemod; un entrypoint + scheduler. Las detecciones escriben
`Expediente` "propuesto" en el dominio.

**Fase 4 — Notificaciones y validación.** Módulo comunicación del dominio para
hallazgos; cola de validación del frontend (ya existe) conectada a `Expediente`;
ratificación como transacción RBAC que actualiza `estado_actual`.

**Fase 5 — Composición y limpieza.** docker-compose raíz; `uv` con todos los
miembros; borrar código muerto y esquemas retirados; normalizar nomenclatura.

**Fase 6 (destino mayor) — OpenDataManager.** Sustituir los extractores directos
por suscripciones a datasets de OpenDataManager.

---

## 5. Realidad de ejecución

Las fases 1-2 cambian esquema y contrato: **requieren una base de datos para
validar** y no deben hacerse a ciegas. Pueden ejecutarse en ramas, una por fase,
con validación real en cada una. El nuevo `Expediente` ya está alineado con este
destino (vive en sipi-core); encaja sin retrabajo cuando se ejecute la Fase 1.
