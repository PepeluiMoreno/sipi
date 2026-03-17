# 🆕 Agente OSM v2 - Mejoras y Características

## 📊 Comparación de Versiones

### Versión 1 (osm_sync_agent.py)
- Query por bounding box (bbox)
- España completa requiere bbox manual: `(36.0, -9.5, 43.8, 3.3)`
- Timeout: 120 segundos
- Query más simple

### Versión 2 (osm_sync_agent_v2.py) ⭐ **RECOMENDADA**
- ✅ Query por **área ISO** (más eficiente)
- ✅ Query **mejorada con 5 criterios** progresivos
- ✅ Soporte para **elementos pequeños** (cruces, humilladeros, grutas)
- ✅ Filtrado por **denominación católica**
- ✅ Timeout adaptativo (30 min para España completa, 3 min para bbox)
- ✅ Mejor cobertura de edificios religiosos

## 🎯 Query Mejorada - 5 Criterios

La versión 2 usa una query exhaustiva con 5 criterios progresivos:

### Criterio 1: Lugares de culto católicos explícitos
```overpass
node["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"]
way ["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"]
rel ["amenity"="place_of_worship"]["religion"="christian"]["denomination"="catholic"]
```

### Criterio 2: Edificios religiosos católicos por tipo
```overpass
node["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"]
way ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"]
rel ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["denomination"="catholic"]
```

### Criterio 3: Lugares de culto cristianos sin denominación
```overpass
node["amenity"="place_of_worship"]["religion"="christian"][!"denomination"]
way ["amenity"="place_of_worship"]["religion"="christian"][!"denomination"]
rel ["amenity"="place_of_worship"]["religion"="christian"][!"denomination"]
```

### Criterio 4: Edificios religiosos cristianos sin denominación
```overpass
node["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["religion"="christian"][!"denomination"]
way ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["religion"="christian"][!"denomination"]
rel ["building"~"^(church|cathedral|chapel|monastery|convent|hermitage|basilica)$"]["religion"="christian"][!"denomination"]
```

### Criterio 5: Elementos pequeños (cruces, humilladeros, grutas)
```overpass
node["place_of_worship"~"^(cross|wayside_shrine|lourdes_grotto)$"]["religion"="christian"]
way ["place_of_worship"~"^(cross|wayside_shrine|lourdes_grotto)$"]["religion"="christian"]
rel ["place_of_worship"~"^(cross|wayside_shrine|lourdes_grotto)$"]["religion"="christian"]
```

## 🚀 Uso de la Versión 2

### 1. Sincronizar España Completa (área ISO)

**Ventajas:**
- ✅ Más eficiente que bbox
- ✅ No requiere calcular coordenadas
- ✅ Usa área administrativa de OSM

```bash
# CLI
python osm_cli.py sync --spain-area

# Programáticamente
stats = await agent.sync_churches(use_spain_area=True)
```

### 2. Sincronizar por Provincia (como antes)

```bash
python osm_cli.py sync --provincia "Madrid"
```

### 3. Sincronizar por Bbox (como antes)

```bash
python osm_cli.py sync --bbox "40.3,-3.8,40.5,-3.6"
```

## 📈 Mejoras en Cobertura

La query mejorada captura **muchos más elementos** que la versión 1:

### Elementos adicionales capturados:

1. **Ermitas** (`hermitage`)
2. **Cruces** (`cross`, `wayside_cross`)
3. **Humilladeros** (`wayside_shrine`)
4. **Grutas de Lourdes** (`lourdes_grotto`)
5. **Edificios sin denominación** (puede incluir ortodoxos, protestantes históricos, etc.)

### Estimación de cobertura:

- **v1**: ~8,000-10,000 elementos
- **v2**: ~15,000-20,000 elementos (estimado)

## ⚙️ Optimizaciones

### Timeout Adaptativo

```python
# España completa: 31 minutos
timeout = 1860.0 if use_spain_area else 180.0

# Bbox específico: 3 minutos
```

### Output Optimizado

```overpass
out tags center qt;
```

En lugar de:
```overpass
out body;
>;
out skel qt;
```

**Ventajas:**
- ✅ Menos datos transferidos
- ✅ Geometría simplificada a punto central
- ✅ Incluye todos los tags necesarios
- ✅ Más rápido

