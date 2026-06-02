"""Fusión inteligente de bienes religiosos: CEE (inmatriculaciones) × OSM.

Entity resolution bilingüe (es/gl) entre el listado CEE (sin coordenadas) y
los bienes religiosos de OpenStreetMap (con coordenadas), produciendo un seed
de Inmuebles con procedencia y bandas de confianza.
"""
from .sources import load_cee, load_osm, CEERecord, OSMRecord
from .matcher import match_cee_osm, Match
from .seed import run_fusion, write_outputs, FusedEntity

__all__ = [
    "load_cee", "load_osm", "CEERecord", "OSMRecord",
    "match_cee_osm", "Match", "run_fusion", "write_outputs", "FusedEntity",
]
