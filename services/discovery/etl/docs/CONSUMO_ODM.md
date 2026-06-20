# Consumo de OpenDataManager (ODM) — suscripción por colección (slug)

SIPI **no extrae** las fuentes que ya cosecha ODM: las **consume** como recursos
versionados de ODM y los resuelve sobre `sipi-core`. Este documento describe el
contrato de consumo, desacoplado **por colección** mediante un identificador
estable (`slug`), y la **preparación del ETL como solicitud de suscripción**.

## Flujo

1. ODM publica un dataset → `POST /odm/webhook` (firmado HMAC-SHA256 en
   `X-ODM-Signature`). Lo recibe `services/discovery/etl/app_webhook.py`.
2. SIPI verifica la firma y **enruta**: resuelve `(dominio, fuente)` y, si aplica,
   llama `poblar_recurso(...)`, que descarga el JSONL del último dataset
   (`/api/datasets/{id}/data.jsonl`) y lo resuelve sobre `sipi-core` por lotes.

## Enrutado: por COLECCIÓN (slug) + RESOURCE_MAP (respaldo)

El enrutado va por el **`slug` de colección** — la **clave estable** de ODM, *no*
el nombre de display (editable, frágil) ni el UUID (cambia entre entornos):

- El webhook incluye **`collection_slugs`** (claves estables) y `collections`
  (nombres, solo display).
- `src/odm/config.py::resolver_destino(resource_name, collection_slugs, publisher, collections)`
  resuelve `(dominio, fuente)` con esta prioridad:
  1. **`RESOURCE_MAP[resource_name]`** — override fino (fuente exacta de recursos
     concretos). Gana sobre la colección.
  2. **`COLLECTION_MAP[slug]`** — la colección fija el **dominio** (y la **fuente**
     si es uniforme; si no, se deriva del publisher).
  3. *Compat*: si el emisor es antiguo y no manda `collection_slugs`, se hace
     `slugify` de los nombres de `collections`.
- Si no casa ni recurso ni colección suscrita → se ignora.

**Consecuencia**: cuando ODM añade un recurso nuevo a una colección a la que SIPI
está suscrito, SIPI lo procesa **sin tocar código**. Y como el enrutado es por
slug, **renombrar** la colección en ODM no rompe nada.

### `COLLECTION_MAP` (slug de colección ODM → dominio SIPI)

Las colecciones en ODM son **neutrales y compartibles** (sin prefijo de app):
varias aplicaciones pueden suscribirse a la misma.

| slug de colección en ODM | nombre sugerido | dominio | fuente |
|---|---|---|---|
| `administraciones-dir3` | Administraciones (DIR3) | administracion | DIR3 |
| `diocesis` | Diócesis | diocesis | CEE |
| `entidades-religiosas` | Entidades religiosas | entidad_religiosa | por recurso |
| `notarias` | Notarías | notaria | CGN |
| `registros-de-la-propiedad` | Registros de la Propiedad | registro_propiedad | CORPME |
| `inmuebles` | Inmuebles | inmueble | por recurso (OSM/IAPH/CEE) |

`config.SLUGS_NECESARIOS` = las claves de esta tabla (lo que SIPI declara). El
`slug` lo genera ODM al crear la colección (slugify del nombre); es estable y no
cambia al renombrar.

`RESOURCE_MAP` se mantiene como **respaldo/override** (fuente precisa por recurso:
RER, CEE_PARROQUIA, CONFER, DIR3_PUENTE, etc.).

## Preparación del ETL = solicitud de suscripción (auto-servicio M2M)

La "preparación" del consumidor **no es configuración manual en ODM**: es una
**solicitud de suscripción** que SIPI emite al arrancar, autenticándose con su
token de aplicación (Bearer, §12 de ODM).

`app_webhook.py` lo hace en el `startup` (best-effort, no bloquea el arranque):

```python
ODMClient().bootstrap_suscripciones()   # usa config.SLUGS_NECESARIOS
```

que ejecuta, contra `/graphql` de ODM con `Authorization: Bearer <ODM_APP_TOKEN>`:

1. **`requestSubscriptions(collectionSlugs: [...])`** — idempotente: la aplicación
   autenticada se suscribe a las colecciones que necesita, por slug. Slugs que aún
   no existen en ODM se ignoran (no crean nada).
2. **`mySubscriptions`** — *readiness*: por cada suscripción dice si está
   **satisfecha** (tiene dataset publicado), su versión y la URL del último
   dataset. SIPI registra en log las colecciones que faltan o están vacías.

Así SIPI comprueba al arrancar que **tiene sus recursos satisfechos** para el ETL.

### Variables de entorno

| Variable | Para qué |
|---|---|
| `ODM_BASE_URL` | base de ODM (p. ej. `https://<host-odm>`) |
| `ODM_WEBHOOK_SECRET` | verificación de la firma del webhook (= secret del Subscriber en ODM) |
| `ODM_APP_TOKEN` | token Bearer de la aplicación; necesario para `bootstrap_suscripciones` |

### Lo único manual en ODM (una vez)

1. Dar de alta a **SIPI** como *Subscriber*/aplicación en ODM y emitir su **token
   Bearer** (→ `ODM_APP_TOKEN`) y su **webhook_secret** (→ `ODM_WEBHOOK_SECRET`),
   con `webhook_url = https://<host-sipi>/odm/webhook`.
2. Crear las **colecciones** de la tabla (nombres neutrales) y meterles los
   recursos. La **suscripción la pide SIPI sola** (paso anterior).

## Contrato del payload (ODM → SIPI)

```jsonc
{
  "event": "dataset.published",
  "collections": ["Administraciones (DIR3)", ...],     // nombres (display)
  "collection_slugs": ["administraciones-dir3", ...],  // ← enrutado (clave estable)
  "dataset": {
    "id": "...", "resource_id": "...", "resource_name": "...",
    "publisher": "...", "version": "1.2.3", "version_type": "minor",
    "record_count": 123, "checksum": "..."
  },
  "download_urls": { "data": "/api/datasets/{id}/data.jsonl", ... }
}
```

Firma: `hmac_sha256(ODM_WEBHOOK_SECRET, json.dumps(payload, sort_keys=True))` en
`X-ODM-Signature`.

## Ficheros

- `app_webhook.py` — receptor del webhook (enruta por slug) + `startup` que llama
  a `bootstrap_suscripciones`.
- `src/odm/config.py` — `COLLECTION_MAP` (por slug), `SLUGS_NECESARIOS`,
  `RESOURCE_MAP`, `resolver_destino`.
- `src/odm/client.py` — `request_subscriptions`, `my_subscriptions`,
  `bootstrap_suscripciones`, descarga JSONL.
- `src/odm/pipeline.py` — `poblar_recurso(..., destino=(dominio,fuente))`.
- `src/odm/resolvers.py` — resolvers por dominio (upsert sobre sipi-core).

## Pendiente / evolución

- **Nivel "Máximo"**: que los recursos ODM declaren `dominio`/`fuente` como
  metadato (params/tags) y el payload los traiga → SIPI sin mapa alguno.
- Alinear `modules/comunicacion/services/odmgr_router` (política notify/trigger)
  para que también pueda enrutar por slug de colección, no solo por `resource_name`.
