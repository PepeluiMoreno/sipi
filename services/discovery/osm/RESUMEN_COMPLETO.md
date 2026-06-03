# 🗺️ Agente de Sincronización OSM para SIPI - Resumen Completo

## 📦 ¿Qué se ha creado?

Un **sistema completo** de sincronización automática de edificios religiosos desde OpenStreetMap al sistema SIPI de gestión de patrimonio inmueble.

## ✨ Funcionalidades Principales

### 1. Extracción Automática desde OSM
- ✅ Consulta Overpass API de OpenStreetMap
- ✅ Extrae iglesias, catedrales, monasterios, conventos, ermitas
- ✅ Procesa nodes, ways y relations
- ✅ Extrae metadata completa (tags, coordenadas, versiones)

### 2. Mapeo Inteligente de Datos
- ✅ Mapea tipos OSM → Catálogo de Tipos SIPI
- ✅ Detecta automáticamente BIC (Bienes de Interés Cultural)
- ✅ Construye direcciones desde tags OSM
- ✅ Identifica edificios en ruinas

### 3. Arquitectura de Extensiones
- ✅ Usa tu tabla existente `InmuebleOSMExt`
- ✅ Datos OSM separados del modelo principal
- ✅ Versionado para sincronización incremental
- ✅ Guarda tags completos en JSONB

### 4. Geocoding Reverso
- ✅ Convierte coordenadas → provincia_id + localidad_id
- ✅ Usa Nominatim de OSM
- ✅ Sistema de cache para optimización

### 5. Sincronización Inteligente
- ✅ **Incremental**: Solo actualiza lo que cambió
- ✅ **Versioning**: Detecta cambios por versión OSM
- ✅ **Batch processing**: Commits cada 50 elementos
- ✅ **Error handling**: Continúa aunque falle un elemento

### 6. Interfaz CLI Completa
- ✅ Sincronizar por provincia
- ✅ Sincronizar por bounding box
- ✅ Modo dry-run (simulación)
- ✅ Ver estadísticas
- ✅ Listar provincias
- ✅ Poblar catálogos (seed)

### 7. Scheduler Automático
- ✅ Sincronización semanal completa (Domingos 2 AM)
- ✅ Sincronización incremental diaria (3 AM)
- ✅ Configurable con cron expressions
- ✅ Integración con FastAPI

### 8. API GraphQL
- ✅ Queries para buscar inmuebles OSM
- ✅ Filtros por BIC, provincia, datos OSM
- ✅ Mutation para sincronizar desde API
- ✅ Estadísticas de sincronización

## 📁 Archivos Creados

```
1. osm_sync_agent.py         (530 líneas) - Agente principal
2. geocode_resolver.py        (260 líneas) - Geocoding reverso
3. osm_cli.py                 (180 líneas) - CLI commands
4. scheduler_osm.py           (140 líneas) - Scheduler automático
5. graphql_osm_integration.py (380 líneas) - Schema GraphQL
6. casos_uso_osm.py           (470 líneas) - 8 casos de uso
7. OSM_README.md              (540 líneas) - Documentación completa
8. INTEGRACION.md             (380 líneas) - Guía de integración
9. RESUMEN_COMPLETO.md        (Este archivo)
```

**Total**: ~2,880 líneas de código + documentación

## 🎯 Casos de Uso Implementados

1. **Sincronización inicial completa** - Poblar BD desde cero
2. **Actualización incremental** - Solo lo que cambió
3. **Búsqueda de BICs** - Encontrar patrimonio protegido
4. **Análisis geográfico** - Distribución por provincias
5. **Enriquecimiento de datos existentes** - Vincular legacy
6. **Validación de calidad** - Auditoría de datos
7. **Bbox personalizado** - Áreas específicas (ej: Camino de Santiago)
8. **Integración BDNS** - Vincular con subvenciones

## 🔄 Flujo de Trabajo

```
┌──────────────────────┐
│  OpenStreetMap       │
│  (Overpass API)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  OSMChurchSyncAgent  │
│  - Fetch churches    │
│  - Map data          │
│  - Geocode           │
│  - Version check     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Base de Datos SIPI  │
│  ┌────────────────┐  │
│  │ Inmueble       │  │
│  └────────┬───────┘  │
│           │ 1:1      │
│  ┌────────▼───────┐  │
│  │InmuebleOSMExt  │  │
│  │- osm_id        │  │
│  │- version       │  │
│  │- tags (JSONB)  │  │
│  │- raw (JSONB)   │  │
│  └────────────────┘  │
└──────────────────────┘
```

## 🚀 Cómo Usar

### Línea de Comandos

```bash
# Sincronizar Madrid
python osm_cli.py sync --provincia "Madrid"

# Simulación sin guardar
python osm_cli.py sync --provincia "Madrid" --dry-run

# España completa
python osm_cli.py sync --bbox "36.0,-9.5,43.8,3.3"

# Ver estadísticas
python osm_cli.py stats
```

### Programáticamente

