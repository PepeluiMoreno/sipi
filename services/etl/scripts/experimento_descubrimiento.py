#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Banco de experimentos del descubrimiento (CLI).

Ejemplos:
  # una ejecución con los parámetros por defecto
  python scripts/experimento_descubrimiento.py --csv-dir DATA --osm-json osm.json \
      --osm-boundaries muni.json --provincia Pontevedra

  # con una configuración propia (JSON de DiscoveryConfig)
  python scripts/experimento_descubrimiento.py ... --config mi_config.json

  # barrido de un parámetro
  python scripts/experimento_descubrimiento.py ... --barrido umbral_alta 0.68 0.72 0.78
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from modules.fusion.config import DiscoveryConfig          # noqa: E402
from modules.fusion.experimento import comparar, barrido   # noqa: E402


def _num(v):
    try:
        return int(v) if v.isdigit() else float(v)
    except (ValueError, AttributeError):
        return v


def main():
    ap = argparse.ArgumentParser(description="Banco de experimentos del descubrimiento")
    ap.add_argument("--csv-dir", required=True)
    ap.add_argument("--osm-json", required=True)
    ap.add_argument("--osm-boundaries")
    ap.add_argument("--provincia")
    ap.add_argument("--ccaa")
    ap.add_argument("--config", help="JSON de DiscoveryConfig")
    ap.add_argument("--barrido", nargs="+", metavar=("PARAM", "VALOR"),
                    help="parámetro a barrer seguido de sus valores")
    args = ap.parse_args()

    run_kw = dict(provincia=args.provincia, ccaa=args.ccaa,
                  osm_boundaries=args.osm_boundaries)
    base = DiscoveryConfig.from_json(args.config) if args.config else DiscoveryConfig()

    if args.barrido:
        parametro, *valores = args.barrido
        barrido(args.csv_dir, args.osm_json, base, parametro,
                [_num(v) for v in valores], **run_kw)
    else:
        comparar(args.csv_dir, args.osm_json, {"config": base}, **run_kw)


if __name__ == "__main__":
    main()
