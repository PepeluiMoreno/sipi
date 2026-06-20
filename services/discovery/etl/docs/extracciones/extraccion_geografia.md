# Extracción: Distribución Territorial de España

## Fuentes

La geografía de España se extrae desde **OpenDataManager (ODMGR)**, que actúa como
capa de staging y actualización programada. SIPI-ETL nunca accede directamente a INE ni CNIG.

### ODMGR → `core.geo_territorio`

| Recurso ODMGR | Fuente original | Cubre |
|---|---|---|
| España - CCAA y Provincias (INE) | INE `VALORES_VARIABLE/70` y `/20` | CCAA + Provincias |
| España - Entidades de Población (CNIG) | CNIG Nomenclátor Geográfico (CSV) | Municipios + ELM + Parroquias + Núcleos |

Ver arquitectura completa en:
`sipi_core/docs/ARQUITECTURA_GEOGRAFIA.md`

## Script de carga

`load/cargar_geografia.py`

Consume `geo_territorio` desde la GraphQL data API de ODMGR y carga
`sipi.unidades_territoriales` en orden ascendente de `nivel` (1→2→3→4+),
construyendo el mapa `codigo → UUID` sobre la marcha para resolver las FKs.

## Orden de ejecución

```
1. Ejecutar recurso "España - CCAA y Provincias" en ODMGR
2. Ejecutar recurso "España - Entidades de Población" en ODMGR
3. python load/cargar_geografia.py
```

Los pasos 1 y 2 solo son necesarios cuando INE/CNIG publican datos nuevos (anual).
