#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vigilancia SIPI<-ODM (CLI). Requiere ODM_BASE_URL (instancia viva de ODM).

  python scripts/vigilancia.py --list                  # datasets expuestos por ODM
  python scripts/vigilancia.py --sync                  # sincroniza maestros (dry-run: LogSink)
  python scripts/vigilancia.py --refresh <RESOURCE_ID> # refresco a demanda
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from modules.opendata import ODMClient, sincronizar_todos, descubrir_datasets, refrescar, LogSink  # noqa: E402

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sync", action="store_true")
    ap.add_argument("--refresh")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    c = ODMClient()  # config por entorno (ODM_BASE_URL, ...)
    if args.list:
        print(json.dumps(descubrir_datasets(c), ensure_ascii=False, indent=2))
    elif args.refresh:
        print(refrescar(c, args.refresh))
    elif args.sync:
        sink = LogSink()
        res = sincronizar_todos(c, sink, limit=args.limit)
        print("Sincronización (dry-run):", json.dumps(res, ensure_ascii=False))
        print("Muestra:", json.dumps(sink.muestra, ensure_ascii=False, indent=2))
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
