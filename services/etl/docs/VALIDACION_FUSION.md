# Validación del procedimiento de fusión CEE × OSM

Módulo: `services/etl/src/modules/fusion`. Objetivo: a partir del listado CEE
de inmatriculaciones (sin coordenadas) y de los bienes religiosos de
OpenStreetMap (con coordenadas), producir un *seed* de `Inmueble` sin duplicar,
con procedencia y bandas de confianza.

## Procedimiento

1. **Normalización bilingüe (es/gl)**: se quitan acentos, palabras de tipo
   (iglesia/igrexa, capilla/capela, ermita/ermida…), conectores y tratamientos;
   se normalizan hagiónimos gallego→castellano (Xoán→Juan, Paio→Pelayo…). Tanto
   el "Título" descriptivo del CEE como los nombres OSM se reducen a tokens de
   advocación comparables.
2. **Bloqueo** por token de advocación distintivo (se descartan los tokens
   ultra-frecuentes de la provincia).
3. **Score** = nombre (Jaccard + ratio de secuencia)·0.75 + compatibilidad de
   tipo·0.20 + bonus por municipio·0.10.
4. **Bandas**: ALTA (auto-fusión) / MEDIA (revisión) / SOLO_CEE / SOLO_OSM.

## Resultado real — provincia de Pontevedra

Datos: **1.176 bienes OSM** reales (Overpass, ES-PO) × **1.383 registros CEE**.

| Banda | Nº |
|-------|----|
| ALTA (auto-fusión CEE+OSM) | 132 |
| MEDIA (cola de revisión) | 41 |
| SOLO_CEE (sin equivalente OSM) | 1.210 |
| SOLO_OSM (no en listado CEE) | 1.089 |

Ejemplos ALTA correctos (incluyen cruce de idioma es↔gl):

- `0.95` CEE *"Ermita de la Asunción"* ↔ OSM *"Ermita de Nuestra Señora de la Asunción"*
- `0.87` CEE *"Capilla de la Consolación"* ↔ OSM *"Capela da Nosa Señora da Consolación"*
- `0.79` CEE *"Casa rectoral San Miguel de Curantes"* ↔ OSM *"Igrexa de San Miguel de Curantes"*
- `0.74` CEE *"Capilla de San Roque"* ↔ OSM *"Capela de San Roque"*

## Conclusiones

**Funciona** la normalización bilingüe y el emparejamiento por nombre+tipo:
detecta correctamente los bienes que están en ambas fuentes, cruzando gallego y
castellano. Un bug inicial (no se eliminaban las palabras de tipo en gallego)
hundía el resultado; corregido, las coincidencias ALTA pasaron de 5 a ~132.

**Limitación principal — falta clave geográfica fina.** A nivel provincia el
nombre solo es ambiguo: hay decenas de "San Miguel" / "Santa María" por
provincia. Además, en OSM `addr:city` solo está poblado en el **5 %** de los
bienes (aunque el **100 %** tiene coordenadas). El gran volumen de SOLO_CEE y
SOLO_OSM refleja en parte cobertura real (muchas capillas/cementerios/parcelas
del CEE no están itemizados en OSM, y viceversa), pero también ambigüedad por
falta de desambiguación a nivel municipio.

## Próximas mejoras (palancas claras)

1. **Bloqueo geográfico por municipio** (la palanca grande): reverse-geocodificar
   las coordenadas OSM (100 % disponibles) contra los polígonos de municipio
   (PostGIS, point-in-polygon) para asignar municipio a cada bien OSM. Confina el
   emparejamiento dentro del municipio → sube precisión y recall, y resuelve la
   ambigüedad de advocaciones repetidas.
2. **Catastro como fuente de coordenadas para el CEE**: donde la inmatriculación
   tenga referencia catastral, obtener geometría autoritativa del Catastro
   (WFS/INSPIRE). Resuelve los SOLO_CEE que OSM no cubre.
3. **Wikidata como ancla**: los bienes OSM con QID permiten enlace de alta
   confianza y enriquecimiento (diócesis, inception, heritage).
4. **Diccionario de hagiónimos gl→es** ampliado (ya iniciado) y, opcionalmente,
   embeddings semánticos para la franja MEDIA.

## Reproducir

```bash
cd services/etl
python scripts/seed_inmuebles_fusion.py \
    --cee ../../apps/api/ETL/preparation/data/output \
    --osm /ruta/osm_pontevedra.json \
    --provincia Pontevedra \
    --out /tmp/pontevedra
# -> _seed.json (todo) · _revision.json (banda MEDIA) · _resumen.json
```

El JSON de OSM se obtiene con la query `extract/queries/churches.overpassql`
acotada por provincia (`area["ISO3166-2"="ES-PO"]`).
