# -*- coding: utf-8 -*-
"""Carga de las dos fuentes a registros homogéneos para la fusión.

- CEE: CSVs normalizados (uno por CCAA) con columnas variables
  (Titulo / Título / Descripción según la hoja). Sin coordenadas.
- OSM: JSON de Overpass (bienes religiosos católicos/cristianos) con
  coordenadas y nombres bilingües (name / name:es / name:gl).
"""
import csv
import glob
import json
import os
from dataclasses import dataclass, field

from .normalize import canon_tokens, extract_advocacion, strip_accents, tipo_canon

__all__ = ["CEERecord", "OSMRecord", "load_cee", "load_osm"]


@dataclass
class CEERecord:
    municipio: str
    provincia: str
    ccaa: str
    registro: str
    titulo: str
    tipo: str
    titular: str
    advocacion: str
    tipo_canon: str
    tokens: list = field(default_factory=list)


@dataclass
class OSMRecord:
    osm_id: str
    name: str
    names: list
    tipo_canon: str
    lat: float
    lon: float
    city: str
    wikidata: str
    tokens: set = field(default_factory=set)
    municipio: str = None        # asignado por reverse-geocoding (geo.py)
    municipio_norm: str = None


def _cee_titulo(row: dict) -> str:
    return row.get("Titulo") or row.get("Título") or row.get("Descripción") or ""


def load_cee(csv_dir: str, provincia: str = None, ccaa: str = None):
    """Carga registros del CEE; filtra por provincia o CCAA si se indica."""
    out = []
    pv = strip_accents(provincia) if provincia else None
    cc = strip_accents(ccaa) if ccaa else None
    for f in sorted(glob.glob(os.path.join(csv_dir, "*.csv"))):
        if "estadistic" in os.path.basename(f):
            continue
        with open(f, encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if pv and strip_accents(row.get("Provincia", "")) != pv:
                    continue
                if cc and strip_accents(row.get("Comunidad Autónoma", "")) != cc:
                    continue
                titulo = _cee_titulo(row)
                adv = extract_advocacion(titulo)
                out.append(CEERecord(
                    municipio=(row.get("Municipio") or "").strip(),
                    provincia=(row.get("Provincia") or "").strip(),
                    ccaa=(row.get("Comunidad Autónoma") or "").strip(),
                    registro=(row.get("REGISTRO") or "").strip(),
                    titulo=titulo,
                    tipo=(row.get("Tipo") or "").strip(),
                    titular=(row.get("Titular") or "").strip(),
                    advocacion=adv,
                    tipo_canon=tipo_canon(row.get("Tipo", ""), titulo),
                    tokens=canon_tokens(adv),
                ))
    return out


def load_osm(json_path: str):
    """Carga elementos OSM (salida Overpass `out tags center`)."""
    d = json.load(open(json_path, encoding="utf-8"))
    out = []
    for e in d.get("elements", []):
        tg = e.get("tags", {})
        names = [n for n in (tg.get("name"), tg.get("name:es"), tg.get("name:gl")) if n]
        if not names:
            continue
        toks = set()
        for n in names:
            toks |= set(canon_tokens(n))
        center = e.get("center") or {}
        out.append(OSMRecord(
            osm_id="%s/%s" % (e.get("type"), e.get("id")),
            name=names[0],
            names=names,
            tipo_canon=tipo_canon(tg.get("building"), tg.get("amenity")),
            lat=e.get("lat") or center.get("lat"),
            lon=e.get("lon") or center.get("lon"),
            city=tg.get("addr:city", ""),
            wikidata=tg.get("wikidata"),
            tokens=toks,
        ))
    return out
