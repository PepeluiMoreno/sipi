#!/usr/bin/env python3
"""
extract/ine/descargar_nomenclator.py — Extracción: descarga el Nomenclátor Municipal del INE

Fuente oficial:
    Instituto Nacional de Estadística (INE)
    Relación de municipios y sus códigos por provincias
    https://www.ine.es/daco/daco42/codmun/codmun{año}.xlsx

    El fichero se publica anualmente. Contiene todos los municipios de España
    con sus códigos oficiales (CODAUTO, CPRO, CMUN) conforme al Registro de
    Entidades Locales del Ministerio de Hacienda.

    Columnas del fichero:
        CODAUTO  — Código de comunidad autónoma (2 dígitos)
        CPRO     — Código de provincia (2 dígitos)
        CMUN     — Código de municipio dentro de la provincia (3 dígitos)
        DC       — Dígito de control
        NOMBRE   — Nombre oficial del municipio

    Nota: el fichero no incluye el nombre de la provincia ni de la CA;
    esos se resuelven en la fase Transform con tablas de mapeo INE.

Uso:
    python extract/ine/descargar_nomenclator.py
    python extract/ine/descargar_nomenclator.py --año 2023
    python extract/ine/descargar_nomenclator.py --output data/input/ine/
"""

import argparse
import sys
import urllib.request
from datetime import date
from pathlib import Path

AÑO_ACTUAL = date.today().year
# El INE usa el patrón {YY}codmun.xlsx (dos últimas cifras del año)
URL_PATRON = "https://www.ine.es/daco/daco42/codmun/{yy}codmun.xlsx"
DESTINO_DEFAULT = Path(__file__).parent.parent.parent / "data" / "input"


def descargar(año: int, destino: Path) -> Path:
    yy = str(año)[-2:]
    url = URL_PATRON.format(yy=yy)
    destino.mkdir(parents=True, exist_ok=True)
    nombre = f"{yy}codmun.xlsx"
    ruta = destino / nombre

    print(f"Descargando: {url}")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.ine.es/",
        })
        with urllib.request.urlopen(req) as r, open(ruta, "wb") as f:
            f.write(r.read())
        print(f"Guardado en: {ruta}  ({ruta.stat().st_size:,} bytes)")
        return ruta
    except Exception as e:
        if año == AÑO_ACTUAL:
            print(f"No disponible para {año}, intentando {año - 1}...")
            return descargar(año - 1, destino)
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descarga el Nomenclátor Municipal del INE"
    )
    parser.add_argument("--año", type=int, default=AÑO_ACTUAL,
                        help=f"Año del nomenclátor (default: {AÑO_ACTUAL})")
    parser.add_argument("--output", type=Path, default=DESTINO_DEFAULT,
                        help=f"Directorio de destino (default: {DESTINO_DEFAULT})")
    args = parser.parse_args()
    descargar(args.año, args.output)
