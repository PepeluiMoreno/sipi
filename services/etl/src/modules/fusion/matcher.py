# -*- coding: utf-8 -*-
"""Emparejamiento (entity resolution) entre registros CEE y OSM.

Parámetros (pesos, umbrales, cap de bloqueo) provienen de `DiscoveryConfig`, de
modo que el módulo de investigación pueda ajustarlos sin tocar esta lógica. Si no
se pasa config, se usan los valores por defecto validados sobre Pontevedra.

- **Bloqueo por municipio** (recomendado): solo se comparan CEE y OSM del mismo
  municipio (asignado a OSM por reverse-geocoding). Geográficamente confirmado ->
  alta precisión. Para municipios CEE sin join se cae a candidatos de provincia,
  pero topando la banda en MEDIA (nunca auto-fusión), porque una coincidencia de
  nombre entre municipios distintos suele ser falso positivo (~58 % lo eran).
- **Province-wide** (sin geo): bloqueo por token de advocación distintivo.
"""
import collections
import difflib
from dataclasses import dataclass

from .config import DiscoveryConfig
from .geo import norm_municipio
from .normalize import strip_accents, tipo_score

__all__ = ["Match", "match_cee_osm", "ALTA", "MEDIA"]

# Constantes de compatibilidad (los valores por defecto de DiscoveryConfig).
ALTA, MEDIA = DiscoveryConfig.umbral_alta, DiscoveryConfig.umbral_media


@dataclass
class Match:
    cee: object
    osm: object  # OSMRecord o None
    score: float
    name_sim: float
    tipo_sim: float
    band: str
    geo_confirmado: bool = False


def _name_sim(a_tokens, b_tokens, cfg) -> float:
    if not a_tokens or not b_tokens:
        return 0.0
    a, b = set(a_tokens), set(b_tokens)
    jac = len(a & b) / len(a | b)
    seq = difflib.SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    return cfg.peso_jaccard * jac + cfg.peso_secuencia * seq


def _band(score, cfg):
    if score >= cfg.umbral_alta:
        return "ALTA"
    if score >= cfg.umbral_media:
        return "MEDIA"
    return "BAJA"


def _best(c, candidates, cfg, geo_mode):
    best = None
    for o in candidates:
        ns = _name_sim(c.tokens, o.tokens, cfg)
        ts = tipo_score(c.tipo_canon, o.tipo_canon)
        bonus = 0.0
        if not geo_mode and getattr(o, "city", "") and \
                strip_accents(o.city) == strip_accents(c.municipio):
            bonus = cfg.bonus_municipio
        score = cfg.peso_nombre * ns + cfg.peso_tipo * ts + bonus
        if best is None or score > best[0]:
            best = (score, o, ns, ts)
    return best


def match_cee_osm(cee, osm, use_geo=True, province_fallback=True, config=None):
    """Empareja cada registro CEE con su mejor candidato OSM.

    `config` (DiscoveryConfig) externaliza pesos/umbrales. Devuelve
    (matches, set de índices OSM emparejados en ALTA/MEDIA).
    """
    cfg = config or DiscoveryConfig()
    has_geo = use_geo and any(getattr(o, "municipio_norm", None) for o in osm)

    by_muni = collections.defaultdict(list)
    muni_keys = set()
    if has_geo:
        for o in osm:
            if o.municipio_norm:
                by_muni[o.municipio_norm].append(o)
                muni_keys.add(o.municipio_norm)

    df = collections.Counter()
    for o in osm:
        for t in o.tokens:
            df[t] += 1
    cap = max(3, cfg.cap_token_distintivo_ratio * max(1, len(osm)))
    tok_index = collections.defaultdict(list)
    for o in osm:
        for t in o.tokens:
            if df[t] <= cap:
                tok_index[t].append(o)

    def muni_block(c):
        k = norm_municipio(c.municipio)
        if k in by_muni:
            return by_muni[k]
        for kk in muni_keys:
            if k and (k in kk or kk in k):
                return by_muni[kk]
        return None

    def token_block(c):
        out, seen = [], set()
        for t in c.tokens:
            for o in tok_index.get(t, ()):
                if id(o) not in seen:
                    seen.add(id(o)); out.append(o)
        return out

    matches, matched = [], set()
    osm_id_to_idx = {id(o): j for j, o in enumerate(osm)}

    for c in cee:
        geo_conf, cands = False, None
        if has_geo:
            cands = muni_block(c)
            geo_conf = cands is not None
        if not cands and province_fallback:
            cands = token_block(c)
        best = _best(c, cands, cfg, geo_mode=geo_conf) if cands else None

        if best and best[0] > 0:
            score, o, ns, ts = best
            band = _band(score, cfg)
            if not geo_conf and band == "ALTA":
                band = "MEDIA"  # sin confirmación geográfica no hay auto-fusión
            matches.append(Match(c, o, score, ns, ts, band, geo_conf))
            if band in ("ALTA", "MEDIA"):
                matched.add(osm_id_to_idx[id(o)])
        else:
            matches.append(Match(c, None, 0.0, 0.0, 0.0, "SIN_MATCH", False))
    return matches, matched
