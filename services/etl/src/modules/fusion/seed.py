# -*- coding: utf-8 -*-
"""Orquestación: construye el *seed inteligente* a partir de la fusión CEE×OSM.

Cada entidad fusionada es candidata a un `Inmueble` canónico (esquema `app`)
que cuelga su procedencia:
  - `Inmatriculacion`  -> registro CEE (registro, título, titular, tipo)
  - `InmuebleOSMExt`   -> elemento OSM (osm_id, wikidata, coordenadas)

Filosofía:
  - banda ALTA  -> auto-fusión (Inmueble con coords de OSM + ambas procedencias)
  - banda MEDIA -> cola de revisión (no se fusiona en firme)
  - CEE sin match (o BAJA) -> Inmueble solo-CEE, sin coords (pendiente de
    geolocalizar vía Catastro/geocoder)
  - OSM sin match -> Inmueble solo-OSM, con coords (no está en el listado CEE;
    interesante para la causa)

Nunca se descarta dato de origen: toda la procedencia queda registrada.
"""
import json
from dataclasses import dataclass, asdict, field

from .matcher import match_cee_osm
from .sources import load_cee, load_osm

__all__ = ["FusedEntity", "run_fusion"]


@dataclass
class FusedEntity:
    nombre: str
    tipo: str
    municipio: str
    provincia: str
    confianza: str            # ALTA | MEDIA | SOLO_CEE | SOLO_OSM
    score: float
    lat: float = None
    lon: float = None
    # procedencia
    cee_registro: str = None
    cee_titulo: str = None
    cee_titular: str = None
    osm_id: str = None
    osm_nombre: str = None
    wikidata: str = None
    geo_confirmado: bool = False  # municipio CEE == municipio OSM (point-in-polygon)
    municipio_con_cee: bool = None  # SOLO_OSM: si el municipio tiene registros CEE (señal fuerte de hallazgo)
    fuentes: list = field(default_factory=list)  # ['CEE','OSM']


