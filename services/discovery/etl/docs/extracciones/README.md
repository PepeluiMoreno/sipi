# Extracciones ETL — Índice

Cada extracción tiene su propio documento con: fuente, parámetros HTTP,
estructura HTML/CSV/API, ejecución y limitaciones conocidas.

| Código | Script | Fuente | Documento |
|--------|--------|--------|-----------|
| E1 | `extract/ine/descargar_nomenclator.py` | INE — Nomenclátor de municipios (Excel) | [extraccion_ine_nomenclator.md](extraccion_ine_nomenclator.md) — **TODO** |
| E2 | `extract/dir3/descargar_dir3.py` | DIR3 — Directorio de unidades orgánicas (ZIP) | [extraccion_dir3.md](extraccion_dir3.md) — **TODO** |
| E3 | `extract/registradores/descargar_registros_propiedad.py` | registradores.org — Directorio web (scraping 2 niveles) | [extraccion_registradores.md](extraccion_registradores.md) — **TODO** |
| E4 | `extract/colegios-notariales/descargar_colegios_notariales.py` | Ministerio de Exteriores — PDF colegios notariales | [extraccion_colegios_notariales.md](extraccion_colegios_notariales.md) — **TODO** |
| E5 | `extract/notarios/descargar_notarios.py` | CGN vía OpenDataManager (GraphQL + JSONL) | [extraccion_notarias_odm.md](extraccion_notarias_odm.md) — **TODO** |
| E5b | `extract/notarios/descargar_notarios_cgn.py` | CGN — buscador web directo (scraping) | [extraccion_notarias.md](extraccion_notarias.md) ✓ |
| E6 | `extract/osm/extract_inmuebles_osm.py` | OpenStreetMap Overpass API + Wikidata | [extraccion_osm_wikidata.md](extraccion_osm_wikidata.md) — **TODO** |

---

## Convención de nombrado

- **E1–E9:** extracciones de fuentes externas (datos de referencia)
- **T1–T9:** transformaciones (normalización, resolución de FKs)
- **L1–L9:** cargas en base de datos (`sipi.*`)
- **Código `b`:** variante alternativa del mismo paso (ej. E5 ODM vs E5b scraping directo)

## Fuentes configurables

Las URLs de fuentes externas se gestionan en [`fuentes.env`](../../fuentes.env).
Editar ahí si alguna fuente cambia de ubicación, sin tocar el código.

## TODO — documentos pendientes

Crear un `.md` por cada extracción marcada **TODO** arriba, siguiendo la
estructura de [`extraccion_notarias.md`](extraccion_notarias.md):

1. Descripción de la fuente
2. Parámetros HTTP / estructura de la API / selectores CSS
3. Ejecución con ejemplos
4. Limitaciones conocidas
5. Pipeline completa E→T→L
