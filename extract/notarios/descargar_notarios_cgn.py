#!/usr/bin/env python3
"""
extract/notarios/descargar_notarios_cgn.py
— E5b: Scraping directo del buscador de Notarías del Consejo General del Notariado

Fuente: Consejo General del Notariado (CGN)
URL:    https://www.notariado.org/portal/Elige%20a%20tu%20notario%20orden

Estrategia:
    El formulario de búsqueda (form id=pbwg_form-eligetunotario) carga TODOS los
    resultados en el DOM (hasta ~835 por consulta) y los filtra en cliente con JS.
    Se itera por provincia capital para maximizar cobertura, deduplicando por nombre+municipio.

    Parámetros del formulario (POST via jQuery):
        Nombre      — nombre del notario (texto libre)
        Apellidos   — apellidos del notario (texto libre)
        CodigoPostal— código postal (5 dígitos)
        Poblacion   — municipio (texto libre, búsqueda parcial)
        Idioma      — idioma de trabajo (Alemán, Catalán, Euskera, …)

    La respuesta incluye los ítems de resultado con clase numérica (.1, .2, …).
    Se parsea con BeautifulSoup; si el HTML no contiene resultados renderizados
    (JS-only), usar --playwright para renderizado con Playwright.

Salida: data/input/notarios/notarios_cgn_raw.csv

Campos de salida:
    nombre_notario, municipio, provincia, direccion_raw,
    codigo_postal, telefono, email, numero_protocolo, url_notaria

Uso:
    python extract/notarios/descargar_notarios_cgn.py
    python extract/notarios/descargar_notarios_cgn.py --dry-run
    python extract/notarios/descargar_notarios_cgn.py --provincia Madrid
    python extract/notarios/descargar_notarios_cgn.py --delay 1.0
    python extract/notarios/descargar_notarios_cgn.py --playwright   # requiere: pip install playwright && playwright install chromium
"""

import argparse
import csv
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: pip install beautifulsoup4")
    sys.exit(1)

# ── Constantes ───────────────────────────────────────────────────────────────

FORM_URL = "https://www.notariado.org/portal/Elige%20a%20tu%20notario%20orden"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SIPI-ETL/1.0)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "text/html,application/xhtml+xml",
    "Referer": FORM_URL,
}

DESTINO = Path(__file__).parent.parent.parent / "data" / "input" / "notarios"
CSV_PATH = DESTINO / "notarios_cgn_raw.csv"

CAMPOS = [
    "nombre_notario", "municipio", "provincia", "direccion_raw",
    "codigo_postal", "telefono", "email", "numero_protocolo", "url_notaria",
]

