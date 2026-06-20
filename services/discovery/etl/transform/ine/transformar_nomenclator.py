#!/usr/bin/env python3
"""
transform/ine/transformar_nomenclator.py — T1: Nomenclátor INE → CSVs normalizados

Lee codmun{año}.xlsx del INE y genera tres CSVs en data/input/ine/:
    comunidades_autonomas.csv   — código INE, nombre oficial
    provincias.csv              — código INE, nombre oficial, código CCAA
    municipios.csv              — código INE completo (CPRO+CMUN+DC), nombre, código provincia

Los nombres de CCAA y provincia se resuelven con tablas de mapeo INE oficiales
(los códigos son estables; los nombres cambian excepcionalmente por ley).

Fuente: https://www.ine.es/daco/daco42/codmun/codmun{año}.xlsx

Uso:
    python transform/ine/transformar_nomenclator.py
    python transform/ine/transformar_nomenclator.py --input data/input/ine/codmun2024.xlsx
    python transform/ine/transformar_nomenclator.py --output data/input/ine/
"""

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

# ── Mapeos oficiales INE (estables) ──────────────────────────────────────────

CCAA: dict[str, str] = {
    "01": "Andalucía",
    "02": "Aragón",
    "03": "Asturias, Principado de",
    "04": "Balears, Illes",
    "05": "Canarias",
    "06": "Cantabria",
    "07": "Castilla y León",
    "08": "Castilla-La Mancha",
    "09": "Cataluña",
    "10": "Comunitat Valenciana",
    "11": "Extremadura",
    "12": "Galicia",
    "13": "Madrid, Comunidad de",
    "14": "Murcia, Región de",
    "15": "Navarra, Comunidad Foral de",
    "16": "País Vasco",
    "17": "Rioja, La",
    "18": "Ceuta",
    "19": "Melilla",
}

PROVINCIAS: dict[str, tuple[str, str]] = {
    # código: (nombre, código_ccaa)
    "01": ("Álava",                   "16"),
    "02": ("Albacete",                "08"),
    "03": ("Alicante/Alacant",        "10"),
    "04": ("Almería",                 "01"),
    "05": ("Ávila",                   "07"),
    "06": ("Badajoz",                 "11"),
    "07": ("Balears, Illes",          "04"),
    "08": ("Barcelona",               "09"),
    "09": ("Burgos",                  "07"),
    "10": ("Cáceres",                 "11"),
    "11": ("Cádiz",                   "01"),
    "12": ("Castellón/Castelló",      "10"),
    "13": ("Ciudad Real",             "08"),
    "14": ("Córdoba",                 "01"),
    "15": ("Coruña, A",               "12"),
    "16": ("Cuenca",                  "08"),
    "17": ("Girona",                  "09"),
    "18": ("Granada",                 "01"),
    "19": ("Guadalajara",             "08"),
    "20": ("Gipuzkoa",                "16"),
    "21": ("Huelva",                  "01"),
    "22": ("Huesca",                  "02"),
    "23": ("Jaén",                    "01"),
    "24": ("León",                    "07"),
    "25": ("Lleida",                  "09"),
    "26": ("Rioja, La",               "17"),
    "27": ("Lugo",                    "12"),
    "28": ("Madrid",                  "13"),
    "29": ("Málaga",                  "01"),
    "30": ("Murcia",                  "14"),
    "31": ("Navarra",                 "15"),
    "32": ("Ourense",                 "12"),
    "33": ("Asturias",                "03"),
    "34": ("Palencia",                "07"),
    "35": ("Palmas, Las",             "05"),
    "36": ("Pontevedra",              "12"),
    "37": ("Salamanca",               "07"),
    "38": ("Santa Cruz de Tenerife",  "05"),
    "39": ("Cantabria",               "06"),
    "40": ("Segovia",                 "07"),
    "41": ("Sevilla",                 "01"),
    "42": ("Soria",                   "07"),
    "43": ("Tarragona",               "09"),
    "44": ("Teruel",                  "02"),
    "45": ("Toledo",                  "08"),
    "46": ("Valencia/València",       "10"),
    "47": ("Valladolid",              "07"),
    "48": ("Bizkaia",                 "16"),
    "49": ("Zamora",                  "07"),
    "50": ("Zaragoza",                "02"),
    "51": ("Ceuta",                   "18"),
    "52": ("Melilla",                 "19"),
}

