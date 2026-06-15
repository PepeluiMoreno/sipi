# -*- coding: utf-8 -*-
"""Detector léxico determinista de desacralizaciones en boletines diocesanos.

No usa IA: la fórmula canónica es estable y discriminante. Detecta el decreto de
"reducción a uso(s) profano(s)" (c. 1222 §2) y extrae el inmueble afectado.

Diseño alineado con el motor de entidades religiosas: familias de raíces con
peso + vetos para suprimir falsos positivos.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# --- normalización -------------------------------------------------------------
def _strip_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: str) -> str:
    """minúsculas, sin acentos, espacios colapsados."""
    return re.sub(r"\s+", " ", _strip_acentos(s or "").lower()).strip()


# --- patrones ------------------------------------------------------------------
# Fórmula nuclear (ancla determinista). Cubre forma sustantiva ("reducción a
# usos profanos") y verbal ("reducir/reducida/reduce a uso profano").
RX_REDUCCION = re.compile(
    r"reduc\w*\s+a\s+usos?\s+profanos?",
    re.IGNORECASE,
)
# Refuerzos (suben confianza)
RX_CANON_1222 = re.compile(r"\b(c(?:anon|an|\.)?\s*\.?\s*1222)\b", re.IGNORECASE)
RX_SUPRESION_PARROQUIA = re.compile(r"supresi[oó]n\s+de\s+la\s+parroquia", re.IGNORECASE)
RX_DESAFECTACION = re.compile(r"desafectaci[oó]n(?:\s+al\s+culto)?", re.IGNORECASE)
RX_EJECUTORIA = re.compile(r"reducido?\s+a\s+uso\s+profano", re.IGNORECASE)

# Nombre del templo: tras una palabra de tipo religioso + "de"
RX_TEMPLO = re.compile(
    r"\b(iglesia|templo|capilla|ermita|bas[ií]lica|santuario|parroquia|"
    r"convento|monasterio|oratorio)\s+(?:parroquial\s+)?(?:de\s+(?:la\s+|el\s+|los\s+|las\s+)?)?"
    r"([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÜÑáéíóúüñ'’\.\- ]{2,60}?)"
    r"(?=,|\.|\s+de\s+[A-ZÁÉÍÓÚÑ]|\s+en\s+[A-ZÁÉÍÓÚÑ]|\s*$)",
    re.UNICODE,
)
# Municipio: tras el nombre del templo, ", de <Municipio>" o " en <Municipio>"
RX_MUNICIPIO = re.compile(
    r"(?:,\s*de\s+|,?\s+en\s+|\s+de\s+)([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÜÑáéíóúüñ'’\.\- ]{2,50}?)"
    r"(?=[\.,;\n]|\s+Descargar|\s*$)",
    re.UNICODE,
)
# Fecha ISO o "a 14 de marzo de 2025"
RX_FECHA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RX_FECHA_LARGA = re.compile(
    r"\b(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})\b", re.IGNORECASE
)
_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# Vetos: contextos donde "uso profano" NO implica desacralización de un inmueble
# religioso del inventario (citas doctrinales, glosas, derecho comparado…).
RX_VETO = re.compile(
    r"(en\s+general|doctrina|comentario|conferencia|art[ií]culo\s+de\s+opini[oó]n)",
    re.IGNORECASE,
)


@dataclass
class Desacralizacion:
    templo: Optional[str]          # "San Martín", "San Juan Bautista"...
    tipo_templo: Optional[str]     # iglesia / parroquia / convento...
    municipio: Optional[str]
    fecha: Optional[date]
    confianza: int                 # 0-100
    suprime_parroquia: bool = False
    fragmento: str = ""            # span de evidencia
    senales: list = field(default_factory=list)

    def clave(self) -> str:
        return _norm(f"{self.templo}|{self.municipio}")


def _parse_fecha(texto: str) -> Optional[date]:
    m = RX_FECHA_ISO.search(texto)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = RX_FECHA_LARGA.search(texto)
    if m:
        mes = _MESES.get(_strip_acentos(m.group(2).lower()))
        if mes:
            try:
                return date(int(m.group(3)), mes, int(m.group(1)))
            except ValueError:
                pass
    return None


def _ventana(texto: str, ini: int, fin: int, radio: int = 160) -> str:
    a = max(0, ini - radio)
    b = min(len(texto), fin + radio)
    return re.sub(r"\s+", " ", texto[a:b]).strip()


def detectar_desacralizaciones(texto: str, diocesis: Optional[str] = None) -> list[Desacralizacion]:
    """Devuelve las desacralizaciones detectadas en un texto (página de boletín,
    decreto suelto o índice de decretos). Una por aparición de la fórmula nuclear.
    """
    if not texto:
        return []
    resultados: list[Desacralizacion] = []

    for m in RX_REDUCCION.finditer(texto):
        frag = _ventana(texto, m.start(), m.end())          # ventana simétrica: señales + fecha
        post = re.sub(r"\s+", " ", texto[m.end(): m.end() + 240]).strip()  # el templo va TRAS la fórmula
        if RX_VETO.search(frag):
            continue

        senales = ["reduccion_uso_profano"]
        conf = 60  # ancla
        if RX_CANON_1222.search(frag):
            conf += 15; senales.append("canon_1222")
        suprime = bool(RX_SUPRESION_PARROQUIA.search(frag))
        if suprime:
            conf += 15; senales.append("supresion_parroquia")
        if RX_DESAFECTACION.search(frag):
            conf += 5; senales.append("desafectacion")

        # templo + municipio: SIEMPRE hacia delante desde la fórmula
        templo = tipo_templo = municipio = None
        mt = RX_TEMPLO.search(post)
        if mt:
            tipo_templo = mt.group(1).lower()
            templo = mt.group(2).strip(" .,")
            senales.append("templo")
            conf += 5
            mm = RX_MUNICIPIO.search(post, mt.end())
            if mm:
                municipio = mm.group(1).strip(" .,")
                senales.append("municipio")

        resultados.append(Desacralizacion(
            templo=templo,
            tipo_templo=tipo_templo,
            municipio=municipio,
            fecha=_parse_fecha(frag),
            confianza=min(conf, 100),
            suprime_parroquia=suprime,
            fragmento=frag,
            senales=senales,
        ))

    # dedup por (templo, municipio) conservando la de mayor confianza
    mejor: dict[str, Desacralizacion] = {}
    for d in resultados:
        k = d.clave()
        if k not in mejor or d.confianza > mejor[k].confianza:
            mejor[k] = d
    return sorted(mejor.values(), key=lambda d: (-d.confianza, d.templo or ""))
