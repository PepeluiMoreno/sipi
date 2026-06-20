#!/usr/bin/env python3
"""
transform/cee/scraper_diocesis.py — extrae datos de diócesis del portal CEE

Fuente: https://www.conferenciaepiscopal.es/es/iglesia-en-espana/diocesis/
Salida: data/output/cee/diocesis.json

Extrae por cada diócesis:
  - nombre, provincia_eclesiastica
  - direccion (nombre_via, codigo_postal, municipio, provincia_nombre)
  - telefono, telefono2, email, sitio_web
  - obispo_nombre, obispo_url, obispo_foto_url

Uso:
    python transform/cee/scraper_diocesis.py
    python transform/cee/scraper_diocesis.py --delay 2.0
    python transform/cee/scraper_diocesis.py --out data/output/cee/diocesis.json
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL    = "https://www.conferenciaepiscopal.es"
INDEX_URL   = f"{BASE_URL}/diocesis/"
OUT_DEFAULT = Path(__file__).parent.parent.parent / "data" / "output" / "cee" / "diocesis.json"

HEADERS = {
    "User-Agent": "SIPI-ETL/1.0 (investigacion patrimonial; contacto interno)",
    "Accept-Language": "es-ES,es;q=0.9",
}

# URLs a ignorar en el índice (no son diócesis territoriales)
EXCLUIR_SLUGS = {"ordinariato-para-los-catolicos-orientales-en-espana"}


# ── Índice ───────────────────────────────────────────────────────────────────

def obtener_urls_diocesis(session: requests.Session) -> list[dict]:
    """
    Obtiene la lista de {nombre_corto, url} desde el índice CEE.

    El índice presenta las diócesis en una <figure class="wp-block-table">
    con una tabla cuyas celdas contienen un <a href> por diócesis.
    """
    log.info(f"GET {INDEX_URL}")
    r = session.get(INDEX_URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tabla = soup.find("figure", class_="wp-block-table")
    if not tabla:
        # Fallback: buscar cualquier table en el contenido
        content = soup.find("div", class_="entry-content") or soup.find("main")
        tabla = content.find("table") if content else None

    if not tabla:
        log.error("No se encontró la tabla de diócesis en el índice")
        return []

    diocesis = []
    seen = set()
    for a in tabla.find_all("a", href=True):
        href = a["href"]
        url = href if href.startswith("http") else BASE_URL + href
        slug = url.rstrip("/").split("/")[-1]

        if slug in EXCLUIR_SLUGS or url in seen:
            continue
        seen.add(url)

        diocesis.append({
            "nombre_corto": a.get_text(strip=True),
            "url": url,
            "es_archidiocesis": "archidiocesis-de" in url or "arzobispado" in url,
        })

    log.info(f"  → {len(diocesis)} entradas en el índice")
    return diocesis


# ── Detalle ──────────────────────────────────────────────────────────────────

def _texto_p(p) -> str:
    return p.get_text(" ", strip=True) if p else ""


def parsear_diocesis(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", class_="entry-content")
    if not content:
        return {"url": url, "_error": "sin entry-content"}

    data: dict = {"url": url}
    parrafos = [p for p in content.find_all("p") if p.get_text(strip=True)]

    # ── Nombre y provincia eclesiástica ──────────────────────────────────────
    for p in parrafos:
        texto = _texto_p(p)
        # Con provincia: "Diócesis de X. Provincia eclesiástica de Y"
        m = re.match(
            r"(?:Archi)?[Dd]i[oó]cesis\s+de\s+(.+?)\s*[.–]\s*Provincia eclesi[aá]stica\s+de\s+(.+)",
            texto,
        )
        if m:
            data["nombre"] = m.group(1).strip()
            data["provincia_eclesiastica"] = m.group(2).strip()
            break
        # Sin provincia (archidiócesis cabeza de provincia): "Archidiócesis de X"
        m2 = re.match(r"Archidi[oó]cesis\s+de\s+(.+?)[\s.]*$", texto)
        if m2:
            data["nombre"] = m2.group(1).strip()
            break
        # Arzobispado Castrense y otros especiales
        m3 = re.match(r"Arzobispado\s+(.+?)[\s.]*$", texto)
        if m3:
            data["nombre"] = m3.group(1).strip()
            break

    # Fallback: h1 limpiando el prefijo
    if "nombre" not in data:
        h1 = soup.find("h1")
        if h1:
            h1_txt = h1.get_text(strip=True)
            h1_txt = re.sub(r"^(?:Archi)?[Dd]i[oó]cesis\s+de\s+|^Arzobispado\s+", "", h1_txt).strip()
            data["nombre"] = h1_txt

    # ── Contacto (dirección, teléfono, email) ────────────────────────────────
    contacto_idx = None
    for i, p in enumerate(parrafos):
        strong = p.find("strong")
        if strong and "Contacto" in strong.get_text():
            contacto_idx = i
            break

    if contacto_idx is not None:
        # La dirección puede estar inline en el mismo párrafo o en los siguientes
        lineas_contacto = []
        p_contacto = parrafos[contacto_idx]
        texto_inline = p_contacto.get_text(" ", strip=True)
        texto_inline = re.sub(r"Contacto\s*:\s*", "", texto_inline).strip()
        if texto_inline:
            lineas_contacto.append(texto_inline)

        for p in parrafos[contacto_idx + 1:]:
            texto = _texto_p(p)
            # Paramos cuando encontramos teléfono, email, obispo u otro bloque
            if re.search(r"\d{3}[\s\-–]\d{3}", texto):
                break
            if "@" in texto or texto.lower().startswith("obispo") or texto.lower().startswith("más info"):
                break
            if any(key in texto.lower() for key in ["guía y estructura", "actividades", "parroquias"]):
                break
            lineas_contacto.append(texto)

        if lineas_contacto:
            direccion_raw = " | ".join(lineas_contacto)
            data["direccion_raw"] = direccion_raw

            # Intentar extraer código postal y municipio
            m_cp = re.search(r"(\d{5})\s+(.+?)(?:\s*\((.+?)\))?\s*$", direccion_raw)
            if m_cp:
                data["codigo_postal"] = m_cp.group(1)
                data["municipio_nombre"] = m_cp.group(2).strip()
                if m_cp.group(3):
                    data["provincia_nombre"] = m_cp.group(3).strip()
            # La parte antes del CP es el nombre de la vía
            if "codigo_postal" in data:
                via = direccion_raw.split(data["codigo_postal"])[0].strip().strip("|").strip()
                if via:
                    data["nombre_via"] = via

    # ── Teléfonos ────────────────────────────────────────────────────────────
    for p in parrafos:
        texto = _texto_p(p)
        if re.search(r"\d{3}[\s\-–]\d{3}[\s\-–]\d{3}", texto):
            telefonos = re.findall(r"\d{3}[\s\-–]\d{3}[\s\-–]\d{3,4}", texto)
            telefonos = [re.sub(r"[\s–\-]", " ", t).strip() for t in telefonos]
            if telefonos:
                data["telefono"] = telefonos[0]
            if len(telefonos) > 1:
                data["telefono2"] = telefonos[1]
            break

    # ── Email ────────────────────────────────────────────────────────────────
    for p in parrafos:
        texto = _texto_p(p)
        m = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", texto)
        if m:
            data["email"] = m.group(0)
            break

    # ── Obispo ───────────────────────────────────────────────────────────────
    for p in parrafos:
        texto = _texto_p(p)
        if re.match(r"Obispo\s*:|Arzobispo\s*:|Administrador\s+apostólico\s*:", texto, re.I):
            a_obispo = p.find("a", href=True)
            if a_obispo:
                data["obispo_nombre"] = a_obispo.get_text(strip=True)
                href = a_obispo["href"]
                data["obispo_url"] = href if href.startswith("http") else BASE_URL + href
            else:
                # Nombre sin enlace
                nombre = re.sub(r"^(Obispo|Arzobispo|Administrador apostólico)\s*:\s*", "", texto, flags=re.I)
                data["obispo_nombre"] = nombre.strip()
            break

    # ── Foto del obispo ──────────────────────────────────────────────────────
    fig = content.find("figure")
    if fig:
        img = fig.find("img")
        a_fig = fig.find("a", href=True)
        if a_fig and a_fig["href"].endswith((".jpg", ".jpeg", ".png", ".webp")):
            data["obispo_foto_url"] = a_fig["href"]
        elif img and img.get("src"):
            data["obispo_foto_url"] = img["src"]

    # ── Sitio web ────────────────────────────────────────────────────────────
    # Buscar específicamente párrafos con "Más información:" o "Web diocesana:"
    # y cuyo enlace apunte a un dominio externo (no conferenciaepiscopal.es)
    for p in parrafos:
        texto = _texto_p(p)
        if "más información" in texto.lower() or "web diocesana" in texto.lower():
            a = p.find("a", href=True)
            if a:
                href = a["href"]
                if "conferenciaepiscopal.es" not in href:
                    data["sitio_web"] = href
            break

    return data


# ── Main ─────────────────────────────────────────────────────────────────────

def main(out_path: Path, delay: float):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    urls = obtener_urls_diocesis(session)
    if not urls:
        log.error("No se obtuvieron URLs. Revisar estructura del índice CEE.")
        return

    resultados = []
    errores = []

    for i, entry in enumerate(urls, 1):
        url = entry["url"]
        log.info(f"[{i}/{len(urls)}] GET {url}")
        try:
            r = session.get(url, timeout=20)
            r.raise_for_status()
            datos = parsear_diocesis(url, r.text)
            resultados.append(datos)
            if "_error" in datos:
                errores.append(url)
        except Exception as e:
            log.warning(f"  Error en {url}: {e}")
            errores.append(url)
        time.sleep(delay)

    out_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"✓ {len(resultados)} diócesis → {out_path}")
    if errores:
        log.warning(f"  {len(errores)} con error: {errores}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de diócesis CEE")
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Segundos entre peticiones (default: 1.5)")
    args = parser.parse_args()
    main(args.out, args.delay)
