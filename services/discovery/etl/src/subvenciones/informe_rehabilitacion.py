# -*- coding: utf-8 -*-
"""Informe de concesiones de OBRA de rehabilitación a entidades NIF R/G.

Herramienta reproducible y a demanda. En vez de barrer los ~27M de concesiones,
PRE-FILTRA en el SNPSAP por `descripcion` (títulos de obra: rehabilitación,
restauración, conservación…) → reduce a decenas de miles → puntúa NIF R/G con el
scorer canónico de sipi-core → clasifica OBRA de edificio vs BIEN MUEBLE
(imágenes, retablos, órganos… que no son obras) → emite CSV + resumen.

    python -m subvenciones.informe_rehabilitacion --salida informe.csv
    python -m subvenciones.informe_rehabilitacion --desde-anio 2024 --solo-r
    python -m subvenciones.informe_rehabilitacion --terminos rehabilitación obras cubierta \
        --min-importe 50000 --umbral-g 0.6 --salida /tmp/rehab.csv

Notas:
- NIF R (entidad religiosa, RER) es ancla determinista; NIF G (asociación/
  fundación) es ruidoso: con --umbral-g se exige señal religiosa mínima, pero la
  limpieza fina de fundaciones confesionales requiere el cruce con el censo
  (entidades religiosas / inmatriculaciones), que vive en el motor con BD.
- Fuente directa del SNPSAP para uso autónomo y rápido. El pipeline completo y
  neutral (vía ODM + censo) es el del motor de vigilancia de la API.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from typing import Iterator, List, Optional

from sipi_core.modules.discovery.subvenciones import (
    to_concesion, evaluar, clasificar_obra,
)

API_DEFECTO = "https://www.infosubvenciones.es/bdnstrans/api"
VPD_DEFECTO = "GE"
TERMINOS_OBRA = [
    "rehabilitación", "restauración", "conservación", "consolidación",
    "cubierta", "fachada", "reforma", "reparación", "obras",
]


def _get(base: str, endpoint: str, params: dict) -> dict:
    url = f"{base}/{endpoint}/busqueda?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "sipi-informe-rehab"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def iter_concesiones_obra(base: str, terminos: List[str], desde: Optional[int],
                          hasta: Optional[int], vpd: str = VPD_DEFECTO,
                          page_size: int = 10000, pausa: float = 0.0) -> Iterator[dict]:
    """Concesiones cuyo título casa con cada término (pre-filtro de servidor),
    unidas y deduplicadas por codConcesion. order=codConcesion (clave única) para
    que la paginación profunda no se rompa."""
    vistos: set = set()
    for term in terminos:
        pg = 0
        while True:
            params = {"vpd": vpd, "order": "codConcesion", "direccion": "desc",
                      "pageSize": page_size, "page": pg, "descripcion": term}
            if desde:
                params["fechaDesde"] = f"01/01/{desde}"
            if hasta:
                params["fechaHasta"] = f"31/12/{hasta}"
            try:
                d = _get(base, "concesiones", params)
            except Exception as e:  # noqa: BLE001
                print(f"  aviso: '{term}' pág {pg} falló ({e})", file=sys.stderr)
                break
            content = d.get("content") or []
            if not content:
                break
            for rec in content:
                cod = rec.get("codConcesion")
                if cod and cod in vistos:
                    continue
                if cod:
                    vistos.add(cod)
                yield rec
            if d.get("last"):
                break
            pg += 1
            if pausa:
                time.sleep(pausa)


def construir_filas(records: Iterator[dict], umbral_g: float = 0.0) -> List[dict]:
    """Puntúa NIF R/G, clasifica obra/mueble y arma las filas del informe."""
    filas = []
    for rec in records:
        c = to_concesion(rec)
        if c is None:               # descarta personas físicas y NIF fuera de R/G
            continue
        f = evaluar(c.nif, c.nombre, *c.textos_finalidad(None))
        clase = clasificar_obra(c.convocatoria, rec.get("descripcionCooficial"), c.nombre)
        letra = c.nif[:1].upper()
        # G solo si alcanza el umbral de señal religiosa (R no se filtra).
        if letra == "G" and umbral_g and f.valor < umbral_g:
            continue
        filas.append({
            "nif": c.nif, "letra": letra, "beneficiario": c.nombre,
            "importe_eur": int(c.importe or 0), "anio": str(c.fecha_concesion or "")[:4],
            "clase_obra": clase, "fiabilidad": round(f.valor, 2),
            "codConcesion": c.cod_concesion, "titulo": (c.convocatoria or "")[:160],
        })
    return filas


def filtrar(filas: List[dict], solo_r: bool, incluir_mueble: bool,
            min_importe: int) -> List[dict]:
    out = filas
    if solo_r:
        out = [x for x in out if x["letra"] == "R"]
    if not incluir_mueble:
        out = [x for x in out if x["clase_obra"] != "mueble"]
    if min_importe:
        out = [x for x in out if x["importe_eur"] >= min_importe]
    return sorted(out, key=lambda x: -x["importe_eur"])


def escribir_csv(filas: List[dict], salida: str) -> None:
    cols = ["nif", "letra", "beneficiario", "importe_eur", "anio",
            "clase_obra", "fiabilidad", "codConcesion", "titulo"]
    with open(salida, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def resumen(filas: List[dict]) -> str:
    from collections import Counter
    tot = sum(x["importe_eur"] for x in filas)
    porletra = Counter(x["letra"] for x in filas)
    porclase = Counter(x["clase_obra"] for x in filas)
    return (f"{len(filas)} concesiones · {tot:,.0f}€\n".replace(",", ".")
            + f"  por NIF: {dict(porletra)}\n  por clase: {dict(porclase)}")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Informe de concesiones de obra de rehabilitación a NIF R/G")
    p.add_argument("--api", default=API_DEFECTO, help="Base del SNPSAP")
    p.add_argument("--vpd", default=VPD_DEFECTO)
    p.add_argument("--terminos", nargs="+", default=TERMINOS_OBRA,
                   help="Términos de obra para el pre-filtro por descripción")
    p.add_argument("--desde-anio", type=int, default=None)
    p.add_argument("--hasta-anio", type=int, default=None)
    p.add_argument("--solo-r", action="store_true", help="Solo NIF R (religioso determinista)")
    p.add_argument("--umbral-g", type=float, default=0.0,
                   help="Exige esta fiabilidad mínima a las G (señal religiosa)")
    p.add_argument("--incluir-mueble", action="store_true",
                   help="Incluye restauración de bienes muebles (por defecto, fuera)")
    p.add_argument("--min-importe", type=int, default=0)
    p.add_argument("--pausa", type=float, default=0.0, help="Cortesía entre páginas (s)")
    p.add_argument("--salida", default="concesiones_rehabilitacion_RG.csv")
    args = p.parse_args(argv)

    recs = iter_concesiones_obra(args.api, args.terminos, args.desde_anio,
                                 args.hasta_anio, vpd=args.vpd, pausa=args.pausa)
    filas = construir_filas(recs, umbral_g=args.umbral_g)
    filas = filtrar(filas, args.solo_r, args.incluir_mueble, args.min_importe)
    escribir_csv(filas, args.salida)
    print(resumen(filas))
    print(f"→ {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
