# -*- coding: utf-8 -*-
"""Scorer determinista (sin IA) de concesiones BDNS para rehabilitación de
inmuebles inmatriculados.

Tres señales independientes que se combinan en una fiabilidad 0..1:

  1. NIF del beneficiario  → `clasificar_nif`
       R = entidad religiosa inscrita (RER): ancla determinista.
       G = asociación / fundación: incluye el punto ciego de las fundaciones
           confesionales (diocesanas, colegios/hospitales religiosos); requiere
           contexto léxico para confirmarse.
  2. Finalidad de la convocatoria/concesión → `detectar_finalidad_rehab`
       familias de raíces con peso (rehabilitación, conservación, patrimonio,
       elementos constructivos, tipología de templo) + vetos que suprimen los
       falsos positivos (rehabilitación de personas, gremios seculares…).
  3. Cruce con el censo (lo aporta el analyzer): el beneficiario es una entidad
     religiosa conocida y/o tiene inmuebles inmatriculados.

Diseño alineado con el motor de entidades religiosas del proyecto: pesos por
familia de raíz + vetos. La fórmula es estable y auditable: cada punto suma una
señal trazable en `senales`.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


# --- normalización -------------------------------------------------------------
def _strip_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    """minúsculas, sin acentos, espacios colapsados."""
    return re.sub(r"\s+", " ", _strip_acentos(s or "").lower()).strip()


# ============================================================================
# 1. NIF
# ============================================================================
RE_NIF = re.compile(r"^\s*([A-Za-z])\s*\d", re.IGNORECASE)


@dataclass
class ClaseNif:
    letra: Optional[str]      # 'R' / 'G' / otra / None
    clase: str                # 'religiosa' / 'asociacion_fundacion' / 'otro' / 'desconocido'
    peso: float               # aporte a la fiabilidad (0..1)
    en_alcance: bool          # True solo para R y G (el resto se descarta)


def clasificar_nif(nif: str) -> ClaseNif:
    """Clasifica el beneficiario por la letra inicial del NIF.

    R → entidad religiosa (Registro de Entidades Religiosas). Ancla fuerte.
    G → asociación/fundación (sin máscara RGPD en BDNS). Confesional o no:
        peso base menor, a confirmar por finalidad/nombre.
    """
    m = RE_NIF.match(nif or "")
    if not m:
        return ClaseNif(letra=None, clase="desconocido", peso=0.0, en_alcance=False)
    letra = m.group(1).upper()
    if letra == "R":
        return ClaseNif(letra="R", clase="religiosa", peso=0.35, en_alcance=True)
    if letra == "G":
        return ClaseNif(letra="G", clase="asociacion_fundacion", peso=0.15, en_alcance=True)
    return ClaseNif(letra=letra, clase="otro", peso=0.0, en_alcance=False)


# ============================================================================
# 2. Finalidad (rehabilitación / conservación de edificios)
# ============================================================================
# Familias de raíces POSITIVAS (peso) — se cuentan una sola vez por familia.
_FAMILIAS_POS: list[tuple[str, float, list[str]]] = [
    ("rehabilitacion", 0.30, [r"rehabilit", r"restaur", r"\brehab\b"]),
    ("conservacion",   0.18, [r"conservaci", r"consolidaci", r"restituci", r"reparaci"]),
    ("patrimonio",     0.20, [r"patrimoni", r"\bbic\b", r"bien\s+de\s+inter[eé]s\s+cultural",
                              r"monument", r"hist[oó]rico[- ]art[ií]stic", r"catalogad"]),
    ("elemento",       0.12, [r"cubiert", r"fachad", r"tejad", r"\btorre\b", r"campanari",
                              r"retablo", r"[oó]rgano", r"b[oó]veda", r"ptura", r"artesonad"]),
    ("templo",         0.15, [r"iglesi", r"templo", r"ermita", r"capill", r"bas[ií]lic",
                              r"santuari", r"convent", r"monasteri", r"catedral",
                              r"parroqui", r"claustr", r"abad[ií]a"]),
]

# Vetos: la palabra "rehabilitación" NO se refiere a un edificio.
_VETO_FINALIDAD = re.compile(
    r"(rehabilitaci[oó]n\s+(psicosocial|funcional|integral\s+de\s+personas|laboral))"
    r"|(drogodepend|toximan|toxicoman|reinserci|inserci[oó]n\s+laboral|salud\s+mental|"
    r"fisioterap|logoped|terapia\s+ocupacional|discapac\w*\s+(intelectual|f[ií]sica))",
    re.IGNORECASE,
)


@dataclass
class Finalidad:
    es_rehab_edificio: bool
    peso: float                       # 0..1 aporte de la finalidad
    senales: list = field(default_factory=list)
    vetada: bool = False


def detectar_finalidad_rehab(*textos: str) -> Finalidad:
    """Evalúa si la finalidad es rehabilitación/conservación de un edificio.

    Recibe los textos relevantes de la convocatoria y/o concesión (finalidad,
    convocatoria, instrumento, descripción). Devuelve el aporte de peso y las
    familias detectadas. Si dispara un veto, la finalidad queda anulada.
    """
    t = _norm(" ".join(x for x in textos if x))
    if not t:
        return Finalidad(es_rehab_edificio=False, peso=0.0, senales=[], vetada=False)

    if _VETO_FINALIDAD.search(t):
        return Finalidad(es_rehab_edificio=False, peso=0.0, senales=["veto_no_edificio"], vetada=True)

    peso = 0.0
    senales: list[str] = []
    for nombre, w, raices in _FAMILIAS_POS:
        if any(re.search(r, t) for r in raices):
            peso += w
            senales.append(nombre)

    # Es rehabilitación de edificio si hay acción (rehab/conservación) y, o bien
    # tipología de templo/patrimonio, o bien un elemento constructivo concreto.
    accion = ("rehabilitacion" in senales) or ("conservacion" in senales)
    contexto = any(s in senales for s in ("templo", "patrimonio", "elemento"))
    es = accion and contexto
    return Finalidad(es_rehab_edificio=es, peso=min(peso, 0.55), senales=senales, vetada=False)


# ============================================================================
# 3. Vetos de gremio secular sobre el NOMBRE del beneficiario
# ============================================================================
# Cofradías/hermandades seculares que NO son entidad católica: el contexto
# gremial suprime la señal religiosa del nombre (no la del NIF-R, que es legal).
_VETO_GREMIO = re.compile(
    r"(cofrad[ií]a\s+de\s+pescador|mareant|p[oó]sito|donant\w*\s+de\s+sangre|"
    r"labrador|regant|gastron[oó]mic|hermandad\s+de\s+labrador|"
    r"sociedad\s+gastron[oó]mica)",
    re.IGNORECASE,
)
# Léxico que confirma carácter religioso en un nombre (útil sobre todo para G).
_LEXICO_RELIGIOSO = re.compile(
    r"(parroqui|di[oó]cesi|arzobisp|obispad|cofrad[ií]a|hermandad|cabildo|"
    r"\bsanta?\b|virgen|sant[ií]sim|nuestra\s+se[nñ]ora|orden\s+(franciscan|"
    r"dominic|carmelit|jesuit)|fundaci[oó]n\s+(di[oó]cesan|santa|san\b))",
    re.IGNORECASE,
)


def nombre_es_religioso(nombre: str) -> bool:
    """True si el nombre del beneficiario delata carácter religioso y NO es un
    gremio secular. Se usa para reforzar (no para vetar) la señal de NIF-G."""
    n = _norm(nombre)
    if not n:
        return False
    if _VETO_GREMIO.search(n):
        return False
    return bool(_LEXICO_RELIGIOSO.search(n))


# ============================================================================
# Fiabilidad combinada
# ============================================================================
@dataclass
class Fiabilidad:
    valor: float                      # 0..1
    es_candidato: bool                # supera el alcance mínimo (NIF R/G + finalidad)
    senales: list = field(default_factory=list)
    detalle: dict = field(default_factory=dict)


def evaluar(
    nif: str,
    nombre: str,
    *textos_finalidad: str,
    bonus_censo: float = 0.0,
    senales_censo: Optional[list] = None,
) -> Fiabilidad:
    """Combina NIF + finalidad + cruce con censo en una fiabilidad 0..1.

    `bonus_censo` lo aporta el analyzer tras cruzar con la BD (p. ej. +0.25 si el
    beneficiario es una entidad religiosa con inmuebles inmatriculados).
    """
    clase = clasificar_nif(nif)
    fin = detectar_finalidad_rehab(*textos_finalidad)

    senales: list[str] = []
    detalle: dict = {
        "nif_letra": clase.letra,
        "nif_clase": clase.clase,
        "nif_peso": clase.peso,
        "finalidad_senales": fin.senales,
        "finalidad_peso": fin.peso,
        "finalidad_vetada": fin.vetada,
        "es_rehab_edificio": fin.es_rehab_edificio,
        "bonus_censo": bonus_censo,
    }

    if not clase.en_alcance:
        return Fiabilidad(valor=0.0, es_candidato=False, senales=["nif_fuera_de_alcance"], detalle=detalle)

    senales.append(f"nif_{clase.clase}")
    valor = clase.peso

    if fin.vetada:
        # Finalidad explícitamente no-edificio → no es candidato aunque el NIF sea R.
        return Fiabilidad(valor=0.0, es_candidato=False,
                          senales=senales + ["finalidad_vetada"], detalle=detalle)

    valor += fin.peso
    senales.extend(fin.senales)

    # Refuerzo del nombre para NIF-G (confirma punto ciego confesional)
    if clase.letra == "G" and nombre_es_religioso(nombre):
        valor += 0.12
        senales.append("nombre_religioso")
        detalle["nombre_religioso"] = True

    if bonus_censo:
        valor += bonus_censo
        if senales_censo:
            senales.extend(senales_censo)

    valor = max(0.0, min(valor, 1.0))
    # Candidato: NIF en alcance + finalidad es rehabilitación de edificio.
    es_candidato = fin.es_rehab_edificio
    detalle["fiabilidad"] = round(valor, 3)
    return Fiabilidad(valor=valor, es_candidato=es_candidato, senales=senales, detalle=detalle)
