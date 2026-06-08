# odmclient

SIPI como **cliente** de OpenDataManager (ODM). No publica recursos: declara y
mantiene el *desired-state* de recursos (de sus publishers reales) que consume.

## Estructura
- `manifests/*.json` — un manifiesto declarativo por recurso ODM (publisher + resource).
- `apply_manifests.py` — motor único e idempotente que aplica los manifiestos vía
  GraphQL (upsert: publisher por acrónimo, resource por nombre). Mapea al
  `CreateResourceInput` real de ODM.

## Distinguir lo que ya existe en ODM de lo nuevo (`mode`)
Muchos recursos son tan generales que **ODM ya los tiene creados** (de hecho casi
todos se rescataron de su propio `seed_resources.py`). SIPI no debe re-crearlos ni
mantenerlos: los **consume**. Cada manifiesto declara su intención:

- `"mode": "subscribe"` — el recurso **ya existe en ODM**; se fija su `odm_id` real.
  El motor solo verifica que sigue ahí y (futuro) asegura la suscripción de SIPI.
  **Nunca escribe sus params** (evita que SIPI pise la definición de ODM).
- `"mode": "manage"` — recurso **propio de SIPI** que ODM no tiene (p. ej. el CEE).
  El motor hace upsert. Si el nombre ya existiera en ODM, lo marca como posible colisión.

Mecánicamente la distinción se obtiene casando por nombre contra `{ resources }` del
ODM vivo; el dry-run la imprime (`SUBSCRIBE · ya existe` vs `MANAGE · create`).
Hoy: **11 subscribe + 1 manage (CEE)**.

## Uso
```bash
# dry-run: SOLO lee ODM y muestra el plan (no escribe)
python -m app.odmclient.apply_manifests --base-url https://odmgr.pepelui.es --token "$ODM_TOKEN"
# aplicar (escribe en ODM) — requiere autorización previa:
python -m app.odmclient.apply_manifests --base-url ... --token ... --apply
```

## Gobernanza
- Coleccionar/editar manifiestos = lado SIPI, libre.
- `--apply` escribe en ODM -> **gateado**: el diff del manifiesto es el artefacto
  de comprensión; se aprueba y solo entonces se aplica.

## Colección de manifiestos (recursos que SIPI consume de ODM)
Rescatados fielmente de `seed_resources.py` de ODM (salvo el CEE, nuevo):

**Geografía** (tablas maestras alimentadas por ODM)
- `espana_comunidades_autonomas.json`, `espana_provincias.json`, `espana_municipios.json` (INE)
- `geonames_entidades_de_poblacion.json` — pedanías / entidades sub-municipales

**Actores**
- `dir3_unidades_organicas_de_espana.json` — administraciones (DIR3)
- `notarias_cgn.json` — Notarías, Guía Notarial (CGN), REST Loop (pivota provincias)
- `registros_corpme.json` — Registros de la Propiedad (CORPME), File Download xlsx
  · AVISO: URL caducada (404 en auditoría ODM); registradores.org renombró el documento.
- `rer_entidades_religiosas.json` — Registro de Entidades Religiosas (Min. Justicia)

**Dominio / enriquecimiento**
- `catastro_parcelas.json` — Catastro INSPIRE (WFS). Nota: bbox de Sevilla; parametrizar para nacional.
- `osm_inmuebles_eclesiasticos.json` — OSM Overpass

**Subvenciones**
- `bdns_concesiones_de_subvenciones.json` — BDNS

**CEE (nuevo)**
- `cee_inmatriculaciones.json` — listado saneado como File Download.
  · PENDIENTE: fijar `url` (objeto MinIO de la organización o enlace de descarga directa de Drive).
