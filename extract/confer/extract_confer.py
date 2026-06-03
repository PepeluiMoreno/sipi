#!/usr/bin/env python3
"""
extract/confer/extract_confer.py — extrae congregaciones y comunidades del mapa CONFER

Fuente: Power BI público en https://confer.es/la-vida-religiosa-en-espana/mapa-de-congregaciones/
API:    https://wabi-west-europe-e-primary-api.analysis.windows.net/public/reports/querydata

Tablas del modelo Power BI:
  itgr_congregacion  → nombre_confer, pagina_web, itgr_afiliadaaconfer
  Entidades          → tipo_entidad, provincia, localidad, continente, pais, estado

Produce dos JSONL:
  data/output/confer/congregaciones.jsonl
  data/output/confer/comunidades.jsonl

Uso:
    python extract/confer/extract_confer.py
    python extract/confer/extract_confer.py --dry-run
    python extract/confer/extract_confer.py --solo-congregaciones
    python extract/confer/extract_confer.py --solo-comunidades
"""

import argparse
import json
import logging
import time
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Power BI identifiers (report público CONFER) ──────────────────────────────
# Embed URL token decoded: {"k":"5a615f34-...","t":"5487283f-..."}
RESOURCE_KEY = "5a615f34-c120-4fed-bcc1-36363c54ff04"
MODEL_ID     = 2721370
DATASET_ID   = "6f51204d-cbf7-43c8-ac29-dfc58aad4bef"
REPORT_ID    = "b55dc753-a2c9-4bc1-9b3a-08a4e08f03b4"
VISUAL_ID    = "5db35b33b48d207fc294"

API_URL = "https://wabi-west-europe-e-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://app.powerbi.com",
    "Referer": "https://app.powerbi.com/",
    "X-PowerBI-ResourceKey": RESOURCE_KEY,
}

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "output" / "confer"

# Filtros base (Europa + CONFER afiliadas)
WHERE_BASE = [
    {"Condition": {"In": {
        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "e"}}, "Property": "Continente"}}],
        "Values": [[{"Literal": {"Value": "'Europa'"}}]],
    }}},
    {"Condition": {"In": {
        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "i"}}, "Property": "itgr_afiliadaaconfer"}}],
        "Values": [[{"Literal": {"Value": "true"}}]],
    }}},
]


# ── DSR decoder ────────────────────────────────────────────────────────────────

def decode_dsr(ds: dict) -> list[dict]:
    """
    Decodifica el formato DSR (Data Shape Result) comprimido de Power BI.

    Estructura:
      ds["ValueDicts"]   → {"D0": [...], "D1": [...], ...}  diccionarios de valores
      ds["PH"][n]["DM0"] → lista de filas comprimidas
      ds["IC"]           → bool, False = hay más páginas (not complete)
      ds["RT"]           → restart token para siguiente página

    Cada fila puede tener:
      S  → schema de columnas: [{N:"G0", T:1, DN:"D0"}, ...]
           T=1 → referencia a diccionario DN; T=0/4 → valor directo
      C  → valores comprimidos (índices o directos)
      R  → bitmask de columnas que repiten valor anterior
      Ø  → bitmask de columnas que son nulas
    """
    value_dicts = ds.get("ValueDicts", {})
    rows_out = []

    for group in ds.get("PH", []):
        dm0 = group.get("DM0", [])
        schema = []        # [{N, T, DN}, ...]
        prev_vals = {}     # {col_name: value}

        for row in dm0:
            # Actualizar schema si viene en esta fila
            if "S" in row:
                schema = row["S"]

            n_cols = len(schema)
            null_mask   = row.get("Ø", 0)
            repeat_mask = row.get("R", 0)
            c_values    = row.get("C", [])

            c_idx = 0
            current = {}

            for col_i, col_def in enumerate(schema):
                col_name = col_def["N"]    # "G0", "G1", ...
                is_null   = bool(null_mask   & (1 << col_i))
                is_repeat = bool(repeat_mask & (1 << col_i))

                if is_null:
                    current[col_name] = None
                elif is_repeat:
                    current[col_name] = prev_vals.get(col_name)
                else:
                    if c_idx < len(c_values):
                        raw = c_values[c_idx]
                        c_idx += 1
                        # T=1 → índice en diccionario DN
                        if col_def.get("T") == 1:
                            dn = col_def.get("DN", "")
                            d  = value_dicts.get(dn, [])
                            current[col_name] = d[raw] if isinstance(raw, int) and raw < len(d) else raw
                        else:
                            current[col_name] = raw
                    else:
                        current[col_name] = None

            prev_vals = {**prev_vals, **current}
            rows_out.append(dict(current))

    return rows_out


def has_more(ds: dict) -> bool:
    """IC=False en el DS significa que hay más datos (not complete)."""
    return not ds.get("IC", True)


# ── Construcción de payloads ───────────────────────────────────────────────────

