# 🗺️ Sistema de Sincronización OSM para SIPI

Agente inteligente que sincroniza edificios religiosos desde OpenStreetMap al sistema SIPI de gestión de patrimonio inmueble.

## 📋 Características

- ✅ **Extracción automática** de iglesias, catedrales, monasterios y otros edificios religiosos desde OSM
- ✅ **Sincronización incremental** - Solo actualiza elementos que cambiaron
- ✅ **Arquitectura de extensiones** - Datos OSM separados en tabla `inmuebles_osm_ext`
- ✅ **Geocoding reverso** - Resolución automática de provincia/localidad desde coordenadas
- ✅ **Detección automática de BIC** - Identifica Bienes de Interés Cultural desde tags OSM
- ✅ **Scheduler integrado** - Ejecuciones periódicas automáticas
- ✅ **CLI completo** - Comandos para gestión manual
- ✅ **GraphQL API** - Consultas y mutaciones para gestionar sincronización

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│     OpenStreetMap Overpass API          │
│     (Datos de edificios religiosos)     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      OSMChurchSyncAgent                 │
│  - Consulta Overpass API                │
│  - Mapea datos OSM → Inmueble           │
│  - Geocoding reverso                    │
│  - Versionado y detección de cambios    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│     Base de Datos SIPI                  │
│  ┌────────────────────────────────┐     │
│  │  Inmueble                       │     │
│  │  - nombre, descripcion          │     │
│  │  - latitud, longitud            │     │
│  │  - provincia_id, localidad_id   │     │
│  │  - tipo_inmueble_id             │     │
│  │  - es_bic, es_ruina             │     │
│  └────────────┬───────────────────┘     │
│               │                          │
│               │ 1:1 relationship         │
│               │                          │
│  ┌────────────▼───────────────────┐     │
│  │  InmuebleOSMExt                │     │
│  │  - osm_id, osm_type            │     │
│  │  - version, source_updated_at  │     │
│  │  - tags (JSONB)                │     │
│  │  - raw (JSONB)                 │     │
│  └────────────────────────────────┘     │
└─────────────────────────────────────────┘
```

## 🚀 Instalación

### 1. Dependencias

```bash
pip install httpx asyncio sqlalchemy apscheduler typer rich
```

### 2. Integrar archivos al proyecto

Copiar los siguientes archivos a tu proyecto SIPI:

```
sipi_graphql/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── osm_sync_agent.py      # Agente principal
│   │   └── geocode_resolver.py    # Geocoding reverso
│   ├── cli/
│   │   └── osm_cli.py              # Comandos CLI
│   └── schedulers/
│       └── scheduler_osm.py        # Scheduler automático
```

### 3. Poblar catálogo de tipos

```bash
python osm_cli.py seed-tipos
```

Este comando crea los tipos de inmueble necesarios:
- Catedral, Basílica, Iglesia, Capilla
- Ermita, Monasterio, Convento
- Campanario, Humilladero, Santuario

## 💻 Uso

### Modo CLI

#### Sincronizar por provincia
```bash
# Sincronizar iglesias de Madrid
python osm_cli.py sync --provincia "Madrid"

# Sincronizar con simulación (no guarda cambios)
python osm_cli.py sync --provincia "Madrid" --dry-run
```

#### Sincronizar por bounding box
```bash
# España completa
python osm_cli.py sync --bbox "36.0,-9.5,43.8,3.3"

# Área específica (Andalucía)
python osm_cli.py sync --bbox "36.0,-7.5,38.7,-1.6"
```

#### Ver estadísticas
```bash
# Estadísticas de sincronización
python osm_cli.py stats

# Listar provincias disponibles
python osm_cli.py list-provincias
```

### Modo Programático

```python
from app.db.database import SessionLocal
from app.agents.osm_sync_agent import OSMChurchSyncAgent

db = SessionLocal()
agent = OSMChurchSyncAgent(db)

# Sincronizar
stats = await agent.sync_churches(
    provincia_nombre="Madrid",
    dry_run=False
)

print(f"Creados: {stats['created']}")
print(f"Actualizados: {stats['updated']}")

db.close()
```

### Scheduler Automático

```python
from app.schedulers.scheduler_osm import OSMSyncScheduler

# Iniciar scheduler
scheduler = OSMSyncScheduler()
scheduler.start()

