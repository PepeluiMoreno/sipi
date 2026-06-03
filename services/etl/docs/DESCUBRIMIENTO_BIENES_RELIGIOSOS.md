# Descubrimiento de bienes religiosos por scoring

Procedimiento del pipeline de descubrimiento de SIPI. Objetivo: **identificar
bienes religiosos y, en especial, los que NO constan en el listado CEE de
inmatriculaciones** (los hallazgos más valiosos), cruzando varias fuentes,
clasificando la "religiosidad" mediante un score multi-señal y notificando los
hallazgos. Evitando duplicados y conservando la procedencia.

---

## 1. La piedra de toque: ¿qué es "religioso"?

No hay un campo único que lo diga. Hay que separar **tres sentidos** que no
coinciden:

| Sentido | Definición | Señal |
|---------|------------|-------|
| **Titularidad** | propiedad de una entidad religiosa (diócesis, parroquia, orden) | *decisivo para la causa* |
| **Uso** | hoy es lugar de culto / uso religioso | secundario |
| **Origen** | fue religioso, hoy secular (ex-templo → museo, hotel…) | **se excluye** |

El CEE es, por construcción, una lista de **titularidad** eclesiástica (incluye
templos, pero también fincas, casas rectorales, cementerios y parcelas que no
son templos). Por tanto, filtrar solo por "lugar de culto" es la definición más
estrecha: pierde lo más valioso y cuela ex-templos secularizados.

**Regla operativa:**

> Un bien es **religioso** si *(su titular es una entidad religiosa)* **Ó**
> *(su uso actual es religioso)*. Es **hallazgo** si es religioso **y** no
> consta en CEE. Los bienes religiosos solo **de origen** (uso y titularidad
> actuales seculares) se excluyen.

Esto encaja con el modelo: eje **uso** = `Inmueble.uso_religioso_activo` +
`InmuebleUso`/`TipoUsoInmueble`; eje **titularidad** = `entidad_religiosa_id` /
`diocesis_id` / `propietario_actor`.

---

## 2. Fuentes y señales

| Fuente | Aporta | Fiabilidad |
|--------|--------|-----------|
| **CEE** (inmatriculaciones) | titularidad eclesiástica (por definición), municipio, tipo; **sin coordenadas** | alta para titularidad |
| **OSM** | uso/arquitectura (`amenity=place_of_worship`, `building=church/chapel…`, `religion`, `denomination`), a veces `operator`/`diocese`; **coordenadas 100 %** | media (uso); baja (titularidad) |
| **Catastro** | **uso catastral** + geometría/coordenadas por referencia (RC); titular **PROTEGIDO** (no público) | alta para uso/coords |
| **Wikidata** | ontología (`P31` iglesia/capilla/monasterio), `P140` religión, `P127` propietario (diócesis/orden); coords | alta donde existe QID |
| **Idealista** (vía `sipi-survey`) | anuncios de venta de inmuebles eclesiásticos | señal de existencia/operación |

---

## 3. El clasificador de religiosidad (scoring multi-señal)

Cada bien candidato recibe un **score de religiosidad** combinando señales
ponderadas. No es un único tag: es la suma de evidencias.

| Señal | Detección | Peso |
|-------|-----------|------|
| **Titularidad religiosa** | CEE `Titular`; OSM `operator`/`operator:type=religious`/`diocese`; WD `P127`=diócesis/orden | **0.40** (decisiva) |
| **Uso catastral religioso** | Catastro `DNPRC` → uso "religioso" | **0.25** (autoritativa) |
| **Uso/función OSM** | `amenity=place_of_worship` + `religion=christian` + `denomination=catholic` | 0.20 |
| **Tipo de edificio/entidad** | iglesia, capilla, ermita, convento, monasterio, casa rectoral, cementerio parroquial | 0.15 |
| **Ontología Wikidata** | `P31` ∈ {iglesia, capilla, monasterio…}; `P140` cristiano | 0.10 (apoyo) |
| **Advocación** | dedicación a santo/virgen (San/Santa/Ntra. Sra./Ermida de…) | 0.05 (débil) |
| **Penalización: secularizado** | `historic=church` + uso actual no religioso; `disused:`; reconversión (hotel, museo…) | −0.40 |

