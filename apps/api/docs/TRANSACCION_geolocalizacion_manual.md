# Requisito — Transacción de geolocalización manual y mapa en vistas

> Requisito registrado a partir del pipeline de fusión/descubrimiento
> (ver `services/etl/docs/DESCUBRIMIENTO_BIENES_RELIGIOSOS.md`). Módulos de
> acceso y comunicación **semejantes a los de SIGA**.

## 1. Transacción: geolocalización manual de inmuebles

Los inmuebles que la fusión deja como **SOLO_CEE** (inmatriculados pero
imposibles de localizar automáticamente — ver `*_pendientes_geo.json`) deben
poder **geolocalizarse a mano** desde la aplicación.

- **Transacción** (catálogo de acceso, patrón SIGA `Transaccion` /
  `diccionario_transacciones`): código `INMUEBLE_GEOLOCALIZAR`,
  recurso `inmueble`, acción `geolocalizar`; agrupada en una `Funcionalidad`
  de Inmuebles, concedida a los `Rol` correspondientes, con `AmbitoTransaccion`
  (alcance territorial: por diócesis/provincia) y traza en `LogAuditoria`.
- **Efecto**: fija `Inmueble.coordenadas` (POINT 4326).
- **Procedencia de la coordenada** (necesaria): añadir un campo persistido
  `fuente_coordenadas` (enum: `MANUAL` / `OSM` / `CATASTRO` / `WIKIDATA` /
  `GEOCODER`). Hoy `Inmueble.geo_quality_inferido` tiene un TODO y devuelve
  siempre `AUTO` por no poder distinguir AUTO/MANUAL: este campo lo resuelve y,
  además, **evita que una reejecución de la fusión sobrescriba** una
  geolocalización manual.
- **Worklist**: la entrada de trabajo es `*_pendientes_geo.json`.

## 2. Mapa en las vistas de inmueble

El mapa **ya está previsto** en el frontend:
- `apps/frontend/src/modules/inmuebles/components/InmuebleMapa.vue` y su vista
  homónima — Leaflet, pintan marcadores y emiten `select` (**solo
  visualización**).
- `InmuebleFormDatosGenerales.vue` edita las coordenadas hoy **tecleando
  lat/long a mano**.

**Falta**, para soportar la transacción anterior, un **modo selector** sobre el
mapa (marcador arrastrable / clic para situar el punto) que emita
`update:coordenadas`, reutilizable en:
- la ficha de inmueble (visualización),
- el formulario de datos generales (sustituye/acompaña a los campos numéricos),
- una vista de **worklist de geolocalización** que recorra los pendientes.

## 3. Notificación de hallazgos

Los **hallazgos** (bien religioso no presente en CEE — ver
`*_hallazgos_osm.json`) son objeto de **notificación** vía el módulo de
comunicación (patrón SIGA): `TipoNotificacion = "HALLAZGO_NO_CEE"` →
`Notificacion` a la audiencia/rol, respetando `PreferenciaNotificacion`. Se
registran como `InmuebleRaw`/`DeteccionAnuncio` (modelos `discovery`).
