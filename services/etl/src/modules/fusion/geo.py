# -*- coding: utf-8 -*-
"""Reverse-geocoding de coordenadas OSM a municipio (point-in-polygon).

Resuelve la palanca clave de la fusión: como OSM trae `addr:city` solo en ~5 %
de los bienes pero coordenadas en el 100 %, asignamos el municipio por
inclusión espacial del punto en el polígono municipal. Eso permite **bloquear
el emparejamiento por municipio**, que sube mucho la precisión (evita casar el
mismo santo en municipios distintos).

Fuente de polígonos:
- Aquí: límites `admin_level=8` de OSM (Overpass `out geom`) convertidos con
  `osm2geojson`, o un GeoJSON de municipios.
- En producción: equivale a `ST_Contains(municipio.geom, punto)` contra los
  polígonos de municipio ya cargados en PostGIS (modelo `geografia`).

Requiere: shapely, osm2geojson (solo para la fuente OSM).
"""
import json
import re

from .normalize import strip_accents

__all__ = ["MunicipioIndex", "norm_municipio"]

# Alias castellano->gallego y otros (municipios que difieren de forma entre CEE y OSM)
_ALIAS = {
    "la caniza": "a caniza", "las nieves": "as neves",
    "villa de cruces": "vila de cruces", "golada": "agolada",
    "cotobad": "cotobade", "puenteareas": "ponteareas",
    "la estrada": "a estrada", "el grove": "o grove",
    "caldas de reyes": "caldas de reis", "sangenjo": "sanxenxo",
    "bayona": "baiona", "mondariz balneario": "mondariz",
}
_ART = re.compile(r"^(a|o|as|os|la|las|el|los)\s+")


def norm_municipio(name: str) -> str:
    """Normaliza un nombre de municipio para el join CEE↔OSM (es↔gl, artículos)."""
    s = strip_accents(name)
    s = _ALIAS.get(s, s)
    s = _ART.sub("", s)
    return s.strip()


class MunicipioIndex:
    """Índice espacial de municipios con consulta point-in-polygon."""

    def __init__(self, polygons, names):
        from shapely.strtree import STRtree
        self._polys = polygons
        self._names = names
        self._tree = STRtree(polygons) if polygons else None

    @classmethod
    def from_overpass_json(cls, path):
        """Construye el índice desde un JSON de Overpass de relaciones admin_level=8."""
        import osm2geojson
        from shapely.geometry import shape
        gj = osm2geojson.json2geojson(json.load(open(path, encoding="utf-8")))
        polys, names = [], []
        for f in gj.get("features", []):
            geom = f.get("geometry")
            if not geom:
                continue
            props = f.get("properties", {})
            nm = props.get("tags", {}).get("name") or props.get("name")
            try:
                polys.append(shape(geom))
                names.append(nm)
            except Exception:
                continue
        return cls(polys, names)

    @classmethod
    def from_geojson(cls, path, name_prop="name"):
        from shapely.geometry import shape
        gj = json.load(open(path, encoding="utf-8"))
        polys, names = [], []
        for f in gj.get("features", []):
            geom = f.get("geometry")
            if not geom:
                continue
            try:
                polys.append(shape(geom))
                names.append(f.get("properties", {}).get(name_prop))
            except Exception:
                continue
        return cls(polys, names)

    def municipio_de(self, lat, lon):
        if self._tree is None or lat is None or lon is None:
            return None
        from shapely.geometry import Point
        p = Point(lon, lat)
        for i in self._tree.query(p):
            idx = int(i)
            if self._polys[idx].contains(p):
                return self._names[idx]
        return None

    def asignar(self, osm_records):
        """Asigna `.municipio` y `.municipio_norm` a cada OSMRecord in situ."""
        n = 0
        for o in osm_records:
            m = self.municipio_de(o.lat, o.lon)
            o.municipio = m
            o.municipio_norm = norm_municipio(m) if m else None
            if m:
                n += 1
        return n