# Capitales de provincia + ciudades autónomas para iterar.
# Producen cobertura suficiente para un MVP; ampliar con municipios más pequeños
# en una segunda pasada si se detectan huecos.
CAPITALES_PROVINCIA: list[tuple[str, str]] = [
    ("Álava",              "Vitoria-Gasteiz"),
    ("Albacete",           "Albacete"),
    ("Alicante",           "Alicante"),
    ("Almería",            "Almería"),
    ("Asturias",           "Oviedo"),
    ("Ávila",              "Ávila"),
    ("Badajoz",            "Badajoz"),
    ("Illes Balears",      "Palma"),
    ("Barcelona",          "Barcelona"),
    ("Burgos",             "Burgos"),
    ("Cáceres",            "Cáceres"),
    ("Cádiz",              "Cádiz"),
    ("Cantabria",          "Santander"),
    ("Castellón",          "Castellón de la Plana"),
    ("Ciudad Real",        "Ciudad Real"),
    ("Córdoba",            "Córdoba"),
    ("A Coruña",           "A Coruña"),
    ("Cuenca",             "Cuenca"),
    ("Girona",             "Girona"),
    ("Granada",            "Granada"),
    ("Guadalajara",        "Guadalajara"),
    ("Gipuzkoa",           "San Sebastián"),
    ("Huelva",             "Huelva"),
    ("Huesca",             "Huesca"),
    ("Jaén",               "Jaén"),
    ("León",               "León"),
    ("Lleida",             "Lleida"),
    ("Lugo",               "Lugo"),
    ("Madrid",             "Madrid"),
    ("Málaga",             "Málaga"),
    ("Murcia",             "Murcia"),
    ("Navarra",            "Pamplona"),
    ("Ourense",            "Ourense"),
    ("Palencia",           "Palencia"),
    ("Las Palmas",         "Las Palmas de Gran Canaria"),
    ("Pontevedra",         "Pontevedra"),
    ("La Rioja",           "Logroño"),
    ("Salamanca",          "Salamanca"),
    ("Segovia",            "Segovia"),
    ("Sevilla",            "Sevilla"),
    ("Soria",              "Soria"),
    ("Tarragona",          "Tarragona"),
    ("S.C. de Tenerife",   "Santa Cruz de Tenerife"),
    ("Teruel",             "Teruel"),
    ("Toledo",             "Toledo"),
    ("Valencia",           "Valencia"),
    ("Valladolid",         "Valladolid"),
    ("Bizkaia",            "Bilbao"),
    ("Zamora",             "Zamora"),
    ("Zaragoza",           "Zaragoza"),
    ("Ceuta",              "Ceuta"),
    ("Melilla",            "Melilla"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _texto(el) -> str:
    """Texto limpio de un elemento BeautifulSoup."""
    return el.get_text(" ", strip=True) if el else ""


def _post_form(poblacion: str, timeout: int = 30) -> bytes | None:
    """Envía el formulario de búsqueda y devuelve el HTML crudo."""
    data = urllib.parse.urlencode({
        "Poblacion": poblacion,
        "Nombre":    "",
        "Apellidos": "",
        "CodigoPostal": "",
        "Idioma":    "",
    }).encode()
    req = urllib.request.Request(FORM_URL, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  WARN request error para '{poblacion}': {e}", file=sys.stderr)
        return None


def _post_form_playwright(poblacion: str) -> bytes | None:
    """Renderiza la búsqueda con Playwright (necesario si JS es imprescindible)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: pip install playwright && playwright install chromium")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FORM_URL)
        page.fill("input[name='Poblacion']", poblacion)
        page.click("button[type='submit'], input[type='submit']")
        page.wait_for_load_state("networkidle")
        html = page.content().encode()
        browser.close()
        return html


def parsear_resultados(html: bytes, provincia: str) -> list[dict]:
    """
    Extrae notarías del HTML de respuesta.

    El portal carga todos los ítems en el DOM con clase numérica (.1, .2, …).
    Cada ítem contiene: nombre notario, municipio, dirección, teléfono, email.
    """
    soup = BeautifulSoup(html, "html.parser")
    resultados: list[dict] = []

    # ── Intento 1: ítems con clase numérica (estructura conocida del portal) ──
    # Buscar contenedor de resultados; puede ser div, ul, ol con id o clase
    contenedor = (
        soup.find(id="zzoz_resultsContainer")
        or soup.find(class_=re.compile(r"results?[-_]?container", re.I))
        or soup.find(id=re.compile(r"result", re.I))
    )

    items = []
    if contenedor:
        # Ítems directos del contenedor
        items = contenedor.find_all(["div", "li", "article"], recursive=False)
        if not items:
            items = contenedor.find_all(["div", "li", "article"])

    # ── Intento 2: ítems con clase numérica en todo el documento ─────────────
    if not items:
        items = [
            el for el in soup.find_all(True)
            if el.get("class") and any(c.isdigit() for c in el["class"])
               and len(_texto(el)) > 20
        ]

    # ── Intento 3: buscar por patrones de texto comunes en el DOM ─────────────
    if not items:
        # Buscar divs/li que contengan "Notaría" o "Notario" en su texto
        items = [
            el for el in soup.find_all(["div", "li", "article"])
            if re.search(r"notar[íi]", _texto(el), re.I)
               and 30 < len(_texto(el)) < 500
        ]

    for item in items:
        texto_item = _texto(item)
        if not texto_item or len(texto_item) < 10:
            continue

        # Nombre del notario: primera línea en negrita o primer texto grande
        nombre_el = item.find(["strong", "b", "h2", "h3", "h4"])
        nombre_notario = _texto(nombre_el) if nombre_el else ""

        # Municipio y CP: buscar patrón "XXXXX Municipio"
        m_cp = re.search(r"\b(\d{5})\s+([\w\s\-áéíóúüñÁÉÍÓÚÜÑ]+)", texto_item)
        codigo_postal = m_cp.group(1) if m_cp else ""
        municipio_scraped = m_cp.group(2).strip() if m_cp else ""

        # Teléfono
        m_tel = re.search(r"\b(9\d{8}|6\d{8}|\+34[\s\-]?\d{9})\b", texto_item)
        telefono = m_tel.group(0).strip() if m_tel else ""

        # Email
        m_email = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", texto_item)
        email = m_email.group(0) if m_email else ""

        # Número de protocolo/plaza
        m_proto = re.search(r"[Nn]º\s*(\d+)|[Pp]rotocolo\s*(\d+)|[Pp]laza\s*(\d+)", texto_item)
        numero_protocolo = next((g for g in (m_proto.groups() if m_proto else []) if g), "")

        # URL de la notaría (enlace dentro del ítem)
        enlace = item.find("a", href=True)
        url_notaria = enlace["href"] if enlace else ""
        if url_notaria and not url_notaria.startswith("http"):
            url_notaria = "https://www.notariado.org" + url_notaria

        # Dirección: texto restante tras quitar nombre, tel, email, CP
        direccion_raw = re.sub(
            r"[\w.\-+]+@[\w.\-]+\.\w+|"
            r"\b(9\d{8}|6\d{8}|\+34[\s\-]?\d{9})\b|"
            r"\b\d{5}\b",
            "", texto_item
        ).strip()
        if nombre_notario:
            direccion_raw = direccion_raw.replace(nombre_notario, "").strip()
        direccion_raw = re.sub(r"\s{2,}", " ", direccion_raw).strip(" ,;-|")

        if not nombre_notario and not municipio_scraped:
            continue  # ítem vacío o irrelevante

        resultados.append({
            "nombre_notario":  nombre_notario,
            "municipio":       municipio_scraped or provincia,
            "provincia":       provincia,
            "direccion_raw":   direccion_raw[:200],
            "codigo_postal":   codigo_postal,
            "telefono":        telefono,
            "email":           email,
            "numero_protocolo": numero_protocolo,
            "url_notaria":     url_notaria,
        })

    return resultados


# ── Main ──────────────────────────────────────────────────────────────────────

def main(
    dry_run: bool = False,
    solo_provincia: str | None = None,
    delay: float = 0.5,
    usar_playwright: bool = False,
):
    provincias = CAPITALES_PROVINCIA
    if solo_provincia:
        provincias = [(p, c) for p, c in provincias if p.lower() == solo_provincia.lower()
                      or c.lower() == solo_provincia.lower()]
        if not provincias:
            print(f"ERROR: Provincia/capital '{solo_provincia}' no encontrada en la lista")
            sys.exit(1)

    vistos: set[str] = set()
    todos: list[dict] = []

    for provincia, capital in provincias:
        print(f"  [{provincia}] {capital}…", end=" ", flush=True)

        if usar_playwright:
            html = _post_form_playwright(capital)
        else:
            html = _post_form(capital)

        if html is None:
            print("ERROR")
            continue

        filas = parsear_resultados(html, provincia)

        nuevos = 0
        for f in filas:
            key = f"{f['nombre_notario']}|{f['municipio']}"
            if key not in vistos:
                vistos.add(key)
                todos.append(f)
                nuevos += 1

        print(f"{nuevos} nuevas ({len(todos)} total)")

        if not dry_run and time.sleep(delay) is None:
            pass  # sleep ya ejecutado como efecto secundario

    if dry_run:
        print(f"\n[DRY-RUN] {len(todos)} notarías encontradas (no guardadas)")
        for f in todos[:5]:
            print(f"  {f['nombre_notario']} | {f['municipio']} | {f['telefono']}")
        return

    DESTINO.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(todos)

    print(f"\n✓ {len(todos)} notarías → {CSV_PATH}")
    print("Continúa con:")
    print("  python transform/notarios/transformar_notarios.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="E5b: scraping directo del directorio de notarías (CGN)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="No guarda CSV, solo muestra estadísticas")
    parser.add_argument("--provincia", metavar="NOMBRE",
                        help="Procesa solo esta provincia/capital (ej. 'Madrid')")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Pausa entre peticiones en segundos (default: 0.5)")
    parser.add_argument("--playwright", action="store_true",
                        help="Usa Playwright para renderizado JS (requiere: playwright install chromium)")
    args = parser.parse_args()

    print("Descargando directorio de Notarías (CGN)…")
    main(
        dry_run=args.dry_run,
        solo_provincia=args.provincia,
        delay=args.delay,
        usar_playwright=args.playwright,
    )
    print("✓ Completado")
