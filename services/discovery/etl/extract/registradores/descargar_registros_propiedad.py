#!/usr/bin/env python3
"""
extract/registradores/descargar_registros_propiedad.py
— E3: Descarga el catálogo de Registros de la Propiedad desde www.registradores.org

Fuente: Colegio de Registradores de la Propiedad, Bienes Muebles y Mercantiles de España
URL:    https://www.registradores.org/directorio/-/registros/propiedad/<provincia>

Nivel 1 (listado por provincia):
  Selector: ul.listado-registros > li
    - nombre:      <a> texto
    - url_detalle: <a href>

Nivel 2 (ficha de cada registro), div.datosDecanato + div.contactoDecanato:
    - direccion_raw:      primer div.texto-decanato
    - telefono:           div.link-decanato con número
    - email:              div.link-decanato con @
    - nombre_registrador: div.link-decanato tras "Datos del Registrador"

Salida: data/input/registradores/registros_propiedad_raw.csv

Campos CSV:
    nombre, direccion_raw, telefono, email, nombre_registrador,
    url_detalle, provincia_nombre, codigo_ine_prov

Uso:
    python extract/registradores/descargar_registros_propiedad.py
    python extract/registradores/descargar_registros_propiedad.py --provincia 28
    python extract/registradores/descargar_registros_propiedad.py --delay 0.5
    python extract/registradores/descargar_registros_propiedad.py --force
"""

import argparse
import csv
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: instala beautifulsoup4:  pip install beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://www.registradores.org/directorio/-/registros/propiedad"
DESTINO  = Path(__file__).parent.parent.parent / "data" / "input" / "registradores"
FICHERO  = DESTINO / "registros_propiedad_raw.csv"
CAMPOS   = [
    "nombre", "direccion_raw", "telefono", "email", "nombre_registrador",
    "url_detalle", "provincia_nombre", "codigo_ine_prov",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SIPI-ETL/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-ES,es;q=0.9",
}

SLUG_EXCEPCIONES: dict[str, str] = {
    "01": "araba-alava",
    "07": "illes-balears",
    "15": "a-coruna",
    "20": "gipuzkoa",
    "35": "las-palmas",
    "38": "santa-cruz-de-tenerife",
    "48": "bizkaia",
    "51": "ceuta",
    "52": "melilla",
}

# Ceuta y Melilla no tienen listado: van directamente a la ficha
URL_DIRECTAS: dict[str, str] = {
    "51": f"{BASE_URL}/ceuta/ceuta/registro-de-la-propiedad-de-ceuta-y-merc-y-bm",
    "52": f"{BASE_URL}/melilla/melilla/registro-de-la-propiedad-de-melilla-y-merc-y-bm",
}

PROVINCIAS: dict[str, str] = {
    "01": "Álava",               "02": "Albacete",
    "03": "Alicante",            "04": "Almería",
    "05": "Ávila",               "06": "Badajoz",
    "07": "Baleares",            "08": "Barcelona",
    "09": "Burgos",              "10": "Cáceres",
    "11": "Cádiz",               "12": "Castellón",
    "13": "Ciudad Real",         "14": "Córdoba",
    "15": "A Coruña",            "16": "Cuenca",
    "17": "Girona",              "18": "Granada",
    "19": "Guadalajara",         "20": "Gipuzkoa",
    "21": "Huelva",              "22": "Huesca",
    "23": "Jaén",                "24": "León",
    "25": "Lleida",              "26": "La Rioja",
    "27": "Lugo",                "28": "Madrid",
    "29": "Málaga",              "30": "Murcia",
    "31": "Navarra",             "32": "Ourense",
    "33": "Asturias",            "34": "Palencia",
    "35": "Las Palmas",          "36": "Pontevedra",
    "37": "Salamanca",           "38": "Santa Cruz de Tenerife",
    "39": "Cantabria",           "40": "Segovia",
    "41": "Sevilla",             "42": "Soria",
    "43": "Tarragona",           "44": "Teruel",
    "45": "Toledo",              "46": "Valencia",
    "47": "Valladolid",          "48": "Bizkaia",
    "49": "Zamora",              "50": "Zaragoza",
    "51": "Ceuta",               "52": "Melilla",
}


