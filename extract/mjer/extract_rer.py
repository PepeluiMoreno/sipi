#!/usr/bin/env python3
"""
extract/mjer/extract_rer.py — Registro de Entidades Religiosas (Ministerio de Justicia)

Por defecto extrae SOLO entidades católicas (filtro.confesion=CAT, filtro.seccion=3/ESPECIAL).
Esto incluye órdenes, congregaciones e institutos de vida consagrada de la Iglesia Católica.

Dos fases:
  1. Enumerar: paginar buscarRER.action con filtros → lista de numeroInscripcion
  2. Detallar: GET DetalleEntidadReligiosa.action?numeroInscripcion=N para cada entidad
               Extrae TODOS los campos disponibles (esquema dinámico), incluido Tipo de entidad

Valores de filtro (obtenidos del formulario MJER):
  filtro.confesion: CAT=CATÓLICOS, CONF_EV=EVANGÉLICOS, CONF_MU=MUSULMANES, ...
  filtro.seccion:   1=TODAS, 2=GENERAL, 3=ESPECIAL (católicas)

Salida:
  data/output/mjer/rer_numeros.txt     — lista de números (fase 1, reanudable)
  data/output/mjer/rer_entidades.jsonl — una entidad por línea (fase 2, reanudable)

Uso:
    python extract/mjer/extract_rer.py              # solo católicas (por defecto)
    python extract/mjer/extract_rer.py --todas      # todas las confesiones
    python extract/mjer/extract_rer.py --fase 1     # solo enumerar
    python extract/mjer/extract_rer.py --fase 2     # solo detallar (requiere fase 1)
    python extract/mjer/extract_rer.py --workers 10 # concurrencia en fase 2
"""

import argparse
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE       = "https://maper.mjusticia.gob.es/Maper"
FORM_URL   = f"{BASE}/RER.action"
BUSCAR_URL = f"{BASE}/buscarRER.action"
DETALLE_URL = f"{BASE}/DetalleEntidadReligiosa.action"

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0",
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

DELAY   = 0.5   # segundos entre páginas en fase 1
TIMEOUT = 30

OUT_DIR       = Path(__file__).parent.parent.parent / "data" / "output" / "mjer"
FILE_NUMEROS  = OUT_DIR / "rer_numeros.txt"
FILE_ENTIDADES = OUT_DIR / "rer_entidades.jsonl"


# ── Fase 1: enumerar ──────────────────────────────────────────────────────────

def new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get(FORM_URL, timeout=TIMEOUT)   # establece JSESSIONID
    return s


def parse_numeros(soup: BeautifulSoup) -> list[str]:
    """Extrae los numeroInscripcion de los links de la tabla de resultados."""
    numeros = []
    vistos = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "numeroInscripcion=" in href:
            n = href.split("numeroInscripcion=")[-1].strip()
            if n and n not in vistos:
                numeros.append(n)
                vistos.add(n)
    return numeros


def max_page(soup: BeautifulSoup) -> int:
    """Devuelve el número máximo de página visible en los links de paginación."""
    paginas = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "avanzarRetrocederRER.action" in href and "page=" in href:
            try:
                paginas.append(int(href.split("page=")[-1]))
            except ValueError:
                pass
    return max(paginas) if paginas else 0


