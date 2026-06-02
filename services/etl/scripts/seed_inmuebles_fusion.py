#!/usr/bin/env python3
"""CLI: fusiona CEE × OSM y genera el seed con procedencia y bandas de confianza.

Uso:
    python scripts/seed_inmuebles_fusion.py \
        --cee  apps/api/ETL/preparation/data/output \
        --osm  /ruta/osm_provincia.json \
        --provincia Pontevedra \
        --out  /tmp/pontevedra

Genera: <out>_seed.json, <out>_revision.json, <out>_resumen.json
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from modules.fusion import run_fusion, write_outputs  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Fusión CEE × OSM -> seed de Inmuebles")
    ap.add_argument("--cee", required=True, help="Directorio con los CSV del CEE")
    ap.add_argument("--osm", required=True, help="JSON de Overpass (bienes religiosos)")
    ap.add_argument("--provincia", help="Filtrar CEE por provincia")
    ap.add_argument("--ccaa", help="Filtrar CEE por comunidad autónoma")
    ap.add_argument("--out", required=True, help="Prefijo de los ficheros de salida")
    args = ap.parse_args()

    entidades, resumen = run_fusion(args.cee, args.osm, provincia=args.provincia, ccaa=args.ccaa)
    write_outputs(entidades, resumen, args.out)
    print("Resumen de la fusión:")
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    print(f"Salida: {args.out}_seed.json / _revision.json / _resumen.json")


if __name__ == "__main__":
    main()