# ── Lógica principal ──────────────────────────────────────────────────────────

INPUT_DEFAULT  = Path(__file__).parent.parent.parent / "data" / "input"
OUTPUT_DEFAULT = Path(__file__).parent.parent.parent / "data" / "input" / "ine"


def encontrar_excel(directorio: Path) -> Path:
    # Patrón actual INE: {YY}codmun.xlsx  (ej: 26codmun.xlsx)
    candidatos = sorted(directorio.glob("*codmun*.xlsx"), reverse=True)
    if not candidatos:
        print(f"ERROR: no se encontró ningún fichero codmun*.xlsx en {directorio}")
        print("       Ejecuta primero: python extract/ine/descargar_nomenclator.py")
        sys.exit(1)
    xlsx = candidatos[0]
    print(f"Usando: {xlsx.name}")
    return xlsx


def transformar(xlsx: Path, output: Path):
    """
    El Excel del INE {YY}codmun.xlsx tiene una hoja por provincia (01–52).
    Cada hoja:
      fila 0 — título general
      fila 1 — nombre de la provincia
      fila 2 — cabeceras: CPRO  CMUN  DC  NOMBRE
      fila 3+ — municipios
    El código de CCAA se resuelve a partir del código de provincia (mapeo PROVINCIAS).
    """
    output.mkdir(parents=True, exist_ok=True)
    xl = pd.ExcelFile(xlsx)

    # ── comunidades_autonomas.csv ─────────────────────────────────────────────
    path_ccaa = output / "comunidades_autonomas.csv"
    with open(path_ccaa, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo_ine", "nombre"])
        for cod, nombre in sorted(CCAA.items()):
            w.writerow([cod, nombre])
    print(f"  → {path_ccaa.name}: {len(CCAA)} comunidades autónomas")

    # ── provincias.csv ────────────────────────────────────────────────────────
    path_prov = output / "provincias.csv"
    with open(path_prov, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo_ine", "nombre", "codigo_ccaa"])
        for cod, (nombre, cod_ccaa) in sorted(PROVINCIAS.items()):
            w.writerow([cod, nombre, cod_ccaa])
    print(f"  → {path_prov.name}: {len(PROVINCIAS)} provincias")

    # ── municipios.csv — una hoja por provincia ───────────────────────────────
    path_mun = output / "municipios.csv"
    total = 0
    with open(path_mun, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo_ine", "nombre", "codigo_provincia"])

        for hoja in xl.sheet_names:
            cod_prov = hoja.zfill(2)
            if cod_prov not in PROVINCIAS:
                continue  # ignorar hojas auxiliares

            # Saltar filas de título/cabecera (las 2 primeras)
            df = pd.read_excel(xlsx, sheet_name=hoja, header=2, dtype=str)
            df.columns = [c.strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                cpro = str(row.get("CPRO", "")).strip().zfill(2)
                cmun = str(row.get("CMUN", "")).strip().zfill(3)
                dc   = str(row.get("DC",   "")).strip().zfill(1)
                nombre = str(row.get("NOMBRE", "")).strip()

                if not nombre or nombre.upper() in ("NAN", "NOMBRE", ""):
                    continue
                if not cmun or cmun == "000":
                    continue

                cod_mun = cpro + cmun  # 5 dígitos: CPRO(2) + CMUN(3), sin DC
                w.writerow([cod_mun, nombre, cod_prov])
                total += 1

    print(f"  → {path_mun.name}: {total:,} municipios")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="T1: transforma Nomenclátor INE → CSVs de geografía"
    )
    parser.add_argument("--input", type=Path, default=None,
                        help="Ruta al fichero codmun*.xlsx (default: busca en data/input/ine/)")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT,
                        help=f"Directorio de salida (default: {OUTPUT_DEFAULT})")
    args = parser.parse_args()

    xlsx = args.input if args.input else encontrar_excel(INPUT_DEFAULT)
    if not xlsx.exists():
        print(f"ERROR: fichero no encontrado: {xlsx}")
        sys.exit(1)

    print(f"\nTransformando {xlsx.name}...")
    transformar(xlsx, args.output)
    print("\n✓ Completado")
