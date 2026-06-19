# Consumo de OpenDataManager (ODM) — suscripción por colección

SIPI **no extrae** las fuentes que ya cosecha ODM: las **consume** como recursos
versionados de ODM y los resuelve sobre `sipi-core`. Este documento describe el
contrato de consumo tras desacoplarlo **por colección** (nivel "Medio").

## Flujo

1. ODM publica un dataset → `POST /odm/webhook` (firmado HMAC-SHA256 en
   `X-ODM-Signature`). Lo recibe `services/discovery/etl/app_webhook.py`.
2. SIPI verifica la firma y **enruta**: resuelve `(dominio, fuente)` y, si aplica,
   llama `poblar_recurso(...)`, que descarga el JSONL del último dataset
   (`/api/datasets/{id}/data.jsonl`) y lo resuelve sobre `sipi-core` por lotes.

## Enrutado: por COLECCIÓN (preferente) + RESOURCE_MAP (respaldo)

Antes el enrutado era por **nombre exacto** de recurso (`RESOURCE_MAP`), frágil:
había que tocar SIPI por cada recurso nuevo. Ahora:

- El webhook de ODM incluye **`collections`** (nombres de las colecciones del
  recurso).
- `src/odm/config.py::resolver_destino(resource_name, collections, publisher)`
  resuelve `(dominio, fuente)` con esta prioridad:
  1. **`RESOURCE_MAP[resource_name]`** — override fino (fuente exacta de recursos
     concretos). Gana sobre la colección.
  2. **`COLLECTION_MAP[colección]`** — la colección fija el **dominio** (y la
     **fuente** si es uniforme; si no, se deriva del publisher).
- Si no casa ni recurso ni colección suscrita → se ignora.

**Consecuencia**: cuando ODM añade un recurso nuevo a una colección a la que SIPI
está suscrito, SIPI lo procesa **sin tocar código**.

### `COLLECTION_MAP` (colección ODM → dominio SIPI)

| Colección organizativa en ODM | dominio | fuente |
|---|---|---|
| `SIPI · Administraciones (DIR3)` | administracion | DIR3 |
| `SIPI · Diócesis` | diocesis | CEE |
| `SIPI · Entidades religiosas` | entidad_religiosa | por recurso |
| `SIPI · Notarías` | notaria | CGN |
| `SIPI · Registros de la Propiedad` | registro_propiedad | CORPME |
| `SIPI · Inmuebles` | inmueble | por recurso (OSM/IAPH/CEE) |

`RESOURCE_MAP` se mantiene como **respaldo/override** (fuente precisa por recurso:
RER, CEE_PARROQUIA, CONFER, DIR3_PUENTE, etc.).

## Configuración en ODM (operativo, una vez)

Para que SIPI reciba los webhooks de una colección:

1. En ODM, crear cada colección **organizativa** de la tabla anterior y meter en
   ella los recursos correspondientes (un recurso puede estar en varias; las
   colecciones son conjuntos no disjuntos del pool).
2. Dar de alta a **SIPI** como *Subscriber* en ODM (webhook a
   `https://<host-sipi>/odm/webhook`, `consumption_mode=webhook`).
3. **Suscribir SIPI a esas colecciones** (vista Subscribers → editor de dos
   paneles → mover la colección a *Subscribed*). ODM entregará entonces los
   `dataset.published` de **todos los recursos miembros, presentes y futuros**.

> Nota: una nodriza se suscribe como su **familia** (colección matriz). Para SIPI
> basta con suscribir las colecciones organizativas `SIPI · …`.

## Contrato del payload (ODM → SIPI)

```jsonc
{
  "event": "dataset.published",
  "collections": ["SIPI · Administraciones (DIR3)", ...],   // ← enrutado por colección
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

- `app_webhook.py` — receptor del webhook; enruta por colección.
- `src/odm/config.py` — `COLLECTION_MAP`, `RESOURCE_MAP`, `resolver_destino`.
- `src/odm/pipeline.py` — `poblar_recurso(..., destino=(dominio,fuente))`.
- `src/odm/resolvers.py` — resolvers por dominio (upsert sobre sipi-core).

## Pendiente / evolución

- **Nivel "Máximo"**: que los recursos ODM declaren `dominio`/`fuente` como
  metadato (params/tags) y el payload los traiga → SIPI sin mapa alguno.
- Alinear `modules/comunicacion/services/odmgr_router` (política notify/trigger)
  para que también pueda enrutar por colección, no solo por `resource_name`.
