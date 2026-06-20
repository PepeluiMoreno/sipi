#!/usr/bin/env python3
"""
extract/notarios/descargar_notarios.py
— E5: Descarga el directorio de Notarios vía OpenDataManager

Fuente oficial:
    Consejo General del Notariado (CGN) de España
    https://www.notariado.org

OpenDataManager gestiona la extracción automática desde la web del CGN
y entrega los datos normalizados. Este script llama a su API para:
    1. Obtener el recurso "Notarios — Consejo General del Notariado"
    2. Ejecutar la extracción si no hay dataset reciente
    3. Descargar el dataset en formato JSONL
    4. Convertir a CSV con los campos esperados por T5

Fichero de salida:
    data/input/notarios/notarios_raw.csv

Campos esperados en el CSV de salida:
    nombre          — nombre completo del notario
    numero          — número de protocolo / plaza
    municipio       — localidad de la notaría
    codigo_ine_mun  — código INE del municipio (5 dígitos)
    provincia       — nombre de la provincia
    codigo_ine_prov — código INE de la provincia (2 dígitos)
    demarcacion     — demarcación notarial

Uso:
    python extract/notarios/descargar_notarios.py
    python extract/notarios/descargar_notarios.py --output data/input/notarios/
    python extract/notarios/descargar_notarios.py --odm-url http://172.22.0.3:8000
    python extract/notarios/descargar_notarios.py --force
"""

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DESTINO_DEFAULT = Path(__file__).parent.parent.parent / "data" / "input" / "notarios"
FICHERO_DEFAULT = DESTINO_DEFAULT / "notarios_raw.csv"

ODM_URL_DEFAULT = "http://172.22.0.3:8000"
RESOURCE_NAME   = "Notarios — Consejo General del Notariado"

TIMEOUT_EJECUCION = 600  # hasta 10 min; el CGN tiene miles de notarios


