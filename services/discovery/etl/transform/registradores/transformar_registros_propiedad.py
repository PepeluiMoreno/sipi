#!/usr/bin/env python3
"""
transform/registradores/transformar_registros_propiedad.py
— T4: Normaliza el CSV bruto de Registros de la Propiedad

Lee:    data/input/registradores/registros_propiedad_raw.csv
Genera: data/input/registradores/registros_propiedad.csv

Transformaciones:
  - Extrae codigo_postal de direccion_raw (último número de 5 dígitos)
  - Extrae tipo_via y nombre_via del inicio de la dirección
  - Extrae numero y piso
  - Extrae municipio_slug de url_detalle (penúltimo segmento de ruta)
  - Deriva codigo_oficial del nombre ("Nº 01" → "28-001")
  - Elimina duplicados por url_detalle

Uso:
    python transform/registradores/transformar_registros_propiedad.py
"""

import csv
import re
import sys
import unicodedata
from pathlib import Path

INPUT  = Path(__file__).parent.parent.parent / "data" / "input" / "registradores" / "registros_propiedad_raw.csv"
OUTPUT = Path(__file__).parent.parent.parent / "data" / "input" / "registradores" / "registros_propiedad.csv"

CAMPOS = [
    "codigo_oficial", "nombre",
    "tipo_via_nombre", "nombre_via", "numero", "piso", "codigo_postal",
    "municipio_slug", "codigo_ine_prov", "provincia_nombre",
    "telefono", "email", "nombre_registrador",
    "url_detalle",
]

# Prefijos de tipo de vía → nombre normalizado (debe coincidir con sipi.tipos_via.nombre)
TIPO_VIA_PREFIJOS: list[tuple[str, str]] = [
    (r"avda\.?|avenida",      "Avenida"),
    (r"c/|calle",             "Calle"),
    (r"pza\.?|plaza",         "Plaza"),
    (r"paseo",                "Paseo"),
    (r"ronda",                "Ronda"),
    (r"v[ií]a",               "Vía"),
    (r"camino",               "Camino"),
    (r"ctra\.?|carretera",    "Carretera"),
    (r"traves[ií]a",          "Travesía"),
]
_TIPO_VIA_RE = re.compile(
    r"^(" + "|".join(p for p, _ in TIPO_VIA_PREFIJOS) + r")\s+(.+)",
    re.IGNORECASE,
)


def extraer_tipo_via(texto: str) -> tuple[str, str]:
    """Devuelve (tipo_via_nombre, resto_sin_tipo_via)."""
    m = _TIPO_VIA_RE.match(texto.strip())
    if not m:
        return "", texto.strip()
    prefijo = m.group(1).lower().rstrip(".")
    resto   = m.group(2).strip()
    for patron, nombre in TIPO_VIA_PREFIJOS:
        if re.fullmatch(patron, prefijo, re.IGNORECASE):
            return nombre, resto
    return "", texto.strip()


