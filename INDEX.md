# 🗺️ Agente de Sincronización OSM para SIPI

## 📂 Contenido del Paquete

Este paquete contiene un **sistema completo de sincronización** entre OpenStreetMap y tu sistema SIPI de gestión de patrimonio inmueble.

### 📋 Guías de Lectura (¡Empieza aquí!)

1. **[RESUMEN_COMPLETO.md](./RESUMEN_COMPLETO.md)** ⭐
   - Vista general del sistema
   - Funcionalidades principales
   - Casos de uso
   - Arquitectura técnica
   - **Recomendado leer primero**

2. **[INTEGRACION.md](./INTEGRACION.md)** 🔧
   - Guía paso a paso de integración
   - Estructura de carpetas
   - Instalación de dependencias
   - Checklist de integración
   - Solución de problemas comunes

3. **[OSM_README.md](./OSM_README.md)** 📚
   - Documentación técnica completa
   - Referencia de API
   - Configuración avanzada
   - Monitoreo y métricas

4. **[QUERY_ANALYSIS.md](./QUERY_ANALYSIS.md)** 🎯 **NUEVO**
   - Análisis de la query Overpass optimizada
   - 5 criterios progresivos explicados
   - Comparación básica vs optimizada
   - +100% cobertura (37,000 vs 18,000 elementos)
   - Optimizaciones técnicas

### 💻 Código Fuente

#### Módulos Principales

1. **[osm_sync_agent.py](./osm_sync_agent.py)** - Agente principal (v1)
   - Clase `OSMChurchSyncAgent`
   - Consulta Overpass API por bbox
   - Mapeo de datos OSM → SIPI
   - Sincronización incremental
   - ~530 líneas

1b. **[osm_sync_agent_v2.py](./osm_sync_agent_v2.py)** - Agente principal (v2) ⭐ **RECOMENDADA**
   - Todas las funcionalidades de v1 +
   - ✅ Soporte para área ISO de España completa
   - ✅ Query mejorada con 5 criterios progresivos
   - ✅ Captura elementos pequeños (cruces, humilladeros, grutas)
   - ✅ Filtrado por denominación católica
   - ✅ Timeout adaptativo (30 min vs 3 min)
   - Ver [VERSION_2_MEJORAS.md](./VERSION_2_MEJORAS.md) para detalles

2. **[geocode_resolver.py](./geocode_resolver.py)** - Geocoding reverso
   - Clase `GeocodeResolver`
   - Coordenadas → Provincia/Localidad
   - Cache de resultados
   - Integración con Nominatim
   - ~260 líneas

3. **[osm_cli.py](./osm_cli.py)** - Interfaz CLI
   - Comandos: sync, stats, list-provincias, seed-tipos
   - Modo dry-run
   - Output con Rich
   - ~180 líneas

4. **[scheduler_osm.py](./scheduler_osm.py)** - Scheduler automático
   - Sincronización semanal/diaria
   - Integración con FastAPI
   - APScheduler
   - ~140 líneas

5. **[graphql_osm_integration.py](./graphql_osm_integration.py)** - API GraphQL
   - Schema Strawberry
   - Queries y Mutations
   - Tipos GraphQL
   - Ejemplos de uso
   - ~380 líneas

#### Ejemplos y Tests

6. **[casos_uso_osm.py](./casos_uso_osm.py)** - 8 casos de uso completos
   - Sincronización inicial
   - Actualización incremental
   - Búsqueda de BICs
   - Análisis geográfico
   - Validación de calidad
   - Y más...
   - ~470 líneas

## 🚀 Quick Start

### 1. Leer documentación
```bash
# Primero: entender el sistema
cat RESUMEN_COMPLETO.md

# Segundo: guía de integración
cat INTEGRACION.md
```

### 2. Instalar dependencias
```bash
pip install httpx apscheduler typer rich sqlalchemy fastapi strawberry-graphql
```

### 3. Copiar archivos a tu proyecto
```
Sipi_graphql/
├── app/
│   ├── agents/
│   │   ├── osm_sync_agent.py          ← AQUÍ
│   │   └── geocode_resolver.py        ← AQUÍ
│   ├── cli/
│   │   └── osm_cli.py                 ← AQUÍ
│   ├── schedulers/
│   │   └── scheduler_osm.py           ← AQUÍ
│   └── graphql/
│       └── osm_resolvers.py           ← INTEGRAR
```

### 4. Poblar catálogos
```bash
python app/cli/osm_cli.py seed-tipos
```

### 5. Primera sincronización (dry-run)
```bash
python app/cli/osm_cli.py sync --provincia "Madrid" --dry-run
```

### 6. Sincronización real
```bash
python app/cli/osm_cli.py sync --provincia "Madrid"
```

## 📊 Estadísticas del Paquete

- **9 archivos** totales
- **~2,880 líneas** de código + documentación
- **8 casos de uso** documentados
- **100% integrado** con tu arquitectura SIPI existente

## 🎯 Características Principales

✅ Sincronización automática desde OpenStreetMap  
✅ Detección de BIC (Bienes de Interés Cultural)  
✅ Geocoding reverso (coordenadas → provincia/localidad)  
✅ Versionado incremental  
✅ CLI completo con Typer  
✅ Scheduler automático (semanal/diario)  
✅ API GraphQL  
✅ Arquitectura de extensiones (tabla separada)  
✅ Manejo de errores robusto  
✅ Documentación completa  

## 🔗 Flujo Recomendado

```
1. RESUMEN_COMPLETO.md    → Entender qué es y qué hace
2. INTEGRACION.md         → Cómo integrarlo paso a paso  
3. osm_sync_agent.py      → Revisar código principal
4. casos_uso_osm.py       → Ver ejemplos prácticos
5. osm_cli.py             → Probar comandos
6. OSM_README.md          → Referencia completa
```

## 🆘 ¿Necesitas Ayuda?

### Problemas Comunes
- **"No se encuentra provincia"** → Ver `INTEGRACION.md` sección "Problemas Comunes"
- **"Error de conexión OSM"** → Verificar internet y rate limits
- **"TipoInmueble no existe"** → Ejecutar `seed-tipos`

### Documentación
- Guía de integración: `INTEGRACION.md`
- Referencia técnica: `OSM_README.md`
- Casos de uso: `casos_uso_osm.py`

## 📞 Contacto

Este sistema fue diseñado específicamente para tu arquitectura SIPI, integrándose perfectamente con:
- Tu tabla `InmuebleOSMExt` existente ✅
- Tu sistema de catálogos (`TipoInmueble`) ✅
- Tu estructura geográfica (`Provincia`, `Localidad`) ✅
- Tu integración BDNS existente ✅

---

**¡Listo para empezar! 🎉**

Lee `RESUMEN_COMPLETO.md` para una visión general, luego sigue `INTEGRACION.md` para integrarlo.