def fase1_enumerar(solo_catolicas: bool = True) -> list[str]:
    """Pagina buscarRER.action y devuelve todos los números de inscripción.
    Con solo_catolicas=True (por defecto) filtra confesion=CAT y seccion=1 (TODAS las secciones).
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar los ya recolectados
    recolectados: list[str] = []
    if FILE_NUMEROS.exists():
        recolectados = [l.strip() for l in FILE_NUMEROS.read_text().splitlines() if l.strip()]
        log.info(f"Fase 1: {len(recolectados)} números ya recolectados, reanudando…")

    vistos = set(recolectados)
    session = new_session()

    # Filtros de búsqueda:
    # filtro.confesion = CAT  → solo CATÓLICOS
    # filtro.seccion   = 1    → TODAS las secciones (General + Especial)
    buscar_data = {
        "filtro.nombre": "", "filtro.numeroInscripcion": "",
        "filtro.numeroInscripcionAntiguo": "",
        "__multiselect_filtro.confesion": "",
        "__multiselect_filtro.subconfesion": "",
        "__multiselect_filtro.tiposEntidad": "",
        "__multiselect_filtro.codigosComunidad": "",
        "__multiselect_filtro.codigosProvincia": "",
        "filtro.municipio": "",
        "filtro.seccion": "1",   # TODAS las secciones
    }
    if solo_catolicas:
        buscar_data["filtro.confesion"] = "CAT"
        log.info("Fase 1: filtro confesión=CAT (CATÓLICOS), sección=TODAS")
    else:
        log.info("Fase 1: sin filtro de confesión (todas las confesiones)")

    r0 = session.post(BUSCAR_URL, data=buscar_data, timeout=TIMEOUT)
    soup0 = BeautifulSoup(r0.text, "html.parser")

    # Determinar el rango de páginas desde la paginación visible
    pagina_max_conocida = max_page(soup0)
    log.info(f"  Páginas visibles en pág 1: hasta {pagina_max_conocida}")

    AVANZAR_URL = f"{BASE}/avanzarRetrocederRER.action"
    pagina = 1
    sin_nuevos_consecutivos = 0

    with open(FILE_NUMEROS, "a", encoding="utf-8") as f:
        while True:
            if pagina == 1:
                soup = soup0
            else:
                r = session.get(AVANZAR_URL, params={"page": pagina}, timeout=TIMEOUT)
                if r.status_code != 200:
                    log.warning(f"  HTTP {r.status_code} en pág {pagina}, fin.")
                    break
                soup = BeautifulSoup(r.text, "html.parser")

            numeros = parse_numeros(soup)

            if not numeros:
                log.info(f"  pág {pagina}: sin resultados, fin.")
                break

            nuevos = [n for n in numeros if n not in vistos]
            for n in nuevos:
                f.write(n + "\n")
                vistos.add(n)
                recolectados.append(n)
            if nuevos:
                f.flush()

            # Actualizar el máximo de páginas conocido
            pagina_max_conocida = max(pagina_max_conocida, max_page(soup))
            log.info(f"  pág {pagina}/{pagina_max_conocida}: {len(numeros)} | {len(nuevos)} nuevos | total {len(recolectados)}")

            if not nuevos:
                sin_nuevos_consecutivos += 1
                if sin_nuevos_consecutivos >= 3:
                    log.info("  3 páginas consecutivas sin nuevos, fin.")
                    break
            else:
                sin_nuevos_consecutivos = 0

            if pagina >= pagina_max_conocida and pagina_max_conocida > 0:
                # Avanzar una más para ver si hay más páginas
                pagina += 1
                time.sleep(DELAY)
                r = session.get(AVANZAR_URL, params={"page": pagina}, timeout=TIMEOUT)
                if r.status_code != 200:
                    break
                soup_next = BeautifulSoup(r.text, "html.parser")
                new_max = max_page(soup_next)
                if new_max > pagina_max_conocida:
                    pagina_max_conocida = new_max
                    soup = soup_next
                    numeros = parse_numeros(soup)
                    nuevos = [n for n in numeros if n not in vistos]
                    for n in nuevos:
                        f.write(n + "\n")
                        vistos.add(n)
                        recolectados.append(n)
                    log.info(f"  pág {pagina}/{pagina_max_conocida}: {len(numeros)} | {len(nuevos)} nuevos | total {len(recolectados)}")
                    if not nuevos:
                        break
                else:
                    break

            pagina += 1
            time.sleep(DELAY)

    log.info(f"Fase 1 completada: {len(recolectados)} números totales")
    return recolectados


# ── Fase 2: detallar ──────────────────────────────────────────────────────────

def parse_detalle(html: str, numero: str) -> dict:
    """
    Extrae TODOS los campos del detalle de una entidad.
    Dos formatos posibles:
      A) <p><strong>Etiqueta</strong>: valor</p>  (más común)
      B) <tr><td>Etiqueta</td><td>valor</td></tr>
    Extrae ambos sin filtrar: esquema completamente dinámico.
    """
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"numero_inscripcion": numero}

    # Formato A: <p><strong>…</strong>
    for p in soup.find_all("p"):
        strong = p.find("strong")
        if not strong:
            continue
        label = strong.get_text(strip=True).rstrip(":")
        strong.extract()
        value = p.get_text(" ", strip=True).lstrip(":").strip()
        if label and value:
            data[label] = value

    # Formato B: tabla con 2 celdas (si no se extrajo nada con A)
    if len(data) <= 1:
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                label = tds[0].get_text(strip=True).rstrip(":")
                value = tds[1].get_text(strip=True)
                if label and value:
                    data[label] = value

    return data


def fetch_detalle(numero: str) -> dict | None:
    try:
        r = requests.get(
            DETALLE_URL,
            params={"numeroInscripcion": numero},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return parse_detalle(r.text, numero)
    except Exception as e:
        log.warning(f"  Error detalle {numero}: {e}")
        return None


def fase2_detallar(numeros: list[str], workers: int):
    """Fetch concurrente de detalles, escribe JSONL reanudable."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    procesados: set[str] = set()
    if FILE_ENTIDADES.exists():
        for line in FILE_ENTIDADES.read_text(encoding="utf-8").splitlines():
            try:
                obj = json.loads(line)
                if obj.get("numero_inscripcion"):
                    procesados.add(obj["numero_inscripcion"])
            except json.JSONDecodeError:
                pass
        log.info(f"Fase 2: {len(procesados)} detalles ya extraídos, reanudando…")

    pendientes = [n for n in numeros if n not in procesados]
    log.info(f"Fase 2: {len(pendientes)} detalles pendientes ({workers} workers)")

    total = len(procesados)
    with open(FILE_ENTIDADES, "a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futuros = {ex.submit(fetch_detalle, n): n for n in pendientes}
            for futuro in as_completed(futuros):
                numero = futuros[futuro]
                resultado = futuro.result()
                if resultado:
                    f.write(json.dumps(resultado, ensure_ascii=False) + "\n")
                    f.flush()
                    total += 1
                    if total % 500 == 0:
                        log.info(f"  … {total} detalles extraídos")

    log.info(f"Fase 2 completada: {total} entidades en {FILE_ENTIDADES}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main(fase: int | None, workers: int, todas: bool):
    solo_catolicas = not todas
    if fase in (None, 1):
        numeros = fase1_enumerar(solo_catolicas=solo_catolicas)
    else:
        if not FILE_NUMEROS.exists():
            log.error(f"Ejecuta primero la fase 1 (falta {FILE_NUMEROS})")
            return
        numeros = [l.strip() for l in FILE_NUMEROS.read_text().splitlines() if l.strip()]
        log.info(f"Fase 1 omitida: {len(numeros)} números cargados de {FILE_NUMEROS.name}")

    if fase in (None, 2):
        fase2_detallar(numeros, workers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrae entidades religiosas del RER (MJusticia)")
    parser.add_argument("--fase", type=int, choices=[1, 2], default=None,
                        help="1=solo enumerar, 2=solo detallar, omitir=ambas")
    parser.add_argument("--workers", type=int, default=5,
                        help="Concurrencia para fetch de detalles (default: 5)")
    parser.add_argument("--todas", action="store_true",
                        help="Extrae todas las confesiones (por defecto solo CATÓLICOS)")
    args = parser.parse_args()
    main(args.fase, args.workers, args.todas)
