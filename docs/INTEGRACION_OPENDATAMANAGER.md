# Integración con OpenDataManager — datos de referencia y procesos de vigilancia

Plan de integración entre SIPI y OpenDataManager (ODM,
github.com/PepeluiMoreno/OpenDataManager). Basado en lectura directa de ambos
repos. **No modifica ODM**: los cambios en ODM se proponen aquí y se ejecutan con
supervisión.

---

## 1. Principio

> SIPI es dueño únicamente de **`Inmueble` + sus `Expediente`s** (el ciclo de
> vida). **Todo el dato de referencia se alimenta de ODM**: geografía, actores y
> las fuentes de eventos. Las tablas maestras de SIPI son **proyecciones/cachés**
> de datasets de ODM, mantenidas frescas por **procesos de vigilancia**.

ODM es la capa de adquisición: va a por el dato público y lo ofrece a las
aplicaciones. Si una fuente falta o está incompleta en ODM, **se programa en ODM**
(con supervisión) — SIPI no scrapea por su cuenta.

---

## 2. Mapeo SIPI ↔ ODM (verificado en `seed_resources.py`)

### Geografía
| Entidad SIPI (`app`) | Resource/Publisher ODM | Fuente | Estado |
|---|---|---|---|
| `ComunidadAutonoma` | INE → `geo_comunidades` | INE | resource sembrado |
| `Provincia` | INE → `geo_provincias` | INE | resource sembrado |
| `Municipio` | INE → `geo_municipios` (codmun) | INE | resource sembrado |
| **`Pedania`/`EntidadPoblacion` (FALTA en SIPI)** | Geonames – Entidades de Población; publisher Min. Hacienda – Entidades Locales | Geonames / MINHAC | resource Geonames sembrado |

### Actores
| Actor SIPI | Resource/Publisher ODM | Fuente | Estado |
|---|---|---|---|
| `Administracion` (jerárquica) | DIR3 – Unidades Orgánicas → `dir3_unidades` | datos.gob/DIR3 | resource sembrado |
| `Notaria` | Notarías – Guía Notarial → `notarios` | Consejo Gral. del Notariado | resource sembrado |
| `RegistroPropiedad` | publisher CORPME (Colegio de Registradores) | registradores.org | **solo publisher → falta resource** |
| `Diocesis`/entidad religiosa | OSM (`operator`) + Wikidata (`P127`) | OSM/Wikidata | fetcher OSM existe |
| `AgenciaInmobiliaria` | portales inmobiliarios | Idealista/… | **en `services/survey`, no en ODM** |

### Fuentes de eventos (→ `Expediente`)
| Tipo de expediente | Resource/Publisher ODM | Fuente | Estado |
|---|---|---|---|
| `subvencion` | publisher BDNS | infosubvenciones.es (API REST) | **solo publisher → falta resource** |
| `actuacion`/`enajenacion` (contratos) | publisher PLACSP | contrataciondelestado.es | **solo publisher → falta resource** |
| geolocalización/uso (enriquecimiento) | Catastro – Parcelas (INSPIRE WFS) | Dir. Gral. del Catastro | resource sembrado (Sevilla) |
| `deteccion`/`enajenacion` | OSM/Wikidata + portales | OSM/Wikidata/Idealista | OSM sí; portales en survey |

---

## 3. Qué aporta ODM ya (reutilizable, verificado)

- **Fetchers genéricos** (`app/fetchers/`): REST, REST paginado, HTML (form,
  paginado, searchloop, tree), SOAP, WFS/WMS/OGC, ATOM, OSM, PowerBI, XBRL, PDF,
  ficheros comprimidos. Cubre casi cualquier fuente pública.
- **`Resource`** con campo `schedule` (crontab) y `active`; ejecutado por
  `FetcherManager.run(session, resource_id)` → produce `Dataset` y registra
  `ResourceExecution`.
- **Scheduler** (`app/scheduler.py`, `app/services/scheduler_service.py`):
  APScheduler con jobstore en PostgreSQL; registra un cron-job por resource
  activo con `schedule`. **Refresco programado: ya hecho.**
- **A demanda**: mutations `executeResource(id)` y `executeAllResources()`.
- **Suscripciones**: `DatasetSubscription` (Application↔Resource) con
  *version pinning* (`pinned_version`, `auto_upgrade`), `current_version` y
  `notified_at` (aviso de versión nueva).
- **Datasets derivados**: `DerivedDatasetConfig` (p. ej. de BDNS concesiones
  extraer catálogo de beneficiarios por NIF).