def parsear_direccion(raw: str) -> dict:
    """
    Extrae tipo_via, nombre_via, numero, piso y codigo_postal de una cadena libre.

    Formato típico:  "Avda. de Guadalajara, 2, 28805"
                     "Infancia, 3 - 1º - Edif. O'Donnell, 28807"
                     "Plaza de España, 1 - 1ª planta, 28013"
    """
    raw = re.sub(r"\s+", " ", raw.strip())

    # CP: último bloque de 4-5 dígitos al final de la cadena.
    # Los CPs españoles son siempre 5 dígitos; algunos registros omiten el cero inicial.
    cp_match = re.search(r"\b(\d{4,5})\s*$", raw)
    if cp_match:
        cp = cp_match.group(1)
        codigo_postal = cp.zfill(5)  # "2005" → "02005"
        sin_cp = raw[: cp_match.start()].rstrip(", ")
    else:
        codigo_postal = ""
        sin_cp = raw

    tipo_via, resto = extraer_tipo_via(sin_cp)

    # Separar por coma: primer token = nombre_via, siguientes = numero/piso/etc.
    partes = [p.strip() for p in resto.split(",")]
    nombre_via = partes[0] if partes else resto

    numero = ""
    piso   = ""
    for parte in partes[1:]:
        # Formato combinado "12 - 2º" → numero="12", piso="2º"
        combinado = re.match(r"^(\d+[A-Za-z]?)\s*[-–]\s*(.+)$", parte)
        if combinado and not numero:
            num_cand = combinado.group(1)
            piso_cand = combinado.group(2).strip()
            if re.search(r"\d+[ºª]|bajo|planta|piso|ent|bj", piso_cand, re.IGNORECASE):
                numero = num_cand
                piso   = piso_cand
                continue

        # Número simple: solo dígitos con posible letra (2, 2A, s/n)
        if not numero and re.match(r"^\d+[A-Za-z]?$|^[Ss]/[Nn]$", parte):
            numero = parte
            continue
        # Piso: contiene ordinal (1º, 2ª, 1ª planta, bajo, etc.)
        if not piso and re.search(r"\d+[ºª]|bajo|planta|piso|ent|bj", parte, re.IGNORECASE):
            piso = re.sub(r"^[-–\s]+", "", parte).strip()
            continue

    return {
        "tipo_via_nombre": tipo_via,
        "nombre_via":      nombre_via,
        "numero":          numero,
        "piso":            piso,
        "codigo_postal":   codigo_postal,
    }


def municipio_slug_desde_url(url: str) -> str:
    """
    /directorio/-/registros/propiedad/madrid/alcala-de-henares/registro-...
    → "alcala-de-henares"
    """
    partes = [p for p in url.rstrip("/").split("/") if p]
    # El último segmento es el slug del registro, el anterior es el municipio
    return partes[-2] if len(partes) >= 2 else ""


def codigo_oficial(nombre: str, codigo_ine_prov: str) -> str:
    """
    "Registro de la Propiedad de Alcalá de Henares Nº 01"  →  "28-001"
    "Registro de la Propiedad de Madrid"                   →  "28-001"  (sin nº → "001")
    """
    m = re.search(r"[Nn][ºo°]\.?\s*(\d+)", nombre)
    num = m.group(1).zfill(3) if m else "001"
    return f"{codigo_ine_prov.zfill(2)}-{num}"


def transformar():
    if not INPUT.exists():
        print(f"ERROR: no encontrado {INPUT}")
        print("       Ejecuta primero: python extract/registradores/descargar_registros_propiedad.py")
        sys.exit(1)

    with open(INPUT, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    vistos: set[str] = set()
    salida: list[dict] = []
    omitidas = 0

    for row in filas:
        url = row.get("url_detalle", "").strip()
        if url in vistos:
            omitidas += 1
            continue
        vistos.add(url)

        nombre = row.get("nombre", "").strip()
        if not nombre:
            omitidas += 1
            continue

        cod_prov = row.get("codigo_ine_prov", "").strip().zfill(2)
        dir_raw  = row.get("direccion_raw", "").strip()

        addr = parsear_direccion(dir_raw)

        salida.append({
            "codigo_oficial":    codigo_oficial(nombre, cod_prov),
            "nombre":            nombre,
            "tipo_via_nombre":   addr["tipo_via_nombre"],
            "nombre_via":        addr["nombre_via"],
            "numero":            addr["numero"],
            "piso":              addr["piso"],
            "codigo_postal":     addr["codigo_postal"],
            "municipio_slug":    municipio_slug_desde_url(url),
            "codigo_ine_prov":   cod_prov,
            "provincia_nombre":  row.get("provincia_nombre", "").strip(),
            "telefono":          row.get("telefono", "").strip()[:20],
            "email":             row.get("email", "").strip()[:255],
            "nombre_registrador": row.get("nombre_registrador", "").strip(),
            "url_detalle":       url,
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(salida)

    print(f"✓ {len(salida)} registros → {OUTPUT}")
    if omitidas:
        print(f"  ({omitidas} duplicados/vacíos omitidos)")
    print("Continúa con:")
    print("  python load/cargar_registros_propiedad.py")


if __name__ == "__main__":
    transformar()
