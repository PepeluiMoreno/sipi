#!/usr/bin/env python3
"""
extract/cee/extract_parroquias.py — extrae parroquias de cada diócesis CEE

Para cada diócesis del JSON de entrada, solicita:
  https://www.conferenciaepiscopal.es/parroquias-de-la-diocesis-de-{slug}/

Estructura de cada celda de la tabla:
  <strong>Nombre municipio<br><em>Titular iglesia</em></strong>
  CP C/ dirección – teléfono (opcional)
  Municipio – Provincia

Salida: data/output/cee/parroquias.json
  Lista de objetos:
    diocesis_slug, diocesis_nombre,
    nombre (municipio/localidad), titular,
    codigo_postal, nombre_via, telefono,
    municipio_nombre, provincia_nombre

Uso:
    python3 extract/cee/extract_parroquias.py
    python3 extract/cee/extract_parroquias.py --delay 1.0
    python3 extract/cee/extract_parroquias.py --diocesis-json data/output/cee/diocesis.json
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL         = "https://www.conferenciaepiscopal.es"
DIOCESIS_DEFAULT = Path(__file__).parent.parent.parent / "data" / "output" / "cee" / "diocesis.json"
OUT_DEFAULT      = Path(__file__).parent.parent.parent / "data" / "output" / "cee" / "parroquias.json"

HEADERS = {
    "User-Agent": "SIPI-ETL/1.0 (investigacion patrimonial; contacto interno)",
    "Accept-Language": "es-ES,es;q=0.9",
}


def slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def nombre_slug(diocesis_url: str) -> str:
    """Devuelve el nombre-slug sin prefijo (ej: 'albacete', 'siguenza-guadalajara')."""
    slug = slug_from_url(diocesis_url)
    return re.sub(r"^(?:archi)?diocesis-de-|^arzobispado-", "", slug)


def url_parroquias(diocesis_url: str, page: int = 1) -> str:
    slug = nombre_slug(diocesis_url)
    base = f"{BASE_URL}/parroquias-de-la-diocesis-de-{slug}/"
    return base if page == 1 else f"{base}page/{page}/"


def url_municipios(diocesis_url: str) -> str:
    slug = nombre_slug(diocesis_url)
    return f"{BASE_URL}/municipios-de-la-diocesis-de-{slug}/"


def parsear_celda(td: Tag, diocesis_slug: str, diocesis_nombre: str) -> dict | None:
    """
    Parsea una celda <td> de la tabla de parroquias.

    Estructura esperada:
      <strong>
        Nombre (municipio o entidad)
        <br>
        <em>Titular de la iglesia</em>
      </strong>
      CP C/ dirección – teléfono
      Municipio – Provincia
    """
    texto = td.get_text("\n", strip=True)
    if not texto:
        return None

    parroquia: dict = {
        "diocesis_slug":   diocesis_slug,
        "diocesis_nombre": diocesis_nombre,
    }

    # ── Nombre y titular ──────────────────────────────────────────────────────
    # Formato A (mayoría): un <strong>Nombre<br><em>Titular</em></strong>
    # Formato B (ej. Jerez): <strong>Nombre</strong><br><strong><em>Titular</em></strong>
    strongs = td.find_all("strong")
    if strongs:
        first_strong = strongs[0]
        em = first_strong.find("em")
        if em:
            # Formato A: em dentro del primer strong
            parroquia["titular"] = em.get_text(strip=True)
            em.extract()
        elif len(strongs) > 1:
            # Formato B: em en el segundo strong
            em2 = strongs[1].find("em")
            if em2:
                parroquia["titular"] = em2.get_text(strip=True)
        parroquia["nombre"] = first_strong.get_text(" ", strip=True).strip()
    else:
        parroquia["nombre"] = texto.split("\n")[0].strip()

    # ── Líneas de texto suelto en el td ──────────────────────────────────────
    # Recogemos los NavigableStrings y el texto de nodos sin strong
    lineas_raw = []
    for node in td.children:
        if isinstance(node, str):
            t = node.strip()
            if t:
                lineas_raw.append(t)
        elif node.name not in ("strong",):
            t = node.get_text(" ", strip=True)
            if t:
                lineas_raw.append(t)

    # Unimos todas las líneas sueltas
    texto_libre = " ".join(lineas_raw)

    # ── Código postal ─────────────────────────────────────────────────────────
    m_cp = re.search(r"\b(\d{5})\b", texto_libre)
    if m_cp:
        parroquia["codigo_postal"] = m_cp.group(1)

    # ── Teléfono ──────────────────────────────────────────────────────────────
    m_tel = re.search(r"[–\-]\s*(\d{9,10})\b", texto_libre)
    if m_tel:
        parroquia["telefono"] = m_tel.group(1)

    # ── Dirección: texto entre CP y teléfono (si existe) ─────────────────────
    if "codigo_postal" in parroquia:
        after_cp = texto_libre.split(parroquia["codigo_postal"], 1)[-1].strip()
        via = re.split(r"[–\-]\s*\d{9}", after_cp)[0]
        via = re.sub(r"\s*[\w\s]+ – [\w\s]+$", "", via).strip()
        if via:
            parroquia["nombre_via"] = via

    # ── Municipio y provincia: línea "Municipio – Provincia" ─────────────────
    # Puede aparecer antes del CP (formato B) o después (formato A).
    # Buscamos en cada línea por separado para no confundirla con la dirección.
    for linea in lineas_raw:
        m_loc = re.search(
            r"([^\d\n–]+?)\s*–\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s/,]+?)\s*$",
            linea.replace("\xa0", "").strip()
        )
        if m_loc and not re.search(r"\d", m_loc.group(2)):
            parroquia["municipio_nombre"] = m_loc.group(1).strip()
            parroquia["provincia_nombre"] = m_loc.group(2).strip()
            break

    return parroquia


def extraer_parroquias_diocesis(url: str, html: str, diocesis_slug: str, diocesis_nombre: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Cada página puede tener N tablas wp-block-table (una por grupo de ~16 parroquias)
    tablas = soup.find_all("figure", class_="wp-block-table")
    if not tablas:
        tablas = soup.find_all("table")
    if not tablas:
        log.warning(f"  Sin tabla de parroquias en {url}")
        return []

    parroquias = []
    for tabla in tablas:
        for td in tabla.find_all("td"):
            p = parsear_celda(td, diocesis_slug, diocesis_nombre)
            if p and p.get("nombre"):
                parroquias.append(p)

    return parroquias


def main(diocesis_json: Path, out_path: Path, delay: float):
    if not diocesis_json.exists():
        log.error(f"No existe {diocesis_json}. Ejecuta primero extract_diocesis.py")
        return

    diocesis_list = json.loads(diocesis_json.read_text(encoding="utf-8"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    todas: list[dict] = []
    errores: list[str] = []

    for i, d in enumerate(diocesis_list, 1):
        diocesis_url    = d.get("url", "")
        diocesis_slug   = slug_from_url(diocesis_url)
        diocesis_nombre = d.get("nombre", diocesis_slug)

        log.info(f"[{i}/{len(diocesis_list)}] {diocesis_nombre}")
        url = url_parroquias(diocesis_url)
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 404:
                log.warning(f"  404 en {url}")
                errores.append(url)
            else:
                r.raise_for_status()
                parroquias = extraer_parroquias_diocesis(url, r.text, diocesis_slug, diocesis_nombre)
                todas.extend(parroquias)
                log.info(f"  → {len(parroquias)} parroquias")
        except Exception as e:
            log.warning(f"  Error en {url}: {e}")
            errores.append(url)
        time.sleep(delay)

    out_path.write_text(json.dumps(todas, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"✓ {len(todas)} parroquias de {len(diocesis_list) - len(errores)} diócesis → {out_path}")
    if errores:
        log.warning(f"  Sin datos en {len(errores)} diócesis: {errores}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrae parroquias de todas las diócesis CEE")
    parser.add_argument("--diocesis-json", type=Path, default=DIOCESIS_DEFAULT)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Segundos entre peticiones (default: 1.5)")
    args = parser.parse_args()
    main(args.diocesis_json, args.out, args.delay)
