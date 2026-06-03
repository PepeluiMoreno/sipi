# 🚀 Guía de Integración - Agente OSM para SIPI

## 📦 Componentes Entregados

### Archivos Principales

```
sipi_osm_agent/
│
├── 📄 osm_sync_agent.py          # Agente principal de sincronización
├── 📄 geocode_resolver.py         # Geocoding reverso (coords → provincia/localidad)
├── 📄 osm_cli.py                  # Interfaz de línea de comandos
├── 📄 scheduler_osm.py            # Scheduler para ejecución automática
├── 📄 graphql_osm_integration.py  # Schema GraphQL + Resolvers
├── 📄 casos_uso_osm.py            # Ejemplos de uso prácticos
│
└── 📚 Documentación
    ├── OSM_README.md              # Documentación completa
    └── INTEGRACION.md             # Esta guía
```

## 🔧 Integración en tu Proyecto SIPI

### Paso 1: Estructura de Carpetas

Organiza los archivos en tu proyecto existente:

```
Sipi_graphql/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── osm_sync_agent.py          ← COPIAR AQUÍ
│   │   └── geocode_resolver.py        ← COPIAR AQUÍ
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── osm_cli.py                 ← COPIAR AQUÍ
│   │
│   ├── schedulers/
│   │   ├── __init__.py
│   │   └── scheduler_osm.py           ← COPIAR AQUÍ
│   │
│   ├── graphql/
│   │   ├── __init__.py
│   │   ├── schema.py                  ← INTEGRAR graphql_osm_integration.py
│   │   └── resolvers/
│   │       └── osm_resolvers.py       ← EXTRAER AQUÍ
│   │
│   └── db/
│       └── models/
│           └── extensiones_fuente.py  ← YA EXISTE ✅
│
├── examples/
│   └── casos_uso_osm.py               ← COPIAR AQUÍ
│
└── docs/
    └── OSM_README.md                   ← COPIAR AQUÍ
```

### Paso 2: Dependencias

Actualizar `requirements.txt` o `pyproject.toml`:

```txt
# Dependencias OSM
httpx>=0.27.0           # Cliente HTTP async
apscheduler>=3.10.0     # Scheduler de tareas
typer>=0.12.0           # CLI
rich>=13.0.0            # Output bonito en terminal

# Ya deberías tener:
sqlalchemy>=2.0.0
fastapi>=0.110.0
strawberry-graphql>=0.220.0
```

Instalar:
```bash
pip install httpx apscheduler typer rich
```

### Paso 3: Migración de Base de Datos

Tu modelo `InmuebleOSMExt` **ya existe** ✅, pero verifica que tenga todos los campos:

```python
# app/db/models/extensiones_fuente.py
class InmuebleOSMExt(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "inmuebles_osm_ext"
    
    inmueble_id: Mapped[str] = mapped_column(String(36), ForeignKey("inmuebles.id"), nullable=False, unique=True)
    osm_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # ← AÑADIR INDEX
    osm_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_updated_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    tags = mapped_column(MutableDict.as_mutable(JSONB), nullable=True)
    raw = mapped_column(MutableDict.as_mutable(JSONB), nullable=True)
    
    inmueble = relationship("Inmueble", backref="osm_ext", uselist=False)
```

**Crear migración Alembic**:
```bash
alembic revision --autogenerate -m "add_index_to_osm_id"
alembic upgrade head
```

### Paso 4: Seed de Datos

Poblar catálogo de tipos de inmueble:

```bash
cd app
python cli/osm_cli.py seed-tipos
```

Esto crea:
- Catedral, Basílica, Iglesia, Capilla
- Ermita, Monasterio, Convento
- Campanario, Humilladero, Santuario

### Paso 5: Configuración

Crear archivo de configuración `app/config/osm_config.py`:

```python
from pydantic_settings import BaseSettings

class OSMSettings(BaseSettings):
    # Overpass API
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT: int = 120
    
    # Nominatim (Geocoding)
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    USER_AGENT: str = "SIPI-Heritage-System/1.0"
    
    # Scheduler
    SYNC_CRON_WEEKLY: str = "0 2 * * 0"  # Domingos 2 AM
    SYNC_CRON_DAILY: str = "0 3 * * *"   # Diario 3 AM
    
    # Rate limiting
    REQUESTS_PER_SECOND: float = 1.0
    
    class Config:
        env_prefix = "OSM_"

osm_settings = OSMSettings()
```

### Paso 6: Integración GraphQL

Añadir al schema principal en `app/graphql/schema.py`:

```python
import strawberry
from app.graphql.resolvers.osm_resolvers import OSMQuery, OSMMutation

# Extender Query y Mutation existentes
@strawberry.type
class Query(ExistingQuery, OSMQuery):
    pass

@strawberry.type  
class Mutation(ExistingMutation, OSMMutation):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

### Paso 7: Integración FastAPI

En tu `main.py`:

```python
from fastapi import FastAPI
from app.schedulers.scheduler_osm import OSMSyncScheduler

app = FastAPI()

# Iniciar scheduler al arrancar la app
scheduler = None

@app.on_event("startup")
async def startup_event():
    global scheduler
    scheduler = OSMSyncScheduler()
    scheduler.start()
    logger.info("✅ OSM Scheduler iniciado")

@app.on_event("shutdown")
async def shutdown_event():
    global scheduler
    if scheduler:
        scheduler.stop()
        logger.info("🛑 OSM Scheduler detenido")
```

## 🎯 Primeros Pasos

### 1. Test de Conexión OSM

```bash
python -c "
import asyncio
from app.agents.osm_sync_agent import OSMChurchSyncAgent
from app.db.database import SessionLocal

async def test():
    db = SessionLocal()
    agent = OSMChurchSyncAgent(db)
    
    # Test con área pequeña
    bbox = (40.4, -3.8, 40.5, -3.7)  # Madrid centro
    data = await agent.fetch_churches(bbox)
    print(f'✅ Encontrados {len(data.get(\"elements\", []))} elementos')
    db.close()

asyncio.run(test())
"
```

### 2. Primera Sincronización (Dry Run)

```bash
python app/cli/osm_cli.py sync --provincia "Madrid" --dry-run
```

Revisa los resultados. Si todo se ve bien:

```bash
python app/cli/osm_cli.py sync --provincia "Madrid"
```

### 3. Verificar Resultados

```bash
python app/cli/osm_cli.py stats
```

### 4. Consultar desde GraphQL

```graphql
query {
  inmuebles(filter: {hasOsmData: true}, limit: 5) {
    nombre
    latitud
    longitud
    esBic
    osmExt {
      osmId
      version
    }
  }
}
```

## 📋 Checklist de Integración

- [ ] Archivos copiados en estructura correcta
- [ ] Dependencias instaladas
- [ ] Índice en `osm_id` creado
- [ ] Tipos de inmueble poblados
- [ ] Test de conexión OSM exitoso
- [ ] Primera sincronización (dry-run) ejecutada
- [ ] Primera sincronización real ejecutada
- [ ] Estadísticas verificadas
- [ ] GraphQL queries funcionando
- [ ] Scheduler configurado
- [ ] Documentación revisada

## 🚨 Problemas Comunes

### Error: "Unable to access OSM"
**Solución**: Verifica conexión a internet y que no estés siendo rate-limited.

### Error: "Provincia no encontrada"
**Solución**: Verifica que la provincia exista en tu BD. Usa:
```bash
python app/cli/osm_cli.py list-provincias
```

### Error: "TipoInmueble 'Iglesia' no existe"
**Solución**: Ejecuta seed de tipos:
```bash
python app/cli/osm_cli.py seed-tipos
```

### Sincronización muy lenta
**Solución**: 
1. Reduce el área (bbox más pequeño)
2. Aumenta timeout en config
3. Usa provincias en lugar de España completa

### Muchos inmuebles sin provincia_id
**Solución**: El geocoding reverso está comentado por defecto. 
Descomenta e implementa en `geocode_resolver.py` o asigna manualmente.

## 🎓 Próximos Pasos

1. **Implementar geocoding completo**
   - Descomentar funciones en `geocode_resolver.py`
   - Configurar Nominatim o alternativa

2. **Optimizar performance**
   - Cachear resultados de geocoding
   - Batch inserts más grandes
   - Paralelizar por provincia

3. **Añadir monitoreo**
   - Métricas de Prometheus
   - Alertas de fallos
   - Dashboard de estadísticas

4. **Integrar Wikidata**
   - Ya tienes `InmuebleWDExt` preparado
   - Sincronizar imágenes de Commons
   - Enriquecer con datos históricos

5. **Panel de administración**
   - UI para gestionar sincronizaciones
   - Ver diferencias antes de aplicar
   - Resolución manual de conflictos

## 📞 Soporte

Para preguntas o problemas:
1. Revisar documentación en `OSM_README.md`
2. Ejecutar casos de uso en `casos_uso_osm.py`
3. Verificar logs del agente

---

**¡Listo para empezar! 🚀**

Tu sistema SIPI ahora tiene capacidad de sincronización automática con OpenStreetMap.
