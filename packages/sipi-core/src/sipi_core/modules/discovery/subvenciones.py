# -*- coding: utf-8 -*-
"""Subvenciones BDNS → rehabilitación de inmuebles inmatriculados (lógica de dominio).

Fuente ÚNICA de la lógica pura (sin IA, sin red, sin BD), compartida por:
  - el motor de vigilancia de la API (`apps/sipi/api`, ejecución desde el UI), y
  - el batch del consumidor ODM (`services/discovery/etl`).

El transporte HTTP a ODM lo pone cada cliente (httpx en la API, urllib en el
etl); aquí solo viven el scorer determinista, la normalización del registro de
concesión y las funciones puras de resolución recurso→dataset.

Tres señales que se combinan en una fiabilidad 0..1 (ver `evaluar`):
  1. NIF del beneficiario (R = entidad religiosa, ancla; G = asociación/fundación).
  2. Finalidad de rehabilitación/conservación de edificio (familias de raíces + vetos).
  3. Cruce con el censo (lo aporta quien tenga BD: entidad religiosa conocida /
     con inmuebles inmatriculados).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ============================================================================
# normalización
# ============================================================================
def _strip_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    """minúsculas, sin acentos, espacios colapsados."""
    return re.sub(r"\s+", " ", _strip_acentos(s or "").lower()).strip()


_norm = norm  # alias interno


# ============================================================================
# 1. NIF
# ============================================================================
RE_NIF = re.compile(r"^\s*([A-Za-z])\s*\d", re.IGNORECASE)
RE_NIF_RG = re.compile(r"^[RG]\d", re.IGNORECASE)


@dataclass
class ClaseNif:
    letra: Optional[str]
    clase: str          # 'religiosa' / 'asociacion_fundacion' / 'otro' / 'desconocido'
    peso: float
    en_alcance: bool    # True solo para R y G


def clasificar_nif(nif: str) -> ClaseNif:
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

# La palabra "rehabilitación" NO se refiere a un edificio.
_VETO_FINALIDAD = re.compile(
    r"(rehabilitaci[oó]n\s+(psicosocial|funcional|integral\s+de\s+personas|laboral))"
    r"|(drogodepend|toximan|toxicoman|reinserci|inserci[oó]n\s+laboral|salud\s+mental|"
    r"fisioterap|logoped|terapia\s+ocupacional|discapac\w*\s+(intelectual|f[ií]sica))",
    re.IGNORECASE,
)


@dataclass
class Finalidad:
    es_rehab_edificio: bool
    peso: float
    senales: list = field(default_factory=list)
    vetada: bool = False


def detectar_finalidad_rehab(*textos: str) -> Finalidad:
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
    accion = ("rehabilitacion" in senales) or ("conservacion" in senales)
    contexto = any(s in senales for s in ("templo", "patrimonio", "elemento"))
    es = accion and contexto
    return Finalidad(es_rehab_edificio=es, peso=min(peso, 0.55), senales=senales, vetada=False)


# ============================================================================
# Clasificación OBRA (de edificio) vs BIEN MUEBLE
# ----------------------------------------------------------------------------
# El objetivo son OBRAS de rehabilitación de edificios. La restauración de bienes
# muebles (imágenes, retablos, órganos, pintura, orfebrería…) NO es una obra.
# ============================================================================
_OBRA_TOKENS = (
    "cubierta", "tejado", "fachada", "muro", "estructura", "consolidacion",
    "forjado", "cimentacion", "humedad", "accesibilidad", "edificio", "inmueble",
    "templo", "iglesia", "ermita", "convento", "monasterio", "capilla", "catedral",
    "basilica", "santuario", "claustro", "torre", "campanario", "espadana", "nave",
    "abadia", "parroquia", "presbiterio", "abside", "soleria", "carpinteria",
    "instalacion electrica", "saneamiento", "obras", "reforma", "reparacion",
)
_MUEBLE_TOKENS = (
    "imagen", "imagenes", "retablo", "talla", "tallas", "pintura", "lienzo",
    "organo", "escultura", "bienes muebles", "bien mueble", "policromia",
    "orfebreria", "bordado", "manto", "palio", "pictoric", "oleo", "sarga",
    "ajuar", "pieza", "ostensorio", "custodia", "campana", "documental", "archivo",
)


def clasificar_obra(*textos: str) -> str:
    """'obra' | 'mueble' | 'mixto' | 'indet' a partir del título/finalidad.

    - 'obra'  : menciona elementos constructivos/inmuebles y ningún bien mueble.
    - 'mueble': menciona bienes muebles y ningún elemento constructivo.
    - 'mixto' : ambos (p. ej. obra del templo + restauración del retablo).
    - 'indet' : ninguno claro (título genérico tipo "subvención nominativa…").
    """
    t = _norm(" ".join(x for x in textos if x))
    obra = any(k in t for k in _OBRA_TOKENS)
    mueble = any(k in t for k in _MUEBLE_TOKENS)
    if obra and not mueble:
        return "obra"
    if mueble and not obra:
        return "mueble"
    if obra and mueble:
        return "mixto"
    return "indet"


# ============================================================================
# 3. Vetos de gremio secular / refuerzo religioso sobre el NOMBRE
# ============================================================================
_VETO_GREMIO = re.compile(
    r"(cofrad[ií]a\s+de\s+pescador|mareant|p[oó]sito|donant\w*\s+de\s+sangre|"
    r"labrador|regant|gastron[oó]mic|hermandad\s+de\s+labrador|sociedad\s+gastron[oó]mica)",
    re.IGNORECASE,
)
_LEXICO_RELIGIOSO = re.compile(
    r"(parroqui|di[oó]cesi|arzobisp|obispad|cofrad[ií]a|hermandad|cabildo|"
    r"\bsanta?\b|virgen|sant[ií]sim|nuestra\s+se[nñ]ora|orden\s+(franciscan|"
    r"dominic|carmelit|jesuit)|fundaci[oó]n\s+(di[oó]cesan|santa|san\b))",
    re.IGNORECASE,
)


def nombre_es_religioso(nombre: str) -> bool:
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
    valor: float
    es_candidato: bool
    senales: list = field(default_factory=list)
    detalle: dict = field(default_factory=dict)


def evaluar(nif: str, nombre: str, *textos_finalidad: str,
            bonus_censo: float = 0.0, senales_censo: Optional[list] = None) -> Fiabilidad:
    clase = clasificar_nif(nif)
    fin = detectar_finalidad_rehab(*textos_finalidad)
    senales: list[str] = []
    detalle = {
        "nif_letra": clase.letra, "nif_clase": clase.clase, "nif_peso": clase.peso,
        "finalidad_senales": fin.senales, "finalidad_peso": fin.peso,
        "finalidad_vetada": fin.vetada, "es_rehab_edificio": fin.es_rehab_edificio,
        "bonus_censo": bonus_censo,
    }
    if not clase.en_alcance:
        return Fiabilidad(0.0, False, ["nif_fuera_de_alcance"], detalle)
    senales.append(f"nif_{clase.clase}")
    valor = clase.peso
    if fin.vetada:
        return Fiabilidad(0.0, False, senales + ["finalidad_vetada"], detalle)
    valor += fin.peso
    senales.extend(fin.senales)
    if clase.letra == "G" and nombre_es_religioso(nombre):
        valor += 0.12
        senales.append("nombre_religioso")
        detalle["nombre_religioso"] = True
    if bonus_censo:
        valor += bonus_censo
        if senales_censo:
            senales.extend(senales_censo)
    valor = max(0.0, min(valor, 1.0))
    detalle["fiabilidad"] = round(valor, 3)
    return Fiabilidad(valor, fin.es_rehab_edificio, senales, detalle)


# ============================================================================
# Normalización del registro de concesión BDNS (JSONL de ODM)
# ============================================================================
def extraer_nif_nombre(beneficiario: str) -> tuple[str, str]:
    """'R1234567A NOMBRE ENTIDAD' → ('R1234567A', 'NOMBRE ENTIDAD')."""
    parts = (beneficiario or "").split(maxsplit=1)
    nif = parts[0].strip(":-") if parts else ""
    nombre = parts[1].strip() if len(parts) > 1 else ""
    return nif, nombre


def parse_fecha(valor) -> Optional[date]:
    s = str(valor or "")[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


@dataclass
class ConcesionBDNS:
    cod_concesion: str
    beneficiario_raw: str
    nif: str
    nombre: str
    importe: Optional[float]
    fecha_concesion: Optional[date]
    instrumento: Optional[str]
    id_convocatoria: Optional[int]
    numero_convocatoria: Optional[str]
    convocatoria: Optional[str]
    descripcion_cooficial: Optional[str]
    nivel1: Optional[str]
    nivel2: Optional[str]
    nivel3: Optional[str]
    url_bdns: Optional[str]
    raw: dict = field(default_factory=dict)

    def textos_finalidad(self, indice_convocatorias: Optional[dict] = None) -> list[str]:
        txts = [self.convocatoria, self.instrumento, self.descripcion_cooficial]
        if indice_convocatorias and self.id_convocatoria is not None:
            extra = indice_convocatorias.get(self.id_convocatoria)
            if extra:
                txts.append(extra)
        return [t for t in txts if t]


def to_concesion(rec: dict) -> Optional[ConcesionBDNS]:
    """Normaliza un registro JSONL del recurso de concesiones a `ConcesionBDNS`.
    Devuelve None si no es beneficiario con NIF R/G (descarta personas físicas
    enmascaradas por RGPD y otras formas jurídicas fuera de alcance)."""
    cod = rec.get("codConcesion") or ""
    ben = rec.get("beneficiario") or ""
    nif, nombre = extraer_nif_nombre(ben)
    if not cod or not nombre or not RE_NIF_RG.match(nif):
        return None
    return ConcesionBDNS(
        cod_concesion=cod, beneficiario_raw=ben, nif=nif.upper(), nombre=nombre,
        importe=rec.get("importe"), fecha_concesion=parse_fecha(rec.get("fechaConcesion")),
        instrumento=rec.get("instrumento") or None,
        id_convocatoria=rec.get("idConvocatoria"),
        numero_convocatoria=(str(rec.get("numeroConvocatoria") or "") or None),
        convocatoria=rec.get("convocatoria") or None,
        descripcion_cooficial=rec.get("descripcionCooficial") or None,
        nivel1=rec.get("nivel1") or None, nivel2=rec.get("nivel2") or None,
        nivel3=rec.get("nivel3") or None, url_bdns=rec.get("urlBR") or None, raw=rec,
    )


def convocatoria_texto(rec: dict) -> tuple[Optional[int], Optional[str]]:
    """De un registro del recurso de convocatorias: (id, texto de finalidad)."""
    cid = rec.get("id") or rec.get("idConvocatoria")
    if cid is None:
        return None, None
    texto = (rec.get("descripcion") or rec.get("descripcionFinalidad")
             or rec.get("finalidad") or rec.get("objeto") or rec.get("convocatoria") or "")
    try:
        return int(cid), (str(texto) or None)
    except (TypeError, ValueError):
        return None, None


# ============================================================================
# Resolución recurso→dataset (puro: el caller hace el HTTP y pasa los resultados)
# ============================================================================
# Nombres de recurso reales en ODM (contrato neutral; el id es por-instalación).
RESOURCE_CONCESIONES = "BDNS - Concesiones de Subvenciones"
RESOURCE_CONVOCATORIAS = "BDNS - Convocatorias de Subvenciones"

Q_RESOURCES = "{ resources { id name } }"


def q_datasets(resource_id: str) -> str:
    return ("{ datasets(resourceId:\"%s\"){ id majorVersion minorVersion patchVersion "
            "createdAt recordCount } }" % resource_id)


def resolver_recurso_id(resources: list, resource_name: str) -> Optional[str]:
    """De la lista devuelta por Q_RESOURCES, el id cuyo name coincide."""
    for r in resources or []:
        if r.get("name") == resource_name:
            return r.get("id")
    return None


def elegir_ultimo_dataset(datasets: list) -> Optional[str]:
    """De la lista devuelta por q_datasets, el id del de mayor versión."""
    ds = list(datasets or [])
    if not ds:
        return None
    ds.sort(key=lambda d: (d.get("majorVersion") or 0, d.get("minorVersion") or 0,
                           d.get("patchVersion") or 0, d.get("createdAt") or ""))
    return ds[-1]["id"]


# Recursos por ejercicio creados por seed_bdns_ejercicios.py en ODM:
#   "BDNS · Concesiones 2024"  (anual)  /  "BDNS · Concesiones 2025-03"  (mensual)
ETIQUETA_HIST_CONCESIONES = "Concesiones"
_RE_HIJO_EJERCICIO = re.compile(r"^BDNS · (?P<etq>.+?) (?P<anio>20\d{2})(?:-(?P<mes>\d{2}))?$")


def recursos_por_ejercicio(resources: list, etiqueta: str = ETIQUETA_HIST_CONCESIONES) -> list:
    """De la lista de Q_RESOURCES, los hijos por ejercicio de una colección BDNS,
    ordenados de más reciente a más antiguo: [(id, name, (anio, mes))].

    Reconoce tanto hijos anuales ("… 2024") como mensuales ("… 2025-03"); el
    consumidor debe deduplicar por clave de registro (codConcesion) al unir los
    datasets, por si conviven ambas granularidades para un mismo año.
    """
    out = []
    for r in resources or []:
        m = _RE_HIJO_EJERCICIO.match(r.get("name") or "")
        if not m or m.group("etq") != etiqueta:
            continue
        anio = int(m.group("anio"))
        mes = int(m.group("mes")) if m.group("mes") else 0
        out.append((r.get("id"), r.get("name"), (anio, mes)))
    out.sort(key=lambda t: t[2], reverse=True)
    return out
