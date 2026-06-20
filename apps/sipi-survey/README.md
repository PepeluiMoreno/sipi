# apps/sipi-survey — Aplicación de vigilancia

Aplicación **técnica** para el establecimiento y control de los *dispositivos de
vigilancia* (watchers/scrapers que vigilan portales y fuentes: Idealista,
Fotocasa, OSM/Wikidata, BOE, BDNS…).

- Comparte el dominio con SIPI vía `packages/sipi-core` (modelo único).
- Orquesta y controla los pipelines de `services/discovery/` (etl, survey, osm).
- Las detecciones se materializan como `Expediente` (estado `propuesto`) para que
  la app **SIPI** las valide/ratifique.

> Esqueleto inicial. Pendiente: API de control + UI técnica. El backend de
> control puede partir de `services/discovery/survey/src/api/`.
