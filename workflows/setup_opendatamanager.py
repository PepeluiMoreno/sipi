#!/usr/bin/env python3
"""
workflows/setup_opendatamanager.py — Configura OpenDataManager con los recursos SIPI

Crea (o actualiza) en OpenDataManager los recursos de datos que alimentan el ETL:

    1. DIR3 — Directorio Común de Unidades Orgánicas y Oficinas
       Fuente: PAe / Ministerio de Hacienda (ZIP con CSV)

    2. Registros de la Propiedad — Directorio CORPME
       Fuente: registradores.org (buscador HTML paginado)

    3. Notarios — Directorio del Consejo General del Notariado (CGN)
       Fuente: notariado.org (buscador HTML paginado)

Requiere que OpenDataManager esté corriendo en ODM_URL.

Uso:
    python workflows/setup_opendatamanager.py
    python workflows/setup_opendatamanager.py --url http://172.22.0.3:8000
    python workflows/setup_opendatamanager.py --url http://localhost:8002
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# URL por defecto: IP del contenedor odmgr_app en la red Docker
ODM_URL_DEFAULT = "http://172.22.0.3:8000"

# ─── Definición de fetchers ────────────────────────────────────────────────────

FETCHERS = [
    {
        "code": "HTML Paginated",
        "class_path": "app.fetchers.paginated_html.PaginatedHtmlFetcher",
        "description": "Buscadores HTML con paginación automática (selectores CSS configurables)",
    },
    {
        "code": "API REST",
        "class_path": "app.fetchers.rest.RestFetcher",
        "description": "API RESTful con soporte para JSON",
    },
    {
        "code": "Paginated REST",
        "class_path": "app.fetchers.paginated_rest.PaginatedRestFetcher",
        "description": "APIs REST JSON paginadas por offset/página",
    },
]

# ─── Definición de recursos ───────────────────────────────────────────────────

RECURSOS = [
    {
        "name": "DIR3 — Unidades Orgánicas",
        "publisher": "PAe — Ministerio de Hacienda y Función Pública",
        "fetcher_code": "API REST",
        "description": (
            "Directorio Común de Unidades Orgánicas y Oficinas. "
            "ZIP con UnidadOrganica.csv (~50 MB). "
            "Descarga directa desde PAe."
        ),
        "params": [
            {
                "key": "url",
                "value": (
                    "https://administracionelectronica.gob.es/ctt/resources/"
                    "Soluciones/238/descargas/Dir3CatalogoEntidadesUnidades.zip"
                ),
            },
            {"key": "method", "value": "GET"},
            {"key": "timeout", "value": "120"},
            {
                "key": "headers",
                "value": json.dumps(
                    {"User-Agent": "Mozilla/5.0 (compatible; SIPI-ETL/1.0)"}
                ),
            },
        ],
    },
    {
        "name": "Registros de la Propiedad — CORPME",
        "publisher": "CORPME — Colegio de Registradores de España",
        "fetcher_code": "HTML Paginated",
        "description": (
            "Directorio completo de ~1.000 Registros de la Propiedad con "
            "nombre oficial, número, municipio sede, provincia y demarcación. "
            "Fuente: registradores.org"
        ),
        "params": [
            {
                "key": "url",
                "value": "https://www.registradores.org/buscadores/registro-propiedad/",
            },
            {"key": "method", "value": "GET"},
            {"key": "rows_selector", "value": "table tr, .registro-item"},
            {"key": "has_header", "value": "true"},
            {"key": "pagination_type", "value": "link"},
            {"key": "page_size", "value": "20"},
            {"key": "max_pages", "value": "100"},
            {"key": "delay_between_pages", "value": "1.5"},
            {"key": "clean_html", "value": "true"},
            {
                "key": "headers",
                "value": json.dumps(
                    {"User-Agent": "Mozilla/5.0 (compatible; SIPI-ETL/1.0)"}
                ),
            },
        ],
    },
    {
        "name": "Notarios — Consejo General del Notariado",
        "publisher": "CGN — Consejo General del Notariado de España",
        "fetcher_code": "HTML Paginated",
        "description": (
            "Directorio de notarios de España con nombre, número de protocolo, "
            "localidad, provincia y demarcación. "
            "Fuente: notariado.org"
        ),
        "params": [
            {
                "key": "url",
                "value": "https://www.notariado.org/portal/notario/inicio/lista-de-notarios",
            },
            {"key": "method", "value": "GET"},
            {"key": "rows_selector", "value": "table tr, .notario-item"},
            {"key": "has_header", "value": "true"},
            {"key": "pagination_type", "value": "link"},
            {"key": "page_size", "value": "20"},
            {"key": "max_pages", "value": "200"},
            {"key": "delay_between_pages", "value": "1.5"},
            {"key": "clean_html", "value": "true"},
            {
                "key": "headers",
                "value": json.dumps(
                    {"User-Agent": "Mozilla/5.0 (compatible; SIPI-ETL/1.0)"}
                ),
            },
        ],
    },
]

# ─── Helpers GraphQL ──────────────────────────────────────────────────────────

def gql(url: str, query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        f"{url}/graphql",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_fetchers(url: str) -> dict[str, str]:
    """Devuelve dict code → id de los fetchers existentes."""
    resp = gql(url, "{ fetchers { id code } }")
    return {f["code"]: f["id"] for f in resp["data"]["fetchers"]}


def get_resources(url: str) -> dict[str, str]:
    """Devuelve dict name → id de los recursos existentes."""
    resp = gql(url, "{ resources { id name } }")
    return {r["name"]: r["id"] for r in resp["data"]["resources"]}


CREATE_FETCHER_GQL = """
mutation CreateFetcher($input: CreateFetcherInput!) {
  createFetcher(input: $input) { id code }
}
"""

CREATE_RESOURCE_GQL = """
mutation CreateResource($input: CreateResourceInput!) {
  createResource(input: $input) { id name }
}
"""

UPDATE_RESOURCE_GQL = """
mutation UpdateResource($id: String!, $input: UpdateResourceInput!) {
  updateResource(id: $id, input: $input) { id name }
}
"""

# ─── Setup ────────────────────────────────────────────────────────────────────

def setup(odm_url: str):
    print(f"OpenDataManager: {odm_url}")
    print()

    # 1. Fetchers
    print("── Fetchers ────────────────────────────────────────────────────────")
    existentes = get_fetchers(odm_url)
    fetcher_ids: dict[str, str] = {}

    for f in FETCHERS:
        code = f["code"]
        if code in existentes:
            fid = existentes[code]
            print(f"  [OK] {code} (id={fid[:8]}…)")
        else:
            resp = gql(odm_url, CREATE_FETCHER_GQL, {
                "input": {
                    "name": code,
                    "classPath": f["class_path"],
                    "description": f["description"],
                }
            })
            if "errors" in resp:
                print(f"  [ERR] {code}: {resp['errors'][0]['message']}")
                sys.exit(1)
            fid = resp["data"]["createFetcher"]["id"]
            print(f"  [+] {code} creado (id={fid[:8]}…)")
        fetcher_ids[code] = fid

    # 2. Recursos
    print()
    print("── Recursos ────────────────────────────────────────────────────────")
    recursos_existentes = get_resources(odm_url)

    for r in RECURSOS:
        name = r["name"]
        fetcher_code = r["fetcher_code"]
        fetcher_id = fetcher_ids.get(fetcher_code)
        if not fetcher_id:
            print(f"  [ERR] Fetcher '{fetcher_code}' no encontrado para recurso '{name}'")
            continue

        params_input = [{"key": p["key"], "value": p["value"]} for p in r["params"]]

        if name in recursos_existentes:
            rid = recursos_existentes[name]
            print(f"  [OK] {name} (id={rid[:8]}…) — ya existe, sin cambios")
        else:
            resp = gql(odm_url, CREATE_RESOURCE_GQL, {
                "input": {
                    "name": name,
                    "publisher": r["publisher"],
                    "fetcherId": fetcher_id,
                    "active": True,
                    "params": params_input,
                }
            })
            if "errors" in resp:
                print(f"  [ERR] {name}: {resp['errors'][0]['message']}")
            else:
                rid = resp["data"]["createResource"]["id"]
                print(f"  [+] {name} creado (id={rid[:8]}…)")

    print()
    print("✓ Setup completado")
    print()
    print("Nota: Los parámetros de URL y selectores deben ajustarse en el UI de")
    print("      OpenDataManager una vez verificados contra las webs reales.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configura recursos SIPI en OpenDataManager")
    parser.add_argument(
        "--url", default=ODM_URL_DEFAULT,
        help=f"URL base de OpenDataManager (default: {ODM_URL_DEFAULT})"
    )
    args = parser.parse_args()

    try:
        setup(args.url)
    except urllib.error.URLError as e:
        print(f"ERROR: No se puede conectar a OpenDataManager en {args.url}")
        print(f"       {e}")
        print()
        print("Asegúrate de que OpenDataManager está corriendo:")
        print("  cd /opt/docker/apps/opendatamanager && docker compose up -d")
        sys.exit(1)