def _payload(selects: list, projections: list, where_extra: list = None,
             restart_token: list = None, count: int = 500) -> dict:
    where = WHERE_BASE + (where_extra or [])
    window = {"Count": count}
    if restart_token:
        window["RestartTokens"] = [restart_token]

    return {
        "version": "1.0.0",
        "queries": [{
            "Query": {"Commands": [{"SemanticQueryDataShapeCommand": {
                "Query": {
                    "Version": 2,
                    "From": [
                        {"Name": "i", "Entity": "itgr_congregacion", "Type": 0},
                        {"Name": "e", "Entity": "Entidades",         "Type": 0},
                    ],
                    "Select": selects,
                    "Where": where,
                    "OrderBy": [{
                        "Direction": 1,
                        "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "i"}}, "Property": "Nombre oficial CONFER"}},
                    }],
                },
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": projections, "Subtotal": 1}]},
                    "DataReduction": {"DataVolume": 3, "Primary": {"Window": window}},
                    "Version": 1,
                    "ExecutionMetricsKind": 1,
                },
            }}]},
            "QueryId": "",
            "ApplicationContext": {
                "DatasetId": DATASET_ID,
                "Sources": [{"ReportId": REPORT_ID, "VisualId": VISUAL_ID}],
            },
        }],
        "cancelQueries": [],
        "modelId": MODEL_ID,
    }


def _col(src: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop},
            "Name": f"{src}.{prop}"}


# ── Paginación genérica ────────────────────────────────────────────────────────

def paginar(client: httpx.Client, build_payload_fn, etiqueta: str,
            count: int = 500) -> list[dict]:
    todos = []
    restart_token = None
    page = 0

    while True:
        page += 1
        log.info(f"  {etiqueta} — página {page}")
        payload = build_payload_fn(restart_token, count)

        try:
            r = client.post(API_URL, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            log.error(f"  Error en página {page}: {exc}")
            break

        try:
            ds = data["results"][0]["result"]["data"]["dsr"]["DS"][0]
        except (KeyError, IndexError):
            log.error(f"  Respuesta inesperada: {str(data)[:300]}")
            break

        rows = decode_dsr(ds)
        if not rows:
            log.info(f"  Sin filas en página {page}. Fin.")
            break

        todos.extend(rows)
        log.info(f"  +{len(rows)} filas (total: {len(todos)})")

        if not has_more(ds):
            log.info(f"  IC=True — datos completos.")
            break

        rt = ds.get("RT")
        if not rt:
            log.warning(f"  Sin RT para continuar paginación. Fin.")
            break
        restart_token = rt[0]  # lista de valores del último registro
        time.sleep(0.3)

    return todos


# ── Queries específicas ────────────────────────────────────────────────────────

SELECTS_CONG = [
    _col("i", "Nombre oficial CONFER"),
    _col("i", "Página web"),
    _col("e", "Tipo de entidad"),
]
PROJ_CONG = [0, 1, 2]

SELECTS_COM = [
    _col("i", "Nombre oficial CONFER"),
    _col("e", "Tipo de entidad"),
    _col("e", "Provincia"),
    _col("e", "Localidad"),
    _col("e", "Estado"),
]
PROJ_COM = [0, 1, 2, 3, 4]


def build_cong(rt, count):
    return _payload(SELECTS_CONG, PROJ_CONG, restart_token=rt, count=count)


def build_com(rt, count):
    return _payload(SELECTS_COM, PROJ_COM, restart_token=rt, count=count)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extrae datos CONFER desde Power BI")
    parser.add_argument("--dry-run",            action="store_true")
    parser.add_argument("--solo-congregaciones", action="store_true")
    parser.add_argument("--solo-comunidades",    action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:

        # ── 1. Congregaciones ─────────────────────────────────────────────────
        if not args.solo_comunidades:
            log.info("=== Extrayendo congregaciones ===")
            rows = paginar(client, build_cong, "congregaciones")

            # Deduplicar: 1 fila por congregación (pueden venir varias por tipo_entidad)
            seen = {}
            for r in rows:
                nombre = (r.get("G0") or "").strip()
                if not nombre:
                    continue
                if nombre not in seen:
                    seen[nombre] = {
                        "nombre_confer": nombre,
                        "pagina_web":   (r.get("G1") or "").strip() or None,
                        "tipos":        set(),
                    }
                tipo = (r.get("G2") or "").strip()
                if tipo:
                    seen[nombre]["tipos"].add(tipo)

            congregaciones = [
                {**v, "tipos": sorted(v["tipos"])}
                for v in seen.values()
            ]
            log.info(f"{len(congregaciones)} congregaciones únicas (de {len(rows)} filas)")

            if args.dry_run:
                for c in congregaciones[:5]:
                    log.info(f"  {c}")
            else:
                out = OUTPUT_DIR / "congregaciones.jsonl"
                with open(out, "w", encoding="utf-8") as f:
                    for obj in congregaciones:
                        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                log.info(f"Guardado: {out}")

        # ── 2. Comunidades / casas ────────────────────────────────────────────
        if not args.solo_congregaciones:
            log.info("=== Extrayendo comunidades/casas ===")
            rows = paginar(client, build_com, "comunidades")

            comunidades = []
            for r in rows:
                obj = {
                    "congregacion_confer": (r.get("G0") or "").strip() or None,
                    "tipo_entidad":        (r.get("G1") or "").strip() or None,
                    "provincia":           (r.get("G2") or "").strip() or None,
                    "localidad":           (r.get("G3") or "").strip() or None,
                    "estado":              str(r.get("G4") or "").strip() or None,
                }
                comunidades.append(obj)

            log.info(f"{len(comunidades)} comunidades/casas extraídas")

            if args.dry_run:
                for c in comunidades[:5]:
                    log.info(f"  {c}")
            else:
                out = OUTPUT_DIR / "comunidades.jsonl"
                with open(out, "w", encoding="utf-8") as f:
                    for obj in comunidades:
                        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
                log.info(f"Guardado: {out}")


if __name__ == "__main__":
    main()
