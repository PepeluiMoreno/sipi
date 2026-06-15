# -*- coding: utf-8 -*-
"""Normalización de nombres de bienes religiosos (castellano + gallego).

Convierte títulos del CEE (descriptivos) y nombres de OSM (bilingües) a un
conjunto de *tokens canónicos* comparables:

- quita acentos y pasa a minúsculas,
- elimina las palabras de tipo (iglesia/igrexa, capilla/capela, ermita/ermida…),
- elimina conectores y tratamientos (de, da, san, santa, nuestra señora…),
- normaliza hagiónimos gallego→castellano (Xoán→juan, Paio→pelayo…),
- extrae la advocación del título descriptivo del CEE.

El objetivo es que "Capilla de San Roque" (CEE, es) y "Capela de San Roque"
(OSM, gl) produzcan los mismos tokens: {roque}.
"""
import re
import unicodedata

__all__ = ["strip_accents", "canon_tokens", "extract_advocacion", "tipo_canon", "tipo_score"]


def strip_accents(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


# Palabras que denotan el *tipo* de bien (es + gl + en) — se eliminan del nombre
TIPO_KW = [
    "concatedral", "catedral", "basilica", "colegiata", "santuario",
    "monasterio", "mosteiro", "convento", "abadia", "iglesia", "igrexa",
    "parroquia", "parroquial", "capilla", "capela", "ermita", "ermida",
    "oratorio", "templo", "cementerio", "camposanto", "casa rectoral",
    "rectoral", "casa parroquial", "cripta",
]
TIPO_TOKENS = set()
for _k in TIPO_KW:
    TIPO_TOKENS.update(_k.split())
TIPO_TOKENS |= {
    "church", "chapel", "hermitage", "cathedral", "sanctuary", "monastery",
    "convent", "place", "worship", "of", "san", "santo", "santa", "sta",
    "sto", "sao",
}

# Conectores y tratamientos sin valor discriminante
STOP = set(
    "de del la el los las do da dos das o a e en con su sus y al lo "
    "nosa nuestra nuestro senora senor virgen advocacion bajo dedicada "
    "dedicado".split()
)

# Hagiónimos / advocaciones gallego -> castellano
GL_ES = {
    "xoan": "juan", "xohan": "juan", "xan": "juan", "breixo": "verisimo",
    "paio": "pelayo", "uxia": "eulalia", "estevo": "esteban",
    "lourenzo": "lorenzo", "vicenzo": "vicente", "marina": "marina",
    "comba": "columba", "andre": "andres", "bartolomeu": "bartolome",
    "xurxo": "jorge", "xacobe": "santiago", "paulo": "pablo", "tome": "tomas",
    "cristovo": "cristobal", "adrao": "adrian", "fins": "felix",
    "trindade": "trinidad",
}


def _gl2es(tok: str) -> str:
    return GL_ES.get(tok, tok)


def canon_tokens(s: str) -> list:
    """Tokens canónicos de un nombre: sin tipo, sin stopwords, gl→es."""
    s = strip_accents(s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [
        t for t in s.split()
        if t and t not in STOP and t not in TIPO_TOKENS and len(t) > 2
    ]
    return [_gl2es(t) for t in toks]


def extract_advocacion(titulo: str) -> str:
    """Extrae el núcleo (tipo + advocación) de un Título descriptivo del CEE.

    Ej.: "Finca en El Chaparral, Bolonia, en la que se sitúa la Ermita del
    Sagrado Corazón, con sus anejos" -> "ermita del sagrado corazon".
    """
    t = strip_accents(titulo)
    pos = None
    for kw in TIPO_KW:
        i = t.find(kw)
        if i != -1 and (pos is None or i < pos):
            pos = i
    frag = t[pos:] if pos is not None else t
    frag = re.split(
        r",|\(|;| con | en la | en el | sita | situad| anejo| dependenc| que |\.",
        frag,
    )[0]
    return frag.strip()


# --- Tipos canónicos comunes a CEE y OSM ---
def tipo_canon(*vals) -> str:
    t = " ".join(strip_accents(v) for v in vals if v)
    if re.search(r"cementerio|camposanto", t):
        return "cementerio"
    if re.search(r"concatedral|catedral|cathedral", t):
        return "catedral"
    if re.search(r"basilica", t):
        return "basilica"
    if re.search(r"ermita|ermida|hermitage", t):
        return "ermita"
    if re.search(r"capilla|capela|chapel", t):
        return "capilla"
    if re.search(r"santuario|sanctuary", t):
        return "santuario"
    if re.search(r"monasterio|mosteiro|monastery|convento|convent|abadia", t):
        return "monasterio"
    if re.search(r"parcela|finca|solar|terreno|huerto", t):
        return "suelo"
    if re.search(r"casa|vivienda|local|edificio|inmueble", t):
        return "edificacion"
    if re.search(r"iglesia|igrexa|church|parroqui|place_of_worship|templo|oratorio", t):
        return "iglesia"
    return "otro"


# Pares de tipos compatibles (mismo bien con distinta clasificación)
_COMPAT = {
    ("iglesia", "catedral"), ("iglesia", "basilica"), ("iglesia", "santuario"),
    ("iglesia", "capilla"), ("capilla", "ermita"), ("iglesia", "ermita"),
    ("iglesia", "monasterio"), ("santuario", "ermita"),
    ("edificacion", "iglesia"),
}


def tipo_score(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if (a, b) in _COMPAT or (b, a) in _COMPAT:
        return 0.6
    if "otro" in (a, b):
        return 0.5
    if {a, b} & {"cementerio", "suelo"}:  # incompatibles fuertes
        return 0.0
    return 0.2