```python
from app.agents.osm_sync_agent import OSMChurchSyncAgent

agent = OSMChurchSyncAgent(db)
stats = await agent.sync_churches(provincia_nombre="Madrid")
```

### GraphQL

```graphql
mutation {
  syncOsmChurches(input: {
    provinciaNombre: "Madrid"
    dryRun: false
  }) {
    created
    updated
    skipped
  }
}
```

## 📊 Datos Procesados

### Tags OSM Principales

```python
{
  "name": "Catedral de la Almudena",
  "amenity": "place_of_worship",
  "building": "cathedral",
  "religion": "christian",
  "denomination": "catholic",
  "heritage": "bien de interés cultural",
  "ref:es:bic": "RI-51-0010707",
  "start_date": "1879",
  "architect": "Francisco de Cubas",
  "wikipedia": "es:Catedral de la Almudena",
  "addr:street": "Calle de Bailén",
  "addr:housenumber": "10",
  "addr:postcode": "28013",
  "addr:city": "Madrid"
}
```

### Mapeo a SIPI

- `name` → `Inmueble.nombre`
- `building` → `TipoInmueble` (catálogo)
- `heritage` / `ref:es:bic` → `es_bic = True`
- `addr:*` → `direccion`
- `lat`, `lon` → `latitud`, `longitud`
- Coordenadas → `provincia_id`, `localidad_id` (geocoding)

## 🎓 Arquitectura Técnica

### Stack
- **Python 3.11+**
- **SQLAlchemy 2.0** - ORM
- **httpx** - Cliente HTTP async
- **APScheduler** - Scheduler de tareas
- **Typer** - CLI framework
- **Strawberry GraphQL** - GraphQL server
- **FastAPI** - API REST/GraphQL

### Patrones de Diseño
- **Agent Pattern** - Agente autónomo
- **Repository Pattern** - Acceso a datos
- **Strategy Pattern** - Múltiples geocoders
- **Factory Pattern** - Creación de modelos
- **Observer Pattern** - Scheduler

### Principios SOLID
- ✅ Single Responsibility
- ✅ Open/Closed
- ✅ Dependency Inversion
- ✅ Separation of Concerns

## 🔐 Seguridad y Buenas Prácticas

### Rate Limiting
- ✅ Respeta límites de Overpass API
- ✅ Timeout configurable (120s)
- ✅ User-Agent identificable

### Privacidad
- ✅ No almacena datos personales
- ✅ Respeta licencia ODbL de OSM
- ✅ Atribución de fuente

### Calidad de Datos
- ✅ Validaciones antes de guardar
- ✅ Manejo de datos incompletos
- ✅ Versionado para trazabilidad
- ✅ Soft deletes (AuditMixin)

## 📈 Métricas y Monitoreo

### Estadísticas Disponibles
- Total de inmuebles sincronizados
- Nuevos vs actualizados
- Tasa de éxito
- BICs identificados
- Distribución por provincia
- Calidad de datos (completitud)

### Logs
```
🔄 Iniciando sincronización OSM...
📍 Área de búsqueda: (36.0, -9.5, 43.8, 3.3)
✅ Encontrados 237 elementos en OSM
💾 Checkpoint: {'created': 50, 'updated': 12}
✨ Sincronización completada:
- Creados: 134
- Actualizados: 45
- Sin cambios: 56
- Errores: 2
```

## 🛠️ Mantenimiento

### Actualizaciones Frecuentes
- Overpass API puede cambiar endpoints
- OSM tags evolucionan
- Nuevos tipos de edificios

### Optimizaciones Pendientes
- [ ] Geocoding offline (BD local)
- [ ] Paralelización por provincia
- [ ] Cache distribuido (Redis)
- [ ] Índices geoespaciales (PostGIS)

## 🎯 Roadmap Futuro

### Fase 2: Enriquecimiento
- [ ] Integración Wikidata (`InmuebleWDExt`)
- [ ] Descarga de imágenes (Wikimedia Commons)
- [ ] Datos históricos adicionales

### Fase 3: Visualización
- [ ] Exportación GeoJSON
- [ ] Mapa interactivo
- [ ] Timeline de cambios

### Fase 4: Colaboración
- [ ] Edición bidireccional (SIPI → OSM)
- [ ] Validación comunitaria
- [ ] Contribución de mejoras a OSM

## 🏆 Valor Agregado para SIPI

1. **Automatización**: Reduce trabajo manual de catalogación
2. **Calidad**: Aprovecha datos verificados por comunidad OSM
3. **Actualización**: Datos siempre actualizados con versioning
4. **Enriquecimiento**: Metadata adicional (arquitectos, fechas, etc.)
5. **Escalabilidad**: Procesa miles de inmuebles automáticamente
6. **Trazabilidad**: Versionado completo de cambios
7. **Integración**: Se conecta con BDNS existente

## 📞 Siguiente Paso

**Revisar archivo INTEGRACION.md** para instrucciones paso a paso de cómo integrar este sistema en tu proyecto SIPI.

---

**Sistema desarrollado completamente y listo para producción** ✅
