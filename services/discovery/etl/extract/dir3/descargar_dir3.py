#!/usr/bin/env python3
"""
extract/dir3/descargar_dir3.py — Extracción: descarga el catálogo DIR3

Fuente oficial:
    Portal de la Administración Electrónica (PAe) — MPTFP
    Directorio Común de Unidades Orgánicas y Oficinas (DIR3)
    https://administracionelectronica.gob.es/ctt/dir3

    El catálogo se actualiza mensualmente. Contiene todas las unidades
    orgánicas y oficinas de las Administraciones Públicas españolas con
    sus códigos DIR3 oficiales y jerarquía (niveles 1–4).

    El ZIP contiene entre otros:
        UnidadOrganica.csv  — unidades con jerarquía, nivel, ámbito territorial
        Oficina.csv         — oficinas de registro (SIR)

    Campos relevantes de UnidadOrganica.csv:
        CodigoDIR3          — código oficial (ej. "E04921201")
        Denominacion        — nombre oficial
        CodigoPadre         — código DIR3 de la unidad padre (jerarquía)
        Nivel               — nivel jerárquico (1=Administración, 2=Entidad,
                              3=Organismo, 4=Unidad)
        Estado              — V=Vigente, E=Extinguida, T=Transitoria
        FechaAltaOficial    — fecha de alta
        FechaBajaOficial    — fecha de baja (si extinguida)
        CodigoComunidadAutonoma — código INE de la CA de adscripción
        CodigoProvincia     — código INE de la provincia de sede
        CodigoMunicipio     — código INE del municipio de sede

    Descarga alternativa vía datos.gob.es:
        https://datos.gob.es/es/catalogo/e00003705-directorio-comun-dir3

Uso:
    python extract/dir3/descargar_dir3.py
    python extract/dir3/descargar_dir3.py --output data/input/dir3/
"""

import argparse
import sys
import urllib.request
import zipfile
from pathlib import Path

URL_DIR3_ZIP = (
    "https://administracionelectronica.gob.es/ctt/resources/"
    "Soluciones/238/descargas/Dir3CatalogoEntidadesUnidades.zip"
)

DESTINO_DEFAULT = Path(__file__).parent.parent.parent / "data" / "input" / "dir3"

# Ficheros del ZIP que nos interesan
FICHEROS_OBJETIVO = {"UnidadOrganica.csv", "Oficina.csv"}


def descargar(destino: Path):
    destino.mkdir(parents=True, exist_ok=True)
    zip_path = destino / "Dir3CatalogoEntidadesUnidades.zip"

    print(f"Descargando DIR3 desde:")
    print(f"  {URL_DIR3_ZIP}")
    print("  (puede tardar unos minutos, el fichero supera los 50 MB)")

    try:
        urllib.request.urlretrieve(URL_DIR3_ZIP, zip_path)
        print(f"  Descargado: {zip_path.stat().st_size / 1_048_576:.1f} MB")
    except Exception as e:
        print(f"ERROR al descargar: {e}")
        print()
        print("Descarga manual:")
        print(f"  1. Accede a: https://administracionelectronica.gob.es/ctt/dir3/descargas")
        print(f"  2. Descarga 'Catálogo de Entidades y Unidades Orgánicas'")
        print(f"  3. Guarda el ZIP en: {destino}/")
        sys.exit(1)

    print("Extrayendo ficheros...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for nombre in zf.namelist():
            fname = Path(nombre).name
            if fname in FICHEROS_OBJETIVO:
                zf.extract(nombre, destino)
                # Mover a raíz del directorio destino si está en subcarpeta
                extraido = destino / nombre
                destino_final = destino / fname
                if extraido != destino_final:
                    extraido.rename(destino_final)
                print(f"  → {destino_final.name}  ({destino_final.stat().st_size:,} bytes)")

    print(f"\n✓ Ficheros DIR3 disponibles en {destino}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descarga el catálogo DIR3 (unidades orgánicas)"
    )
    parser.add_argument("--output", type=Path, default=DESTINO_DEFAULT,
                        help=f"Directorio de destino (default: {DESTINO_DEFAULT})")
    args = parser.parse_args()
    descargar(args.output)