def gql(odm_url: str, query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        f"{odm_url}/graphql",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


EXECUTE_RESOURCE_GQL = """
mutation ExecuteResource($id: String!) {
  executeResource(id: $id) {
    success
    message
  }
}
"""

GET_EXECUTIONS_GQL = """
query GetExecutions($resourceId: String!) {
  resourceExecutions(resourceId: $resourceId) {
    id
    status
    startedAt
    finishedAt
    errorMessage
  }
}
"""


def ejecutar_y_esperar(odm_url: str, resource_id: str) -> bool:
    print("  Ejecutando recurso en OpenDataManager…")
    resp = gql(odm_url, EXECUTE_RESOURCE_GQL, {"id": resource_id})
    result = resp["data"]["executeResource"]
    if not result["success"]:
        print(f"  ERROR: {result['message']}")
        return False

    inicio = time.time()
    while time.time() - inicio < TIMEOUT_EJECUCION:
        time.sleep(5)
        exec_resp = gql(odm_url, GET_EXECUTIONS_GQL, {"resourceId": resource_id})
        execuciones = exec_resp["data"].get("resourceExecutions", [])
        if execuciones:
            ultima = execuciones[-1]
            estado = ultima.get("status", "")
            if estado == "completed":
                return True
            elif estado in ("failed", "error"):
                print(f"  Ejecución fallida: {ultima.get('errorMessage', '')}")
                return False
            else:
                print(f"  Estado: {estado}…")
    print(f"  ERROR: timeout ({TIMEOUT_EJECUCION}s)")
    return False


def descargar_dataset(odm_url: str, dataset_id: str, destino: Path) -> int:
    url = f"{odm_url}/api/datasets/{dataset_id}/data.jsonl"
    print("  Descargando dataset desde ODM…")

    req = urllib.request.Request(url, headers={"Accept": "application/x-ndjson"})
    registros: list[dict] = []
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            line = line.strip()
            if line:
                registros.append(json.loads(line))

    print(f"  {len(registros)} registros recibidos")

    destino.parent.mkdir(parents=True, exist_ok=True)
    campos = ["nombre", "numero", "municipio", "codigo_ine_mun",
              "provincia", "codigo_ine_prov", "demarcacion"]

    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for reg in registros:
            fila = {
                "nombre":          reg.get("nombre", reg.get("Nombre", "")),
                "numero":          reg.get("numero", reg.get("Número", reg.get("NumeroProtocolo", ""))),
                "municipio":       reg.get("municipio", reg.get("Municipio", reg.get("Localidad", ""))),
                "codigo_ine_mun":  reg.get("codigo_ine_mun", reg.get("CodigoINEMunicipio", "")),
                "provincia":       reg.get("provincia", reg.get("Provincia", "")),
                "codigo_ine_prov": reg.get("codigo_ine_prov", reg.get("CodigoINEProvincia", "")),
                "demarcacion":     reg.get("demarcacion", reg.get("Demarcacion", "")),
            }
            w.writerow(fila)

    return len(registros)


def main(odm_url: str, destino_fichero: Path, force: bool):
    print("Descarga de Notarios — CGN vía OpenDataManager")
    print()

    if destino_fichero.exists() and not force:
        print(f"✓ Fichero ya disponible: {destino_fichero}")
        print(f"  ({destino_fichero.stat().st_size:,} bytes)")
        print()
        print("Para actualizar usa --force.")
        return

    try:
        resp = gql(odm_url, "{ resources { id name datasets { id version createdAt } } }")
    except urllib.error.URLError as e:
        print(f"ERROR: No se puede conectar a OpenDataManager en {odm_url}")
        print(f"       {e}")
        sys.exit(1)

    recurso = None
    for r in resp["data"]["resources"]:
        if r["name"] == RESOURCE_NAME:
            recurso = r
            break

    if recurso is None:
        print(f"ERROR: Recurso '{RESOURCE_NAME}' no encontrado en OpenDataManager.")
        print("Ejecuta: python workflows/setup_opendatamanager.py")
        sys.exit(1)

    resource_id = recurso["id"]
    print(f"  Recurso: {RESOURCE_NAME} (id={resource_id[:8]}…)")

    datasets = recurso.get("datasets") or []
    if datasets and not force:
        dataset = sorted(datasets, key=lambda d: d.get("createdAt", ""), reverse=True)[0]
        print(f"  Dataset existente: v{dataset.get('version', '?')} ({dataset.get('createdAt', '')[:10]})")
    else:
        print("  Sin dataset. Iniciando extracción en ODM…")
        ok = ejecutar_y_esperar(odm_url, resource_id)
        if not ok:
            print()
            print("La extracción automática falló. Configura los parámetros del")
            print(f"recurso '{RESOURCE_NAME}' en el UI de OpenDataManager:")
            print(f"  http://optiplex-790:5173")
            sys.exit(1)
        resp2 = gql(odm_url, "{ resources { id name datasets { id version createdAt } } }")
        for r in resp2["data"]["resources"]:
            if r["name"] == RESOURCE_NAME:
                datasets = r.get("datasets") or []
                break
        if not datasets:
            print("ERROR: No se generó ningún dataset.")
            sys.exit(1)
        dataset = sorted(datasets, key=lambda d: d.get("createdAt", ""), reverse=True)[0]

    n = descargar_dataset(odm_url, dataset["id"], destino_fichero)
    print(f"  → Guardado en: {destino_fichero}")
    print(f"  → {n:,} registros")
    print()
    print("✓ Descarga completada")
    print("Continúa con:")
    print("  python transform/notarios/transformar_notarios.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="E5: descarga directorio de Notarios (CGN) vía OpenDataManager"
    )
    parser.add_argument("--output", type=Path,
                        help="Directorio de salida (default: data/input/notarios/)")
    parser.add_argument("--odm-url", default=ODM_URL_DEFAULT,
                        help=f"URL de OpenDataManager (default: {ODM_URL_DEFAULT})")
    parser.add_argument("--force", action="store_true",
                        help="Fuerza nueva extracción aunque ya exista dataset")
    args = parser.parse_args()

    if args.output:
        fichero = args.output / "notarios_raw.csv"
    else:
        fichero = FICHERO_DEFAULT

    main(args.odm_url, fichero, args.force)