# El scheduler ejecutará:
# - Sincronización semanal completa: Domingos 2 AM
# - Sincronización incremental diaria: Todos los días 3 AM
```

Para ejecutar como servicio:
```bash
python -m app.schedulers.scheduler_osm
```

### GraphQL API

#### Query: Buscar inmuebles con datos OSM

```graphql
query {
  inmuebles(filter: {hasOsmData: true}, limit: 10) {
    id
    nombre
    latitud
    longitud
    osmExt {
      osmId
      osmType
      version
      sourceUpdatedAt
      tags
    }
  }
}
```

#### Mutation: Sincronizar desde GraphQL

```graphql
mutation {
  syncOsmChurches(input: {
    provinciaNombre: "Madrid"
    dryRun: false
  }) {
    created
    updated
    skipped
    errors
  }
}
```

## 🗂️ Estructura de Datos

### Tabla `inmuebles`
Contiene datos principales del inmueble.

```python
Inmueble(
    nombre="Catedral de la Almudena",
    latitud=40.4153,
    longitud=-3.7142,
    provincia_id="...",
    localidad_id="...",
    tipo_inmueble_id="...",  # Catedral
    es_bic=True
)
```

### Tabla `inmuebles_osm_ext`
Contiene metadatos de OpenStreetMap.

```python
InmuebleOSMExt(
    inmueble_id="...",
    osm_id="way/12345678",
    osm_type="way",
    version=7,
    source_updated_at="2024-11-10T10:30:00Z",
    tags={
        "name": "Catedral de la Almudena",
        "amenity": "place_of_worship",
        "building": "cathedral",
        "religion": "christian",
        "denomination": "catholic",
        "heritage": "bien de interés cultural",
        "start_date": "1879",
        "architect": "Francisco de Cubas",
        "wikipedia": "es:Catedral de la Almudena"
    },
    raw={...}  # Respuesta completa de OSM
)
```

## 🎯 Mapeo de Datos OSM

### Tags principales procesados

| Tag OSM | Campo SIPI | Notas |
|---------|------------|-------|
| `name` | `nombre` | Nombre del edificio |
| `amenity=place_of_worship` | `tipo_inmueble_id` | Lugar de culto |
| `building=cathedral` | `tipo_inmueble_id` | Tipo específico |
| `building=church` | `tipo_inmueble_id` | Iglesia |
| `building=chapel` | `tipo_inmueble_id` | Capilla |
| `building=monastery` | `tipo_inmueble_id` | Monasterio |
| `addr:street` + `addr:housenumber` | `direccion` | Dirección completa |
| `heritage` o `ref:es:bic` | `es_bic` | Bien de Interés Cultural |
| `ruins=yes` | `es_ruina` | Edificio en ruinas |
| `lat`, `lon` | `latitud`, `longitud` | Coordenadas |

### Tipos de elementos OSM

- **node**: Punto geográfico simple
- **way**: Polígono cerrado (edificio)
- **relation**: Grupo de elementos relacionados

## 🔧 Configuración Avanzada

### Personalizar query Overpass

Editar `osm_sync_agent.py`, método `_build_overpass_query()`:

```python
# Añadir más tipos de edificios
node["building"="basilica"]({bbox});
way["building"="basilica"]({bbox});

# Filtrar por denominación
node["denomination"="catholic"]({bbox});

# Incluir elementos históricos
node["historic"="church"]({bbox});
```

### Configurar geocoding

Opciones en `geocode_resolver.py`:

1. **Nominatim de OSM** (por defecto)
   - Gratis, rate-limited
   - Requiere respetar política de uso

2. **Base de datos local**
   - Requiere coordenadas en tablas Provincia/Localidad
   - Sin límites de uso

3. **Servicios comerciales**
   - Google Geocoding API
   - Mapbox
   - Here Maps

### Ajustar frecuencia de sincronización

Editar `scheduler_osm.py`:

```python
# Cada 12 horas
trigger=CronTrigger(hour='*/12')

# Primer día de cada mes
trigger=CronTrigger(day=1, hour=2)

# Solo días laborables
trigger=CronTrigger(day_of_week='mon-fri', hour=3)
```

## 📊 Monitoreo

### Logs

Los logs muestran progreso en tiempo real:

```
🔄 Iniciando sincronización OSM...
📍 Área de búsqueda: (40.0, -4.0, 41.0, -3.0)
✅ Encontrados 237 elementos en OSM
💾 Checkpoint: {'created': 50, 'updated': 12, 'skipped': 88, 'errors': 0}
✨ Sincronización completada:
- Creados: 134
- Actualizados: 45
- Sin cambios: 56
- Errores: 2
```

### Métricas

```python
from app.db.models import Inmueble, InmuebleOSMExt

# Total de inmuebles con datos OSM
total_osm = db.query(InmuebleOSMExt).count()

# Inmuebles BIC identificados desde OSM
bic_count = db.query(Inmueble).filter(
    Inmueble.es_bic == True
).join(InmuebleOSMExt).count()

# Última actualización
last_sync = db.query(func.max(InmuebleOSMExt.updated_at)).scalar()
```

## ⚠️ Consideraciones

### Rate Limiting
Overpass API tiene límites:
- Max 2 peticiones simultáneas
- Timeout de 180 segundos por query
- Implementar retry con backoff exponencial

### Calidad de Datos
No todos los datos OSM son perfectos:
- Verificar campos críticos antes de confiar
- Implementar validaciones adicionales
- Permitir override manual

### Privacidad
- No sincronizar datos personales
- Respetar licencia ODbL de OSM
- Atribuir fuente de datos

## 🔄 Actualizaciones Futuras

### Roadmap
- [ ] Integración con Wikidata (`InmuebleWDExt`)
- [ ] Sincronización de imágenes desde Wikimedia Commons
- [ ] Resolución automática de diócesis
- [ ] Geocoding offline con base de datos local
- [ ] Panel de administración web
- [ ] Notificaciones de cambios importantes
- [ ] Exportación a GeoJSON para visualización

## 📚 Referencias

- [OpenStreetMap Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Nominatim API](https://nominatim.org/release-docs/latest/api/Overview/)
- [OSM Tags para edificios religiosos](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dplace_of_worship)
- [Documentación SIPI GraphQL](./README.md)

## 🤝 Contribuir

Para reportar bugs o sugerir mejoras:
1. Crear issue en repositorio
2. Describir comportamiento esperado vs actual
3. Incluir logs relevantes

## 📄 Licencia

Este código es parte del sistema SIPI y sigue la misma licencia del proyecto principal.

---

**Desarrollado para SIPI** - Sistema de Información de Patrimonio Inmueble
