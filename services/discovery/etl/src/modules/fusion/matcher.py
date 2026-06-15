# -*- coding: utf-8 -*-
"""Emparejamiento (entity resolution) entre registros CEE y OSM.

Dos modos:

- **Bloqueo por municipio** (recomendado): solo se comparan CEE y OSM del mismo
  municipio (asignado a OSM por reverse-geocoding, ver geo.py). Geográficamente
  confirmado -> alta precisión. Para municipios CEE sin join, se cae a candidatos
  de toda la provincia, pero **topando la banda en MEDIA** (nunca auto-fusión),
  porque una coincidencia de nombre entre municipios distintos suele ser un
  falso positivo (validado: ~58 % de los matches "province-wide" lo eran).

- **Province-wide** (sin geo): bloqueo por token de advocación distintivo.
  Mayor cobertura aparente pero muchos falsos positivos; útil solo como respaldo.

Score = nombre (Jaccard + ratio de secuencia)·0.78 + compatibilidad de tipo·0.22
        (+0.10 si coincide addr:city, en el modo province-wide).
"""
import collections
import difflib
from dataclasses import dataclass

from .geo import norm_municipio
from .normalize import strip_accents, tipo_score

__all__ = ["Match", "match_cee_osm", "ALTA", "MEDIA"]

ALTA, MEDIA = 0.72, 0.50


@dataclass
class Match:
    cee: object
    osm: object  # OSMRecord o None
    score: float
    name_sim: float
    tipo_sim: float
    band: str
    geo_confirmado: bool = False


def _name_sim(a_tokens, b_tokens) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a, b = set(a_tokens), set(b_tokens)
    jac = len(a & b) / len(a | b)
    seq = difflib.SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return 0.6 * jac + 0.4 * seq


def _band(score):
    if score >= ALTA:
        return "ALTA"
    if score >= MEDIA:
        return "MEDIA"
    return "BAJA"


def _best(c, candidates):
    best = None
    for o in candidates:
        ns = _name_sim(c.tokens, o.tokens)
        ts = tipo_score(c.tipo_canon, o.tipo_canon)
        score = 0.78 * ns + 0.22 * ts
        if best is None or score > best[0]:
            best = (score, o, ns, ts)
    return best


def match_cee_osm(cee, osm, use_geo=True, province_fallback=True):
    """Empareja cada registro CEE con su mejor candidato OSM.

    Si `use_geo` y los OSMRecord tienen `municipio_norm`, bloquea por municipio.
    Devuelve (matches, set de índices OSM emparejados en ALTA/MEDIA).
    """
    has_geo = use_geo and any(getattr(o, "municipio_norm", None) for o in osm)

    # índice por municipio normalizado
    by_muni = collections.defaultdict(list)
    muni_keys = set()
    if has_geo:
        for o in osm:
            if o.municipio_norm:
                by_muni[o.municipio_norm].append(o)
                muni_keys.add(o.municipio_norm)

    # índice por token distintivo (province-wide / fallback)
    df = collections.Counter()
    for o in osm:
        for t in o.tokens:
            df[t] += 1
    cap = max(3, 0.25 * max(1, len(osm)))
    tok_index = collections.defaultdict(list)
    for o in osm:
        for t in o.tokens:
            if df[t] <= cap:
                tok_index[t].append(o)

    def muni_block(c):
        k = norm_municipio(c.municipio)
        if k in by_muni:
            return by_muni[k]
        for kk in muni_keys:  # fallback: municipios fusionados (substring)
            if k and (k in kk or kk in k):
                return by_muni[kk]
        return None

    def token_block(c):
        out = []
        seen = set()
        for t in c.tokens:
            for o in tok_index.get(t, ()):
                if id(o) not in seen:
                    seen.add(id(o)); out.append(o)
        return out

    matches = []
    matched = set()
    osm_id_to_idx = {id(o): j for j, o in enumerate(osm)}

    for c in cee:
        geo_conf = False
        cands = None
        if has_geo:
            cands = muni_block(c)
            geo_conf = cands is not None
        if not cands and province_fallback:
            cands = token_block(c)
        best = _best(c, cands) if cands else None

        if best and best[0] > 0:
            score, o, ns, ts = best
            band = _band(score)
            # sin confirmación geográfica no se permite auto-fusión (ALTA -> MEDIA)
            if not geo_conf and band == "ALTA":
                band = "MEDIA"
            matches.append(Match(c, o, score, ns, ts, band, geo_conf))
            if band in ("ALTA", "MEDIA"):
                matched.add(osm_id_to_idx[id(o)])
        else:
            matches.append(Match(c, None, 0.0, 0.0, 0.0, "SIN_MATCH", False))
    return matches, matched
