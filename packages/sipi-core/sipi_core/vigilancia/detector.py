"""Detector de beneficio a entidades religiosas / fin filo-religioso.

Tres señales combinadas:
1. NIF del beneficiario con letra R (congregaciones e instituciones religiosas)
   → señal inequívoca.
2. Léxico del NOMBRE del beneficiario/adjudicatario (ENTIDAD).
3. Léxico del OBJETO (convocatoria, concesión, contrato) con desambiguación
   toponímica ("calle de la Iglesia" no puntúa).

Devuelve score 0..1, veredicto y las señales activadas (trazabilidad para la
revisión humana: el vigilante propone, la persona dispone).
"""
import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

from .lexico import ENTIDAD, OBJETO, PREFIJOS_TOPONIMICOS, NIF_RE

UMBRAL_ALERTA = 0.85
UMBRAL_REVISION = 0.40


@dataclass
class Deteccion:
    score: float
    veredicto: str            # 'alerta' | 'revision' | 'sin_indicios'
    senales: List[str] = field(default_factory=list)
    nif: Optional[str] = None


def _normalizar(texto: str) -> str:
    """minúsculas + sin tildes para casar el léxico de forma robusta."""
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.lower()


def _puntuar_lexico(texto: str, lexico: dict, etiqueta: str):
    """Devuelve (mejor_peso, señales) de los términos que casan, descartando
    los precedidos de contexto toponímico (callejero)."""
    if not texto:
        return 0.0, []
    plano = _normalizar(texto)
    mejor, senales = 0.0, []
    for patron, peso in lexico.items():
        for m in re.finditer(patron, plano, re.IGNORECASE):
            contexto_previo = plano[max(0, m.start() - 40):m.start()]
            if PREFIJOS_TOPONIMICOS.search(contexto_previo):
                continue  # "calle de la iglesia" → toponimia, no fin religioso
            senales.append(f"{etiqueta}:{m.group(0).strip()}({peso})")
            mejor = max(mejor, peso)
            break  # un acierto por patrón basta
    return mejor, senales


def extraer_nif(beneficiario: str) -> Optional[str]:
    m = NIF_RE.search(beneficiario or "")
    return "".join(m.groups()) if m else None


def evaluar_textos(nombre_entidad: str = "", textos_objeto: Optional[List[str]] = None) -> Deteccion:
    """Núcleo común: nombre del beneficiario/adjudicatario + textos del objeto."""
    senales: List[str] = []
    score = 0.0

    # Señal 1: NIF letra R → entidad religiosa registrada, sin discusión.
    nif = extraer_nif(nombre_entidad)
    if nif and nif[0] == "R":
        senales.append(f"nif:R({nif})")
        score = 1.0

    # Señal 2: léxico en el nombre de la entidad.
    s2, sen2 = _puntuar_lexico(nombre_entidad, ENTIDAD, "entidad")
    senales += sen2
    score = max(score, s2)

    # Señal 3: léxico en el objeto. Refuerza: objeto + entidad débiles suman.
    s3 = 0.0
    for texto in textos_objeto or []:
        p, sen = _puntuar_lexico(texto, OBJETO, "objeto")
        senales += sen
        s3 = max(s3, p)
    if s3 and s2:
        score = max(score, min(1.0, s3 + 0.25))   # corroboración cruzada
    else:
        score = max(score, s3)

    if score >= UMBRAL_ALERTA:
        veredicto = "alerta"
    elif score >= UMBRAL_REVISION:
        veredicto = "revision"
    else:
        veredicto = "sin_indicios"
    return Deteccion(round(score, 2), veredicto, senales, nif)


def evaluar_concesion(registro: dict) -> Deteccion:
    """Registro de BDNS concesiones (campos: beneficiario, convocatoria,
    instrumento, descripcionCooficial…)."""
    return evaluar_textos(
        nombre_entidad=registro.get("beneficiario") or "",
        textos_objeto=[
            registro.get("convocatoria") or "",
            registro.get("descripcionCooficial") or "",
        ],
    )


def evaluar_convocatoria(registro: dict) -> Deteccion:
    """Registro de BDNS convocatorias (descripcion / descripcionLeng)."""
    return evaluar_textos(
        nombre_entidad="",
        textos_objeto=[
            registro.get("descripcion") or "",
            registro.get("descripcionLeng") or "",
        ],
    )


def evaluar_licitacion(objeto: str, adjudicatario: str = "") -> Deteccion:
    """Licitación/contrato de obras: objeto del contrato + adjudicatario.
    Ojo: en obras, el filo-religioso suele estar en el OBJETO (rehabilitación
    de la iglesia de X) aunque el adjudicatario sea una constructora laica."""
    return evaluar_textos(nombre_entidad=adjudicatario, textos_objeto=[objeto])