- **API de datos dinámica** (`app/graphql_data`): construye un schema GraphQL con
  un query por dataset; es por donde un suscriptor (SIPI) **lee** el dato.
- ODM tiene además **frontend propio** (Vue).

---

## 4. Procesos de vigilancia

Un proceso de vigilancia por dataset que SIPI necesita. Cada uno:

1. **Suscripción**: SIPI (como `Application` en ODM) crea una `DatasetSubscription`
   al `Resource` (con *version pinning*).
2. **Disparo del refresco**, dos vías:
   - **Schedule**: `Resource.schedule` (crontab) → el scheduler de ODM ejecuta el
     fetch periódicamente.
   - **A demanda**: el usuario lo lanza desde el **UI del frontend de SIPI**, que
     llama a `executeResource(id)` de ODM.
3. **Consumo en SIPI**: tras el refresco (o al recibir `notified_at` de versión
   nueva), SIPI lee el dataset por `graphql_data` y:
   - si es **referencia** (geo/actores) → *upsert* en la tabla maestra
     (proyección/caché);
   - si es **fuente de evento** (BDNS/PLACSP/portales/OSM) → entra al
     descubrimiento (normalización + fusión + scoring) → `Expediente` "propuesto"
     → notificación + cola de validación.

---

## 5. Huecos a programar en ODM (con supervisión)

Propuestas, **no ejecutadas**:

1. **Resources que hoy son solo publisher**: definir el `Resource` concreto de
   **BDNS** (API REST de infosubvenciones), **PLACSP** (contratación) y **CORPME**
   (registros). Usan fetchers ya existentes (REST/HTML/SOAP).
2. **Portales inmobiliarios**: migrar el scraping de Idealista que hoy vive en
   `services/survey` a un **fetcher/resource de ODM** (HTML paginado/searchloop),
   para que sea compartido y servido — coherente con "ODM va a por el dato y lo
   ofrece".
3. **Pedanías**: rematar el resource de **Geonames – Entidades de Población** /
   Min. Hacienda – Entidades Locales como dataset de referencia sub-municipal.
4. **OSM/Wikidata religioso**: verificar que el fetcher OSM cubre la consulta de
   lugares de culto católicos y el enriquecimiento Wikidata que usa la fusión.

Regla: cualquier cambio en ODM se propone y se ejecuta **con tu supervisión**.

---

## 6. Lo que SIPI construye (su lado)

1. Registrarse como **Application** en ODM y crear las suscripciones.
2. Un **consumidor** que lee de `graphql_data` y, según el dataset, hace *upsert*
   de maestros o alimenta el descubrimiento.
3. **UI de vigilancia** en el frontend: lista de procesos (resources suscritos),
   último refresco/versión, botón de **refresco a demanda** (`executeResource`) y
   edición del **schedule** (crontab).
4. **UI de parámetros** del descubrimiento (rama `feat/ui-parametros-descubrimiento`,
   ya iniciada con `DiscoveryConfig.from_mapping`): editar ponderaciones/umbrales.
5. Añadir el modelo **`Pedania`/`EntidadPoblacion`** y enchufarlo al
   reverse-geocoding de la fusión (hoy `MunicipioIndex` resuelve a municipio;
   con pedanías afina y reduce el rescate por proximidad — relevante para ermitas
   y capillas rurales).

---

## 7. Consecuencias

- **`services/etl/scripts/populate_master_data.py` queda superado**: hoy siembra
  CCAA/provincias/municipios/tipos desde un CSV; ese rol pasa a la vigilancia de
  los resources INE/DIR3/CGN/CORPME de ODM.
- Las **tablas maestras** de SIPI dejan de mantenerse a mano: son proyecciones de
  ODM, refrescadas por vigilancia.
- Encaja con la refactorización (ver `docs/INVENTARIO_Y_REFACTOR.md`): un solo
  servicio de descubrimiento que consume ODM y escribe `Expediente`.

---

## 8. Estado / honestidad

- Esto es **plan**, no está cableado. ODM tiene la plataforma (fetchers,
  scheduler, suscripciones, API de datos) y los publishers/resources sembrados
  para INE, DIR3, CGN (notarías), Catastro, Geonames, y publishers para CORPME,
  BDNS, PLACSP.
- Verificado por lectura de `seed_resources.py`, `app/models.py`,
  `app/services/scheduler_service.py`, `app/graphql/mutations.py`,
  `app/graphql_data/`. Lo marcado como "falta resource" es lo que vi como
  *publisher sin resource concreto* — **a confirmar** al detalle antes de
  programarlo.
- Ningún cambio en ODM se hace sin tu supervisión.
