#!/usr/bin/env python3
"""
transform/dir3/transformar_dir3.py — T3: DIR3 → CSV normalizado de administraciones

Lee UnidadOrganica.csv del catálogo DIR3 y genera:
    data/input/dir3/administraciones.csv

Solo conserva niveles 1–4 y unidades vigentes (Estado=V).
Los códigos de provincia y municipio se normalizan al formato INE
para poder enlazar con las tablas de geografía.

Fuente: data/input/dir3/UnidadOrganica.csv
        (descargado por extract/dir3/descargar_dir3.py)

Uso:
    python transform/dir3/transformar_dir3.py
    python transform/dir3/transformar_dir3.py --input data/input/dir3/UnidadOrganica.csv
    python transform/dir3/transformar_dir3.py --nivel-max 3
"""

import argparse
import csv
import sys
from pathlib import Path

INPUT_DEFAULT  = Path(__file__).parent.parent.parent / "data" / "input" / "dir3" / "UnidadOrganica.csv"
OUTPUT_DEFAULT = Path(__file__).parent.parent.parent / "data" / "input" / "dir3" / "administraciones.csv"

# Mapeo de abreviaturas de ámbito DIR3 → etiqueta legible
AMBITO_MAP = {
    "E": "estatal",
    "A": "autonomico",
    "L": "local",
    "U": "universitario",
    "J": "judicial",
    "O": "otro",
}

# Columnas que puede tener el CSV del DIR3 (los nombres cambian entre versiones)
# Definimos alias para normalizar
COL_ALIAS = {
    # código
    "CODIGODIR3": "codigo_dir3",
    "CODIGO_DIR3": "codigo_dir3",
    "CODIGOUNIDADORGANICA": "codigo_dir3",
    # nombre
    "DENOMINACION": "nombre",
    "NOMBRE": "nombre",
    # padre
    "CODIGOPADRE": "codigo_padre",
    "CODIGO_PADRE": "codigo_padre",
    "CODIGOUNIDADORGANICAPADRE": "codigo_padre",
    # nivel 1–4
    "NIVEL": "nivel",
    "NIVELJERARQUICO": "nivel",
    # estado V/E/T
    "ESTADO": "estado",
    # fechas
    "FECHAALTAOFICIAL": "fecha_alta",
    "FECHABAJAOFICIAL": "fecha_baja",
    # territorio
    "CODIGOCOMUNIDADAUTONOMA": "cod_ccaa",
    "CODIGOPROVINCIA": "cod_provincia",
    "CODIGOMUNICIPIO": "cod_municipio",
    # tipo de órgano
    "TIPOUNIDADORGANICA": "tipo_organo",
    "TIPO": "tipo_organo",
    # ámbito territorial
    "AMBITOUNIDADORGANICA": "ambito",
    "AMBITORIAL": "ambito",
}


def normalizar_columnas(row: dict) -> dict:
    return {COL_ALIAS.get(k.upper().replace(" ", ""), k.lower()): v
            for k, v in row.items()}


def transformar(input_path: Path, output_path: Path, nivel_max: int):
    if not input_path.exists():
        print(f"ERROR: no encontrado {input_path}")
        print("       Ejecuta primero: python extract/dir3/descargar_dir3.py")
        sys.exit(1)

    # Detectar encoding (DIR3 usa latin-1 habitualmente)
    for enc in ("utf-8-sig", "latin-1", "utf-8"):
        try:
            with open(input_path, encoding=enc) as f:
                sample = f.read(1024)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    else:
        encoding = "latin-1"

    print(f"Leyendo {input_path.name} (encoding: {encoding})...")

    filas_out = []
    omitidas = {"nivel_alto": 0, "extinguida": 0, "sin_codigo": 0}

    with open(input_path, encoding=encoding, newline="") as f:
        # Algunos CSVs del DIR3 usan ';' como separador
        sample = f.read(2048)
        f.seek(0)
        sep = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=sep)

        for row in reader:
            r = normalizar_columnas(row)

            codigo = r.get("codigo_dir3", "").strip()
            if not codigo:
                omitidas["sin_codigo"] += 1
                continue

            estado = r.get("estado", "V").strip().upper()
            if estado not in ("V", ""):  # V=Vigente, vacío=asumir vigente
                omitidas["extinguida"] += 1
                continue

            try:
                nivel = int(r.get("nivel", "1").strip())
            except ValueError:
                nivel = 1

            if nivel > nivel_max:
                omitidas["nivel_alto"] += 1
                continue

            # Normalizar códigos INE (provincia 2 dígitos, municipio 5 dígitos)
            cod_prov = r.get("cod_provincia", "").strip().zfill(2) if r.get("cod_provincia") else ""
            cod_mun  = r.get("cod_municipio", "").strip().zfill(5) if r.get("cod_municipio") else ""
            cod_ccaa = r.get("cod_ccaa", "").strip().zfill(2) if r.get("cod_ccaa") else ""

            ambito_raw = r.get("ambito", "").strip().upper()
            ambito = AMBITO_MAP.get(ambito_raw, ambito_raw.lower() if ambito_raw else "")

            filas_out.append({
                "codigo_dir3":    codigo,
                "nombre":         r.get("nombre", "").strip(),
                "nivel":          nivel,
                "tipo_organo":    r.get("tipo_organo", "").strip(),
                "ambito":         ambito,
                "codigo_padre":   r.get("codigo_padre", "").strip(),
                "cod_ccaa_ine":   cod_ccaa,
                "cod_prov_ine":   cod_prov,
                "cod_mun_ine":    cod_mun,
                "fecha_alta":     r.get("fecha_alta", "").strip(),
                "fecha_baja":     r.get("fecha_baja", "").strip(),
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        campos = ["codigo_dir3", "nombre", "nivel", "tipo_organo", "ambito",
                  "codigo_padre", "cod_ccaa_ine", "cod_prov_ine", "cod_mun_ine",
                  "fecha_alta", "fecha_baja"]
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas_out)

    print(f"  → {output_path.name}: {len(filas_out):,} unidades (niveles 1–{nivel_max})")
    print(f"     Omitidas — extinguidas: {omitidas['extinguida']:,}, "
          f"nivel>{nivel_max}: {omitidas['nivel_alto']:,}, "
          f"sin código: {omitidas['sin_codigo']}")
    print(f"\n✓ Completado")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="T3: transforma catálogo DIR3 → CSV normalizado"
    )
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT,
                        help=f"Ruta a UnidadOrganica.csv (default: {INPUT_DEFAULT})")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT,
                        help=f"CSV de salida (default: {OUTPUT_DEFAULT})")
    parser.add_argument("--nivel-max", type=int, default=4,
                        help="Nivel jerárquico máximo a incluir (default: 4)")
    args = parser.parse_args()
    transformar(args.input, args.output, args.nivel_max)