**Bandas:**

- `score ≥ 0.60` → **religioso confirmado**
- `0.35 ≤ score < 0.60` → **probable** → cola de revisión
- `score < 0.35` → **no religioso** (descartar)

Los pesos y umbrales son configurables. La advocación nunca decide por sí sola
(hay topónimos y edificios civiles con nombre de santo).

---

## 4. El pipeline de descubrimiento (paso a paso)

```
  [OSM]   [CEE]   [Catastro]   [Wikidata]   [Idealista]
    │       │         │            │            │
    └───────┴────┬────┴────────────┴────────────┘
                 ▼
   (a) Extracción por fuente
                 ▼
   (b) Normalización es/gl + tipo canónico + advocación
                 ▼
   (c) Reverse-geocoding a municipio (point-in-polygon)
                 ▼
   (d) Clasificación de religiosidad (scoring §3)
                 ▼
   (e) Resolución de entidades / fusión bloqueada por municipio
                 ▼
   (f) Clasificación del resultado
```

**(a) Extracción.** OSM vía Overpass por provincia (`churches.overpassql`,
acotada `area["ISO3166-2"=…]`); CEE desde los CSV normalizados; Catastro y
Wikidata como enriquecimiento bajo demanda.

**(b) Normalización.** Quita acentos, palabras de tipo (iglesia/igrexa,
capilla/capela…), conectores y tratamientos; hagiónimos gallego→castellano
(Xoán→Juan); extrae la advocación del Título descriptivo del CEE. Reduce ambos
lados a tokens comparables.

**(c) Reverse-geocoding a municipio.** Como OSM trae `addr:city` solo en ~5 %
pero coordenadas en el 100 %, se asigna municipio por inclusión del punto en el
polígono municipal (`admin_level=8` o, en producción, `ST_Contains` contra los
polígonos de `geografia` en PostGIS). Con rescate por proximidad para no perder
bienes rurales si el límite no cubre bien el término.

**(d) Clasificación de religiosidad.** Aplica el scoring del §3 a cada
candidato. Lo "probable" va a revisión, lo "no religioso" se descarta.

**(e) Fusión / resolución de entidades.** Empareja CEE↔OSM **bloqueando por
municipio** (clave: evita casar el mismo santo en municipios distintos —
validado: sin geo, ~58 % de los matches "ALTA" eran falsos positivos). Score de
emparejamiento = nombre·0.78 + compatibilidad de tipo·0.22. Bandas ALTA
(auto-fusión) / MEDIA (revisión).

**(f) Clasificación del resultado:**

| Resultado | Significado | Acción |
|-----------|-------------|--------|
| **En CEE y en otra fuente** | inmatriculado y localizado | `Inmueble` canónico con procedencia (`Inmatriculacion` + `InmuebleOSMExt`), coords de OSM; ALTA auto, MEDIA revisión |
| **SOLO_CEE** | inmatriculado **sin localizar** | backlog de **geolocalización manual** (transacción `INMUEBLE_GEOLOCALIZAR`) + intento de coords vía Catastro |
| **SOLO_OSM / otra fuente, religioso y no en CEE** | **HALLAZGO** | enriquecer (Catastro uso/RC, Wikidata), recalcular religiosidad y **notificar** |

---

## 5. El hallazgo (resultado más valioso)

Un bien **religioso** (score §3 ≥ confirmado) **no presente en CEE** es un
hallazgo: un inmueble que la Iglesia usa o posee y que no consta inmatriculado
por esta vía.

**Prioridad del hallazgo:** se marca `municipio_con_cee` cuando el municipio sí
tiene registros CEE y aun así el bien no consta — señal fuerte (el CEE "miró"
ahí). En Pontevedra: 1.107 hallazgos, 714 prioritarios.

