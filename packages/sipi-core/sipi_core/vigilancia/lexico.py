"""Léxico de detección de beneficio a entidades religiosas o fines filo-religiosos.

Dos diccionarios de términos ponderados (0..1) y patrones de desambiguación:
- ENTIDAD: aparece en nombres de beneficiarios/adjudicatarios.
- OBJETO: aparece en objetos de convocatorias, concesiones o licitaciones.
Los pesos reflejan especificidad: 1.0 = inequívoco, 0.3 = necesita compañía.
"""
import re

# ── Términos de ENTIDAD (beneficiario / adjudicatario) ──────────────────
ENTIDAD = {
    r"arzobispad\w+": 1.0,
    r"obispad\w+": 1.0,
    r"archidi[oó]cesis": 1.0,
    r"di[oó]cesis": 1.0,
    r"parroquia\w*": 1.0,
    r"cabildo\s+catedral\w*": 1.0,
    r"conferencia\s+episcopal": 1.0,
    r"c[aá]ritas": 1.0,
    r"prelatura": 1.0,
    r"vicar[ií]a": 0.9,
    r"arciprestazgo": 1.0,
    r"seminario\s+(conciliar|diocesano|menor|mayor)": 1.0,
    r"convento\w*": 0.9,
    r"monasterio\w*": 0.9,
    r"abad[ií]a": 0.8,
    r"hermandad\w*": 0.8,
    r"archicofrad[ií]a\w*": 1.0,
    r"cofrad[ií]a\w*": 0.9,
    r"congregaci[oó]n\s+(de|religiosa)": 0.9,
    r"instituto\s+de\s+vida\s+consagrada": 1.0,
    r"compa[ñn][ií]a\s+de\s+jes[uú]s": 1.0,
    r"jesuit\w+": 0.9,
    r"salesian\w+": 0.9,
    r"franciscan\w+": 0.9,
    r"dominic[oa]s": 0.8,
    r"carmelit\w+": 0.9,
    r"agustin[oa]s": 0.8,
    r"claretian\w+": 0.9,
    r"escolapi\w+": 0.9,
    r"marist\w+": 0.8,
    r"mercedari\w+": 0.9,
    r"benedictin\w+": 0.9,
    r"cistercien\w+": 0.9,
    r"capuchin\w+": 0.9,
    r"redentorist\w+": 0.9,
    r"pa[uú]les": 0.7,
    r"hijas\s+de\s+la\s+caridad": 1.0,
    r"hermanas\s+de\s+": 0.7,
    r"hermanos\s+de\s+la\s+salle|lasalian\w+": 0.9,
    r"misioner[oa]s\s+de": 0.8,
    r"obra\s+p[ií]a": 0.9,
    r"fundaci[oó]n\s+p[ií]a": 1.0,
    r"opus\s+dei": 1.0,
    r"manos\s+unidas": 0.9,
    r"mezquita\w*": 0.9,
    r"comunidad\s+isl[aá]mica": 1.0,
    r"comunidad\s+(israelita|jud[ií]a)": 1.0,
    r"sinagoga": 0.9,
    r"iglesia\s+(evang[eé]lica|adventista|ortodoxa|bautista|pentecostal|de\s+jesucristo|de\s+dios|de\s+cristo)": 1.0,
    r"testigos\s+de\s+jehov[aá]": 1.0,
    r"catedral\w*": 0.8,
    r"santuario\s+de": 0.8,
}

# ── Términos de OBJETO (fin filo-religioso) ──────────────────────────────
OBJETO = {
    r"templo\w*": 0.8,
    r"iglesia\s+(parroquial|de\s+san\w*|de\s+santa\s|de\s+nuestra\s+se[ñn]ora)": 0.9,
    r"iglesia\w*": 0.5,
    r"catedral\w*": 0.8,
    r"ermita\w*": 0.7,
    r"capilla\w*": 0.6,
    r"santuario\w*": 0.7,
    r"bas[ií]lica\w*": 0.8,
    r"retablo\w*": 0.9,
    r"sacrist[ií]a": 0.9,
    r"campanario|espada[ñn]a": 0.8,
    r"culto\s+(religioso|cat[oó]lico)|lugares?\s+de\s+culto": 1.0,
    r"semana\s+santa": 0.9,
    r"procesi[oó]n\w*|procesional\w*": 0.8,
    r"paso\s+de\s+(misterio|palio|cristo|virgen)": 1.0,
    r"cofrade\w*|cofrad[ií]a\w*|hermandad\w*": 0.8,
    r"romer[ií]a\w*": 0.5,
    r"patrimonio\s+religioso": 1.0,
    r"arte\s+sacro": 0.9,
    r"imagen\s+de\s+(la\s+virgen|nuestro\s+padre|crist\w+|san\w*\s)": 0.9,
    r"virgen\s+de\s+": 0.6,
    r"cristo\s+de\s+": 0.7,
    r"catequesis|pastoral\s+(juvenil|diocesana|penitenciaria)?|evangelizaci[oó]n": 0.9,
    r"capellan[ií]a\w*": 1.0,
    r"misa\s|misas\s": 0.6,
    r"parroquia\w*": 0.9,
    r"di[oó]cesis|obispad\w+|arzobispad\w+": 0.9,
    r"convento\w*|monasterio\w*": 0.7,
    r"bel[eé]n\s+(viviente|monumental|navide[ñn]o)": 0.6,
}

# ── Desambiguación: contexto que NEUTRALIZA un término ──────────────────
# (callejero/toponimia: "calle de la Iglesia", "plaza de la Ermita", "barrio…")
PREFIJOS_TOPONIMICOS = re.compile(
    r"(?:calle|c/|avda\.?|avenida|plaza|pza\.?|barrio|camino|carretera|ctra\.?|"
    r"pol[ií]gono|urbanizaci[oó]n|paraje|pago|finca)\s+(?:de\s+)?(?:la\s+|el\s+|los\s+|las\s+)?$",
    re.IGNORECASE,
)

NIF_RE = re.compile(r"\b([A-HJ-NP-SUVW]|[QR])(\d{7})([A-Z0-9])\b")
