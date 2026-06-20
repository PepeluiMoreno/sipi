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

    def municipio_de(self, lat, lon, nearest_tol_deg=None):
        """Municipio que contiene el punto (point-in-polygon).

        Si no lo contiene ningún polígono y `nearest_tol_deg` se indica, devuelve
        el municipio del polígono más cercano dentro de esa tolerancia (en grados)
        junto a la marca de que fue por proximidad. Devuelve (nombre, proximidad).
        """
        if self._tree is None or lat is None or lon is None:
            return (None, False)
        from shapely.geometry import Point
        p = Point(lon, lat)
        for i in self._tree.query(p):
            idx = int(i)
            if self._polys[idx].contains(p):
                return (self._names[idx], False)
        # Fallback por proximidad: punto fuera de todo polígono (borde mal trazado,
        # polígono que es casco urbano y no término, coords ligeramente desplazadas...)
        if nearest_tol_deg:
            try:
                j = int(self._tree.nearest(p))
                if self._polys[j].distance(p) <= nearest_tol_deg:
                    return (self._names[j], True)
            except Exception:
                pass
        return (None, False)

    def asignar(self, osm_records, nearest_tol_deg=0.03):
        """Asigna municipio a cada OSMRecord. Devuelve un informe de cobertura.

        `nearest_tol_deg` (~3 km) rescata por proximidad los puntos que caen
        fuera de todo polígono, para no perder inmuebles rurales cuando los
        límites no cubren bien el término. Marca `.municipio_proximidad`.
        """
        dentro = proximidad = sin = 0
        for o in osm_records:
            m, prox = self.municipio_de(o.lat, o.lon, nearest_tol_deg=nearest_tol_deg)
            o.municipio = m
            o.municipio_norm = norm_municipio(m) if m else None
            o.municipio_proximidad = prox
            if m and not prox:
                dentro += 1
            elif m and prox:
                proximidad += 1
            else:
                sin += 1
        total = max(1, len(osm_records))
        informe = {
            "total": len(osm_records), "dentro": dentro,
            "por_proximidad": proximidad, "sin_asignar": sin,
            "cobertura_pct": round(100 * (dentro + proximidad) / total, 1),
            "area_mediana_poligono": self._area_mediana(),
        }
        # Aviso si los polígonos parecen cascos urbanos en vez de términos
        if informe["sin_asignar"] > 0.10 * total:
            informe["aviso"] = ("cobertura baja: los límites podrían ser cascos "
                                "urbanos y no términos municipales; revisar la fuente")
        return informe

    def _area_mediana(self):
        if not self._polys:
            return None
        import statistics
        return round(statistics.median(p.area for p in self._polys), 5)