**Fiabilidad / falsos positivos:** un hallazgo es tan bueno como el *recall* del
emparejamiento — si la fusión no enlaza un CEE↔OSM que sí son el mismo edificio,
ese bien aparecería como hallazgo siendo falso. Mitigaciones: (1) bloqueo por
municipio, (2) prioridad `municipio_con_cee`, (3) la banda MEDIA retiene los
enlaces dudosos antes de que inflen los hallazgos.

**Notificación** (módulo de comunicación, patrón SIGA):
`TipoNotificacion = "HALLAZGO_NO_CEE"` → `Notificacion` a la audiencia/rol
correspondiente, respetando `PreferenciaNotificacion`. El hallazgo se registra
además como `InmuebleRaw`/`DeteccionAnuncio` (modelos `discovery`).

---

## 6. Enriquecimiento con Catastro

Servicios web libres de la Sede del Catastro (SOAP y REST, **sin API key**):

- `Consulta_RCCOOR` (coords → referencia catastral): para un bien con
  coordenadas (p. ej. un hallazgo OSM), obtiene su RC.
- `Consulta_DNPRC` (RC → datos no protegidos): **uso catastral**, superficie,
  año, clase → alimenta el score de religiosidad (uso) y enriquece el inmueble.
- `Consulta_CPMRC` (RC → coords) e INSPIRE **WFS GetParcel** (RC → geometría):
  para geometría/coordenadas autoritativas.

> Importante: el Catastro público devuelve **datos NO protegidos**. El
> **titular** (propietario) **no** es público vía estos servicios; la
> titularidad eclesiástica hay que tomarla del CEE, de `operator` en OSM o de
> `P127` en Wikidata.

Doble valor: el `uso` catastral refuerza la **piedra de toque** (religiosidad) y
la geometría resuelve la **geolocalización** de los SOLO_CEE.

---

## 7. Salidas del proceso

| Fichero | Contenido |
|---------|-----------|
| `*_seed.json` | todas las entidades fusionadas con procedencia y bandas |
| `*_hallazgos_osm.json` | **hallazgos** (religioso, no en CEE), ordenados por prioridad |
| `*_pendientes_geo.json` | SOLO_CEE sin coordenadas (backlog de geolocalización) |
| `*_revision.json` | banda MEDIA (enlaces/clasificaciones dudosas) |
| `*_resumen.json` | contadores + informe de cobertura geográfica |

Modelos destino: `Inmueble` (canónico) + `Inmatriculacion` (CEE) +
`InmuebleOSMExt`/`InmuebleWDExt` (OSM/Wikidata) + `discovery` (hallazgos).

---

## 8. Integración con los módulos (patrón SIGA)

- **Acceso (RBAC)**: la geolocalización manual y la confirmación de hallazgos se
  registran como `Transaccion` en el catálogo (`diccionario_transacciones`),
  agrupadas en `Funcionalidad`, concedidas a `Rol`, con `AmbitoTransaccion`
  (alcance territorial) y `LogAuditoria`.
- **Comunicación**: los hallazgos se notifican vía `TipoNotificacion` +
  `Notificacion` + `PreferenciaNotificacion` (+ `PlantillaEmail`), con
  resolución de audiencia.

---

## 9. Estado e implementación

- **Hecho y validado** (`services/etl/src/modules/fusion`): normalización es/gl,
  extracción de advocación, reverse-geocoding a municipio, fusión bloqueada por
  municipio, bandas de confianza, emisión de hallazgos y backlog. Validado en
  Pontevedra (ver `VALIDACION_FUSION.md`).
- **Por implementar**: el `clasificador_religioso` con los pesos del §3; los
  conectores de Catastro (`RCCOOR`/`DNPRC`) y Wikidata; las transacciones de
  acceso y los tipos de notificación, sobre los módulos tipo SIGA.