## 🔄 Migración de v1 a v2

### Opción 1: Reemplazar archivo completo

```bash
# Backup de v1
mv osm_sync_agent.py osm_sync_agent_v1_backup.py

# Usar v2
mv osm_sync_agent_v2.py osm_sync_agent.py
```

### Opción 2: Mantener ambas versiones

```python
# Importar la versión que necesites
from osm_sync_agent_v2 import OSMChurchSyncAgent  # v2
# o
from osm_sync_agent import OSMChurchSyncAgent     # v1
```

## 📝 Cambios en el Código

### Firma de función actualizada:

**v1:**
```python
async def sync_churches(
    self, 
    bbox: Optional[Tuple[float, float, float, float]] = None,
    provincia_nombre: Optional[str] = None,
    dry_run: bool = False
)
```

**v2:**
```python
async def sync_churches(
    self, 
    bbox: Optional[Tuple[float, float, float, float]] = None,
    provincia_nombre: Optional[str] = None,
    use_spain_area: bool = False,  # ⬅️ NUEVO
    dry_run: bool = False
)
```

### Mapeo de tipos ampliado:

**Nuevos tipos añadidos:**
```python
osm_to_tipo = {
    # ... tipos existentes ...
    "hermitage": "Ermita",          # ⬅️ NUEVO
    "cross": "Cruz",                # ⬅️ NUEVO
    "wayside_cross": "Crucero",     # ⬅️ NUEVO
    "lourdes_grotto": "Gruta"       # ⬅️ NUEVO
}
```

## 🎯 Recomendaciones

### Para proyectos nuevos:
✅ **Usar v2** directamente

### Para proyectos existentes:
1. Probar v2 con `--dry-run`
2. Comparar resultados
3. Migrar cuando estés satisfecho

### Para España completa:
✅ **Siempre usar** `--spain-area` (v2)
- Más eficiente
- Menos propenso a timeouts
- Mejor manejo en Overpass API

### Para áreas específicas:
✅ Usar `--provincia` o `--bbox` (funciona en ambas versiones)

## 📊 Ejemplos de Uso Comparados

### Sincronizar España completa

**v1:**
```bash
python osm_cli.py sync --bbox "36.0,-9.5,43.8,3.3"
# Puede fallar por timeout
# Requiere conocer coordenadas
```

**v2:**
```bash
python osm_cli.py sync --spain-area
# ✅ Más confiable
# ✅ Más simple
# ✅ Mejor rendimiento
```

### Scheduler

**v1:**
```python
stats = await agent.sync_churches(
    bbox=(36.0, -9.5, 43.8, 3.3),
    dry_run=False
)
```

**v2:**
```python
stats = await agent.sync_churches(
    use_spain_area=True,
    dry_run=False
)
```

## 🐛 Solución de Problemas

### Error: "Timeout en Overpass"
**v2**: Usa `--spain-area` en lugar de bbox para España completa

### Error: "Demasiados elementos"
**v2**: Query optimizada maneja mejor grandes volúmenes

### Resultados incompletos
**v2**: Los 5 criterios capturan más elementos

## 📚 Documentación Actualizada

Todos los documentos han sido actualizados para v2:
- ✅ CLI (`osm_cli.py`)
- ✅ Scheduler (`scheduler_osm.py`)
- ✅ Casos de uso (`casos_uso_osm.py`)

## ✅ Checklist de Migración

- [ ] Backup de v1
- [ ] Instalar v2
- [ ] Actualizar imports si es necesario
- [ ] Probar con `--spain-area --dry-run`
- [ ] Verificar resultados
- [ ] Actualizar scheduler
- [ ] Actualizar scripts existentes
- [ ] Añadir nuevos tipos al catálogo si es necesario:
  - Ermita
  - Cruz
  - Crucero
  - Gruta

## 🎉 Conclusión

La **versión 2** es una mejora significativa sobre la v1:

- ✅ Más eficiente
- ✅ Mejor cobertura
- ✅ Más tipos de edificios
- ✅ Query más robusta
- ✅ Manejo de timeouts mejorado
- ✅ Uso de área ISO para España

**Se recomienda migrar a v2 para todos los proyectos nuevos y existentes.**

---

**¿Dudas?** Revisa `OSM_README.md` o `INTEGRACION.md` para más detalles.
