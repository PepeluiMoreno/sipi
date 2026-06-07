# Geolocalización en cascada de las inmatriculaciones de la CEE

> Análisis y artefactos derivados de la sesión de trabajo sobre cómo localizar
> geográficamente cada inmueble del listado CEE
> (`apps/api/ETL/preparation/data/input/Inmatriculaciones_CEE.xlsx`).
> Complementa a `TRANSACCION_geolocalizacion_manual.md` (worklist manual) y a
> `geografia.md`.

## 1. Punto de partida (verificado contra el dato)

- El xlsx CEE: 19 hojas (una por CCAA) en formato informe; el ETL
  `procesar_inmatriculaciones.py` lo aplana a un CSV por CCAA.
- **35.058 filas**, 34.698 con municipio; ~360 sin municipio.
- **No hay** referencia catastral, coordenadas ni dirección postal. El ancla es
  `Provincia + Municipio` + texto libre (`Título`/`Titular`/`Tipo`).
- **Problemas de calidad detectados:**
  - *Deriva de esquema*: el campo descripción aparece como `Título`, `Titulo`,
    `Descripción` y hay un `ecleSIástica` corrupto. Hay que unificarlo.
  - `Municipio` está **sobrecargado**: 10.394 valores únicos frente a ~8.131
    municipios reales; mezcla municipio con pedanías, `T.M. de X`, `(ERMITA)`,
    fragmentos `, nº` e incluso calles (`C/ ...`).
  - El acento se elimina en el ETL (lossy para geocodificar).

## 2. Cascada de geolocalización

El orden lo impone el dato. Cada nivel intenta **subir** la precisión; nunca se
inventa una coordenada (lo no resuelto se marca explícitamente).

1. **Centroide municipal** (padrón INE). Determinista. Precisión: municipio.
2. **Punto de entidad sub-municipal** (pedanías). Resuelve lo que el padrón
   municipal no puede por diseño. Precisión: núcleo.
3. **Edificio concreto vía OSM/Overpass**: `place_of_worship` dentro del recinto
   `admin_level=8`, casado por **advocación** (extraída de `Titular`/`Título`).
   Precisión: edificio. **No es opcional**: se ejecuta siempre; lo único
   graduado es si una coincidencia se auto-acepta o queda como candidato.
4. **Manual** (worklist `*_pendientes_geo.json`) para la cola irreducible.

### Regla de auto-aceptación de la etapa OSM
Una coincidencia a edificio solo se auto-acepta si depende de un **token que es
único entre los templos de ese municipio** (discriminante real, p.ej. `Solovio`,
`dos Agros`). Si solo comparte un patrón común (`San Juan`, `Santiago`), queda
como `candidato_confirmar` y **no se escribe**: protege contra falsos positivos
(principio anti-fallo-silencioso). Cuando `Titular` es propietario institucional
(`Arzobispado`, `Obispado`, una orden) **no** se usa como advocación.

## 3. Cobertura (medido / proyectado)

| Nivel | Cobertura |
|---|---|
| Centroide municipal INE | **74,4 %** (verificado) |
| + entidad sub-municipal | **+7,2 %** → **81,8 %** (verificado) |
| + geocoder gateado sobre el residuo | proyección **~90-93 %** |
| Suelo irreducible (manual) | **~6-8 %** (fragmentos de dirección, no-en-registros, sin municipio) |

La etapa OSM **no aumenta la cobertura**: mejora la precisión de un subconjunto
(los inmuebles tipo-templo) llevándolos del centroide al edificio. En muestra
urbana ~25-30 % de los tipo-templo se auto-aceptaron a edificio.

> Nota: el padrón usado en el ensayo fue **Wikidata** como proxy reproducible.
> En producción debe sustituirse por el **Nomenclátor INE** (municipios y
> entidades de población), que sube el tramo determinista y la confianza.

## 4. Dos ejes que conviene NO mezclar

- `fuente_coordenadas` = **procedencia**: `MANUAL/OSM/CATASTRO/WIKIDATA/GEOCODER/INE_PADRON`.
- `precision_geo` = **granularidad**: `EDIFICIO/NUCLEO/MUNICIPIO/SIN_UBICAR`.

Una coord puede ser "OSM" y aun así ser solo el centro del pueblo: misma fuente,
precisión opuesta. Separarlos resuelve además el TODO de `geo_quality_inferido`.

## 5. UI

- `GeolocalizacionNota.vue`: traduce `precision_geo`/`fuente_coordenadas`/
  confianza a una nota humana y, en mapa, sugiere pin vs **círculo de
  incertidumbre** (no pintar pin preciso sobre un centroide municipal).
- `FiltroRevisionGeo.vue`: aísla los inmuebles que necesitan **revisión manual**.

### Predicado `requiere_revision` (resolver en backend)
```python
requiere_revision = or_(
    Inmueble.coordenadas.is_(None),            # sin resolver
    Inmueble.geo_confianza == "media",         # determinación de confianza media
    Inmueble.osm_estado == "candidato_confirmar",  # candidato OSM sin confirmar
)
```
Añadir a `InmuebleFilters`: `requiere_revision: bool` y `precision_geo: str`.

## 6. Cómo ejecutar

```bash
python scripts/geolocalizar_inmatriculaciones.py \
  --input data/output --out salida \
  --overpass http://localhost:PUERTO/api/interpreter \
  --osm-sleep 0
```
Contra el Overpass local en contenedor no hay rate limit y la etapa de edificio
corre sobre toda España. Requisito: que el Overpass tenga **areas** generadas en
la importación (si no, `area["admin_level"=8]` devuelve vacío y hay que cambiar a
consulta por geometría de la relación o bbox del centroide).
