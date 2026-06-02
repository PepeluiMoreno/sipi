# -*- coding: utf-8 -*-
"""Emparejamiento (entity resolution) entre registros CEE y OSM.

Estrategia:
  1. **Bloqueo** por token de advocación *distintivo* (descarta tokens
     ultra-frecuentes en la provincia para no comparar todo contra todo).
  2. **Score** = nombre (Jaccard de tokens + ratio de secuencia) ·0.75
                 + compatibilidad de tipo ·0.20
                 + bonus si coincide municipio/addr:city ·0.10
  3. **Bandas de confianza**: ALTA (auto-fusión) / MEDIA (cola de revisión)
     / BAJA / SIN_MATCH.

El bloqueo geográfico fino (por municipio) requiere reverse-geocodificar las
coordenadas OSM contra los polígonos de municipio; ver `seed.py` y la nota en
docs/VALIDACION_FUSION.md. Sin él, el bloqueo es a nivel provincia.
"""
import collections
import difflib
from dataclasses import dataclass

from .normalize import strip_accents, tipo_score

__all__ = ["Match", "match_cee_osm", "ALTA", "MEDIA", "BAJA"]

ALTA, MEDIA, BAJA = 0.72, 0.50, 0.0


@dataclass
class Match:
    cee: object
    osm: object  # OSMRecord o None
    score: float
    name_sim: float
    tipo_sim: float
    band: str


def _name_sim(a_tokens, b_tokens) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a, b = set(a_tokens), set(b_tokens)
    jac = len(a & b) / len(a | b)
    seq = difflib.SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return 0.6 * jac + 0.4 * seq


def _band(score: float) -> str:
    if score >= ALTA:
        return "ALTA"
    if score >= MEDIA:
        return "MEDIA"
    return "BAJA"


def match_cee_osm(cee, osm, distinctive_cap_ratio: float = 0.25):
    """Empareja cada registro CEE con su mejor candidato OSM.

    Devuelve (matches, osm_emparejados_idx).
    """
    df = collections.Counter()
    for o in osm:
        for t in o.tokens:
            df[t] += 1
    n = max(1, len(osm))
    cap = max(3, distinctive_cap_ratio * n)

    index = collections.defaultdict(list)
    for j, o in enumerate(osm):
        for t in o.tokens:
            if df[t] <= cap:  # token distintivo -> sirve para bloquear
                index[t].append(j)

    matches = []
    matched = set()
    for c in cee:
        candidates = set()
        for t in c.tokens:
            candidates.update(index.get(t, ()))
        best = None
        for j in candidates:
            o = osm[j]
            ns = _name_sim(c.tokens, o.tokens)
            ts = tipo_score(c.tipo_canon, o.tipo_canon)
            city_bonus = 0.10 if (o.city and strip_accents(o.city) == strip_accents(c.municipio)) else 0.0
            score = 0.75 * ns + 0.20 * ts + city_bonus
            if best is None or score > best[0]:
                best = (score, j, ns, ts)
        if best and best[0] > 0:
            score, j, ns, ts = best
            band = _band(score)
            matches.append(Match(c, osm[j], score, ns, ts, band))
            if band in ("ALTA", "MEDIA"):
                matched.add(j)
        else:
            matches.append(Match(c, None, 0.0, 0.0, 0.0, "SIN_MATCH"))
    return matches, matched