def run_fusion(csv_dir, osm_json, provincia=None, ccaa=None, osm_boundaries=None):
    """Ejecuta la fusión y devuelve (entidades, resumen).

    Si `osm_boundaries` (JSON Overpass admin_level=8 o GeoJSON de municipios) se
    indica, se asigna municipio a cada bien OSM por point-in-polygon y el
    emparejamiento se bloquea por municipio (mayor precisión).
    """
    cee = load_cee(csv_dir, provincia=provincia, ccaa=ccaa)
    osm = load_osm(osm_json)

    cobertura_geo = None
    if osm_boundaries:
        from .geo import MunicipioIndex
        idx = (MunicipioIndex.from_geojson(osm_boundaries)
               if osm_boundaries.endswith(".geojson")
               else MunicipioIndex.from_overpass_json(osm_boundaries))
        cobertura_geo = idx.asignar(osm)

    matches, matched_osm = match_cee_osm(cee, osm, use_geo=bool(osm_boundaries))

    from .geo import norm_municipio
    cee_munis = {norm_municipio(c.municipio) for c in cee if c.municipio}

    entidades = []
    counts = {"ALTA": 0, "MEDIA": 0, "SOLO_CEE": 0, "SOLO_OSM": 0}

    for m in matches:
        c = m.cee
        if m.band == "ALTA":
            o = m.osm
            entidades.append(FusedEntity(
                nombre=o.name, tipo=c.tipo_canon, municipio=c.municipio,
                provincia=c.provincia, confianza="ALTA", score=round(m.score, 3),
                lat=o.lat, lon=o.lon, cee_registro=c.registro, cee_titulo=c.titulo,
                cee_titular=c.titular, osm_id=o.osm_id, osm_nombre=o.name,
                wikidata=o.wikidata, fuentes=["CEE", "OSM"], geo_confirmado=m.geo_confirmado))
            counts["ALTA"] += 1
        elif m.band == "MEDIA":
            o = m.osm
            entidades.append(FusedEntity(
                nombre=c.advocacion or c.titulo[:80], tipo=c.tipo_canon,
                municipio=c.municipio, provincia=c.provincia, confianza="MEDIA",
                score=round(m.score, 3), lat=o.lat, lon=o.lon,
                cee_registro=c.registro, cee_titulo=c.titulo, cee_titular=c.titular,
                osm_id=o.osm_id, osm_nombre=o.name, wikidata=o.wikidata,
                fuentes=["CEE", "OSM?"], geo_confirmado=m.geo_confirmado))
            counts["MEDIA"] += 1
        else:  # BAJA o SIN_MATCH -> entidad solo CEE
            entidades.append(FusedEntity(
                nombre=c.advocacion or c.titulo[:80], tipo=c.tipo_canon,
                municipio=c.municipio, provincia=c.provincia, confianza="SOLO_CEE",
                score=round(m.score, 3), cee_registro=c.registro, cee_titulo=c.titulo,
                cee_titular=c.titular, fuentes=["CEE"]))
            counts["SOLO_CEE"] += 1

    # OSM no emparejado -> entidad solo OSM (no está en el listado CEE)
    for j, o in enumerate(osm):
        if j in matched_osm:
            continue
        con_cee = bool(o.municipio and norm_municipio(o.municipio) in cee_munis)
        entidades.append(FusedEntity(
            nombre=o.name, tipo=o.tipo_canon, municipio=(o.municipio or o.city), provincia=provincia or "",
            confianza="SOLO_OSM", score=0.0, lat=o.lat, lon=o.lon,
            osm_id=o.osm_id, osm_nombre=o.name, wikidata=o.wikidata,
            municipio_con_cee=con_cee, fuentes=["OSM"]))
        counts["SOLO_OSM"] += 1

    resumen = {
        "cee_total": len(cee),
        "osm_total": len(osm),
        "fusionados_alta": counts["ALTA"],
        "revision_media": counts["MEDIA"],
        "solo_cee": counts["SOLO_CEE"],
        "solo_osm": counts["SOLO_OSM"],
        "entidades_total": len(entidades),
        "hallazgos_osm_no_cee": counts["SOLO_OSM"],
        "hallazgos_osm_no_cee_prioritarios": sum(
            1 for e in entidades if e.confianza == "SOLO_OSM" and e.municipio_con_cee),
    }
    if cobertura_geo is not None:
        resumen["cobertura_geo"] = cobertura_geo
    return entidades, resumen


def write_outputs(entidades, resumen, out_prefix):
    """Escribe seed.json (todo), revision.json (MEDIA), pendientes_geo.json
    (SOLO_CEE sin coordenadas) y resumen.json."""
    with open(out_prefix + "_seed.json", "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in entidades], f, ensure_ascii=False, indent=2)
    with open(out_prefix + "_revision.json", "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in entidades if e.confianza == "MEDIA"],
                  f, ensure_ascii=False, indent=2)
    # Worklist de geolocalización manual: inmuebles imposibles de fusionar (sin coords).
    # Alimenta la transacción `inmueble.geolocalizar` (ver
    # apps/api/docs/TRANSACCION_geolocalizacion_manual.md).
    with open(out_prefix + "_pendientes_geo.json", "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in entidades
                   if e.confianza == "SOLO_CEE" and e.lat is None],
                  f, ensure_ascii=False, indent=2)
    with open(out_prefix + "_resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    # Hallazgos OSM no presentes en CEE (los más valiosos): objeto de notificación.
    # Prioridad: municipio_con_cee=True (CEE cubre ese municipio y aun así no consta).
    hallazgos = [asdict(e) for e in entidades if e.confianza == "SOLO_OSM"]
    hallazgos.sort(key=lambda e: (not e["municipio_con_cee"], e["municipio"] or "", e["nombre"]))
    with open(out_prefix + "_hallazgos_osm.json", "w", encoding="utf-8") as f:
        json.dump(hallazgos, f, ensure_ascii=False, indent=2)