def to_slug(nombre: str) -> str:
    nfkd = unicodedata.normalize("NFKD", nombre)
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def slug_provincia(codigo: str) -> str:
    return SLUG_EXCEPCIONES.get(codigo) or to_slug(PROVINCIAS[codigo])


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parsear_detalle(soup: BeautifulSoup) -> dict:
    """Extrae campos de la ficha de detalle (div.datosDecanato + div.contactoDecanato)."""
    resultado = {
        "direccion_raw": "",
        "telefono": "",
        "email": "",
        "nombre_registrador": "",
    }

    # ── Dirección ────────────────────────────────────────────────────────────
    # La dirección aparece en div.subtit-decanato con texto "Dirección:<valor>"
    datos = soup.select_one("div.datosDecanato")
    if datos:
        for tag in datos.select("div.subtit-decanato"):
            texto = tag.get_text(strip=True)
            if re.match(r"[Dd]irecci[oó]n:", texto):
                resultado["direccion_raw"] = re.sub(r"^[Dd]irecci[oó]n:\s*", "", texto).strip()
                break

    # ── Contacto y registrador ────────────────────────────────────────────────
    contacto = soup.select_one("div.contactoDecanato")
    if not contacto:
        return resultado

    subtit_actual = ""
    for tag in contacto.children:
        if not hasattr(tag, "get"):
            continue
        clases = tag.get("class", [])

        if "subtit-decanato" in clases:
            subtit_actual = tag.get_text(strip=True).lower()

        elif "link-decanato" in clases:
            texto = tag.get_text(strip=True)
            if not texto:
                continue

            if "registrador" in subtit_actual:
                if not resultado["nombre_registrador"]:
                    resultado["nombre_registrador"] = texto

            elif "contacto" in subtit_actual or "tel" in subtit_actual:
                if "@" in texto and not resultado["email"]:
                    resultado["email"] = texto
                elif re.search(r"\d{6,}", texto.replace(" ", "")) and not resultado["telefono"]:
                    # Quitar prefijo "Teléfono" si viene pegado
                    tel = re.sub(r"^[Tt]el[eé]fono\s*", "", texto).strip()
                    resultado["telefono"] = tel

    return resultado


def parsear_listado_provincia(codigo: str) -> list[dict]:
    """Nivel 1: obtiene nombre + url_detalle desde la página de listado."""
    nombre_prov = PROVINCIAS[codigo]

    if codigo in URL_DIRECTAS:
        # Ceuta/Melilla: la ficha ES el listado
        url = URL_DIRECTAS[codigo]
        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"WARN [{codigo}] {e}", file=sys.stderr)
            return []
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1")
        nombre = h1.get_text(strip=True) if h1 else f"Registro de la Propiedad de {nombre_prov}"
        return [{"nombre": nombre, "url_detalle": url,
                 "provincia_nombre": nombre_prov, "codigo_ine_prov": codigo}]

    url = f"{BASE_URL}/{slug_provincia(codigo)}"
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"WARN [{codigo} {nombre_prov}] {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(html, "html.parser")
    ul = soup.select_one("ul.listado-registros")
    if not ul:
        print(f"WARN [{codigo} {nombre_prov}] sin ul.listado-registros en {url}", file=sys.stderr)
        return []

    items = []
    for li in ul.select("li"):
        a = li.find("a")
        if not a:
            continue
        items.append({
            "nombre":           a.get_text(strip=True),
            "url_detalle":      a.get("href", ""),
            "provincia_nombre": nombre_prov,
            "codigo_ine_prov":  codigo,
        })
    return items


def main(codigos: list[str], delay: float, forzar: bool):
    if FICHERO.exists() and not forzar:
        print(f"✓ Fichero ya existe: {FICHERO}  (usa --force para actualizar)")
        return

    DESTINO.mkdir(parents=True, exist_ok=True)
    total = 0

    with open(FICHERO, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()

        for i, codigo in enumerate(codigos):
            nombre_prov = PROVINCIAS[codigo]
            print(f"[{i+1:02d}/{len(codigos)}] {codigo} {nombre_prov}", end=" ", flush=True)

            # Nivel 1: listado de registros de la provincia
            items = parsear_listado_provincia(codigo)
            if not items:
                print("— sin datos")
                continue
            print(f"→ {len(items)} registros", end="  ", flush=True)
            time.sleep(delay)

            # Nivel 2: ficha de detalle de cada registro
            filas = []
            for j, item in enumerate(items):
                url_det = item["url_detalle"]
                try:
                    html_det = fetch_html(url_det)
                    soup_det = BeautifulSoup(html_det, "html.parser")
                    detalle  = parsear_detalle(soup_det)
                except Exception as e:
                    print(f"\n  WARN detalle {url_det}: {e}", file=sys.stderr)
                    detalle = {"direccion_raw": "", "telefono": "", "email": "", "nombre_registrador": ""}

                filas.append({**item, **detalle})

                if j < len(items) - 1:
                    time.sleep(delay)

            writer.writerows(filas)
            f.flush()
            total += len(filas)
            print(f"✓")

            if i < len(codigos) - 1:
                time.sleep(delay)

    print()
    print(f"✓ {total} registros guardados en {FICHERO}")
    print("Continúa con:")
    print("  python transform/registradores/transformar_registros_propiedad.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="E3: descarga catálogo completo de Registros de la Propiedad"
    )
    parser.add_argument("--provincia", metavar="COD",
                        help="Código INE (01-52). Sin este arg descarga todas.")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Segundos entre peticiones (default: 0.5)")
    parser.add_argument("--force", action="store_true",
                        help="Sobreescribe aunque ya exista el fichero")
    args = parser.parse_args()

    if args.provincia:
        cod = args.provincia.zfill(2)
        if cod not in PROVINCIAS:
            print(f"ERROR: código de provincia no válido: {cod}")
            sys.exit(1)
        codigos = [cod]
    else:
        codigos = sorted(PROVINCIAS.keys())

    main(codigos, args.delay, args.force)
