#!/usr/bin/env python3
"""
run_all.py — Orquestador ETL SIPI

Pipeline completo respetando dependencias FK:

    EXTRACT
      E1   ine/descargar_nomenclator              Descarga Nomenclátor Municipal del INE
      E2   dir3/descargar_dir3                    Descarga catálogo DIR3 (unidades orgánicas)
      E3   registradores/descargar_registros       Descarga catálogo CORPME vía OpenDataManager
      E4   cee/extract_diocesis                   Scrape diócesis y provincias eclesiásticas (CEE)
      E5   cee/extract_parroquias                 Scrape parroquias por diócesis (CEE)
      E6   mjer/extract_rer                       Extrae entidades del RER (MJER)
      E7   colegios-notariales/descargar_colegios  Descarga colegios notariales

    TRANSFORM
      T1  ine/transformar_nomenclator             Nomenclátor INE → CSVs de geografía oficial
      T2  dir3/transformar_dir3                   DIR3 → CSV normalizado de administraciones
      T3  cee/transformar_excel                   Excel CEE → CSVs de inmuebles por CCAA
      T4  registradores/transformar_registros      CORPME → CSV registros propiedad

    LOAD  (orden FK: cada paso depende de los anteriores)
      L1  cargar_geografia            CCAA → Provincias → Municipios  (INE)
      L2  cargar_tipologias           Catálogos base (tipos inmueble, estados, etc.)
      L3  cargar_entidades_locales     Entidades locales menores  (Geonames)
      L4  cargar_provincias_eclesiasticas  Provincias eclesiásticas  (CEE)
      L5  cargar_diocesis             Diócesis + obispos  (CEE)
      L6  cargar_parroquias           Parroquias  (CEE)
      L7  cargar_colegios_notariales  Colegios notariales
      L8  cargar_administraciones     Administraciones públicas niveles 1–4  (DIR3)
      L9  cargar_registros_propiedad  Registros de la Propiedad  (CORPME)
      L10 cargar_inmuebles            Inmuebles + Inmatriculaciones  (CEE)
      L11 cargar_entidades_religiosas  Entidades del RER  (MJER)

    EXTRACT (post-MVP)
      E8  osm_sync  Sync OSM → Inmuebles  [TODO]

Uso:
    # Pipeline completo:
    python workflows/run_all.py

    # Solo pasos de carga (datos ya descargados):
    python workflows/run_all.py --steps L1 L2 L3 L4 L5 L6 L7 L8 L9 L10 L11

    # Solo jerarquía eclesiástica:
    python workflows/run_all.py --steps E4 E5 L4 L5 L6

    # Simulación sin guardar:
    python workflows/run_all.py --dry-run
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT          = Path(__file__).parent.parent
EXTRACT_DIR   = ROOT / "extract"
TRANSFORM_DIR = ROOT / "transform"
LOAD_DIR      = ROOT / "load"
INE_DIR            = ROOT / "data" / "input" / "ine"
DIR3_DIR           = ROOT / "data" / "input" / "dir3"
TIPOLOGIAS_DIR     = ROOT / "data" / "input" / "tipologias"
CEE_CSV_DIR        = ROOT / "data" / "csv"
CEE_XLS            = ROOT / "data" / "input" / "Inmatriculaciones_CEE.xlsx"
CEE_OUT_DIR        = ROOT / "data" / "output" / "cee"
REGISTRADORES_DIR  = ROOT / "data" / "input" / "registradores"
MJER_OUT_DIR       = ROOT / "data" / "output" / "mjer"
NOTARIOS_DIR       = ROOT / "data" / "input" / "notarios"

PASOS = {
    # ── EXTRACT ──────────────────────────────────────────────────────────────
    "E1": (EXTRACT_DIR / "ine"                / "descargar_nomenclator.py",          "Descarga Nomenclátor INE"),
    "E2": (EXTRACT_DIR / "dir3"               / "descargar_dir3.py",                 "Descarga catálogo DIR3"),
    "E3": (EXTRACT_DIR / "registradores"      / "descargar_registros_propiedad.py",  "Descarga Registros de la Propiedad (CORPME)"),
    "E4": (EXTRACT_DIR / "cee"                / "extract_diocesis.py",               "Scrape diócesis y provincias eclesiásticas (CEE)"),
    "E5": (EXTRACT_DIR / "cee"                / "extract_parroquias.py",             "Scrape parroquias por diócesis (CEE)"),
    "E6": (EXTRACT_DIR / "mjer"               / "extract_rer.py",                    "Extrae entidades religiosas del RER (MJER)"),
    "E7": (EXTRACT_DIR / "colegios-notariales"/ "descargar_colegios_notariales.py",  "Descarga colegios notariales"),
    # ── TRANSFORM ────────────────────────────────────────────────────────────
    "T1": (TRANSFORM_DIR / "ine"              / "transformar_nomenclator.py",         "Nomenclátor INE → CSVs geografía"),
    "T2": (TRANSFORM_DIR / "dir3"             / "transformar_dir3.py",                "DIR3 → CSV administraciones"),
    "T3": (TRANSFORM_DIR / "cee"              / "transformar_excel.py",               "Excel CEE → CSVs inmuebles"),
    "T4": (TRANSFORM_DIR / "registradores"    / "transformar_registros_propiedad.py", "CORPME → CSV registros propiedad"),
    # ── LOAD (respeta orden FK) ───────────────────────────────────────────────
    "L1":  (LOAD_DIR / "cargar_geografia.py",                    "Carga geografía INE desde ODMGR (CCAA/Provincias/Municipios)"),
    "L2":  (LOAD_DIR / "cargar_tipologias.py",                   "Carga tipologías y catálogos"),
    "L3":  (LOAD_DIR / "cargar_entidades_locales_menores.py",    "Carga entidades locales menores desde ODMGR (Geonames)"),
    "L4":  (LOAD_DIR / "cargar_provincias_eclesiasticas.py",     "Carga provincias eclesiásticas (CEE scraper)"),
    "L5":  (LOAD_DIR / "cargar_diocesis_odmgr.py",               "Carga diócesis desde ODMGR (CEE XLSX)"),
    "L5b": (LOAD_DIR / "cargar_diocesis.py",                     "Carga diócesis — legado desde CSV+JSON CEE scraper"),
    "L6":  (LOAD_DIR / "cargar_parroquias.py",                   "Carga parroquias (CEE scraper)"),
    "L7":  (LOAD_DIR / "cargar_colegios_notariales.py",          "Carga colegios notariales (CSV local)"),
    "L8":  (LOAD_DIR / "cargar_administraciones_odmgr.py",       "Carga administraciones DIR3 desde ODMGR"),
    "L8b": (LOAD_DIR / "cargar_administraciones.py",             "Carga administraciones DIR3 — legado desde CSV local"),
    "L9":  (LOAD_DIR / "cargar_registros_propiedad_odmgr.py",    "Carga Registros de la Propiedad desde ODMGR (CORPME)"),
    "L9b": (LOAD_DIR / "cargar_registros_propiedad.py",          "Carga Registros de la Propiedad — legado desde CSV local"),
    "L10": (LOAD_DIR / "cargar_inmuebles.py",                    "Carga inmuebles e inmatriculaciones"),
    "L11": (LOAD_DIR / "cargar_entidades_religiosas.py",         "Carga entidades religiosas del RER (MJER scraper)"),
    "L12": (LOAD_DIR / "cargar_notarios.py",                     "Carga notarías desde ODMGR (CGN API)"),
    "L13": (LOAD_DIR / "cargar_colegios_profesionales.py",       "Carga colegios profesionales desde ODMGR (CSCAE+CGATE)"),
    "L14": (LOAD_DIR / "cargar_agencias_inmobiliarias.py",       "Carga agencias inmobiliarias desde ODMGR (RERA+Fotocasa)"),
    "L15": (LOAD_DIR / "cargar_entidades_territoriales.py",      "Consolida jerarquía territorial recursiva (tras L1/L3–L6)"),
    # E8: extract/osm/ — post-MVP
}

ORDEN_DEFAULT = [
    # Extract (solo ejecutar si se necesita fuente local de fallback)
    # "E1", "E2", "E3", "E4", "E5", "E6", "E7",
    # Transform (solo con fuentes locales)
    # "T1", "T2", "T3", "T4",
    # Load — orden respeta dependencias FK:
    "L1",   # Geografía INE desde ODMGR
    "L2",   # Tipologías
    "L3",   # Entidades locales menores (Geonames desde ODMGR)
    "L4",   # Provincias eclesiásticas (CEE scraper)
    "L5",   # Diócesis desde ODMGR
    "L6",   # Parroquias (CEE scraper)
    "L7",   # Colegios notariales (CSV local)
    "L8",   # Administraciones DIR3 desde ODMGR
    "L9",   # Registros de la Propiedad desde ODMGR
    "L10",  # Inmuebles e inmatriculaciones
    "L11",  # Entidades religiosas RER
    "L12",  # Notarías desde ODMGR
    "L13",  # Colegios profesionales desde ODMGR
    "L14",  # Agencias inmobiliarias desde ODMGR
    "L15",  # Consolidación: jerarquía territorial recursiva (entidades_territoriales)
]


def ejecutar_paso(paso_id: str, script: Path, descripcion: str, args_extra: list[str]) -> bool:
    print(f"\n{'='*60}")
    print(f"  {paso_id}: {descripcion}")
    print(f"{'='*60}")
    t0 = time.time()

    result = subprocess.run([sys.executable, str(script)] + args_extra)

    elapsed = time.time() - t0
    if result.returncode == 0:
        print(f"  ✓ Completado en {elapsed:.1f}s")
        return True
    else:
        print(f"  ✗ FALLO (código {result.returncode}) tras {elapsed:.1f}s")
        return False


def main():
    parser = argparse.ArgumentParser(description="Orquestador ETL SIPI")
    parser.add_argument("--ine-dir", type=Path, default=INE_DIR,
                        help=f"Directorio CSVs INE (default: {INE_DIR})")
    parser.add_argument("--dir3-dir", type=Path, default=DIR3_DIR,
                        help=f"Directorio datos DIR3 (default: {DIR3_DIR})")
    parser.add_argument("--cee-input", type=Path, default=CEE_XLS,
                        help=f"Excel CEE (default: {CEE_XLS})")
    parser.add_argument("--cee-csv-dir", type=Path, default=CEE_CSV_DIR,
                        help=f"Directorio CSVs CEE (default: {CEE_CSV_DIR})")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Tamaño de lote para L4 (default: 100)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula la carga sin escribir en base de datos")
    parser.add_argument("--steps", nargs="*", choices=list(PASOS.keys()),
                        help="Pasos a ejecutar (default: todos)")
    args = parser.parse_args()

    pasos = args.steps or ORDEN_DEFAULT

    registros_csv   = REGISTRADORES_DIR / "registros_propiedad.csv"
    diocesis_json   = CEE_OUT_DIR / "diocesis.json"
    parroquias_json = CEE_OUT_DIR / "parroquias.json"
    rer_jsonl       = MJER_OUT_DIR / "rer_entidades.jsonl"
    colegios_csv    = NOTARIOS_DIR / "colegios_notariales.csv"

    # Omitir extracciones si los datos ya existen
    def _omitir(ids: list[str], condicion: bool, motivo: str):
        if condicion:
            for p in ids:
                if p in pasos:
                    print(f"  ({p} omitido: {motivo})")
            return [x for x in pasos if x not in ids]
        return pasos

    ine_csvs = ["comunidades_autonomas.csv", "provincias.csv", "municipios.csv"]
    pasos = _omitir(["E1", "T1"], all((INE_DIR / f).exists() for f in ine_csvs),
                    f"CSVs INE ya existen en {INE_DIR}")
    pasos = _omitir(["E2", "T2"], (DIR3_DIR / "administraciones.csv").exists(),
                    f"DIR3 ya existe en {DIR3_DIR}")
    pasos = _omitir(["T3"], CEE_CSV_DIR.exists() and any(CEE_CSV_DIR.glob("*.csv")),
                    f"CSVs CEE ya existen en {CEE_CSV_DIR}")
    pasos = _omitir(["E3", "T4"], registros_csv.exists(),
                    f"{registros_csv.name} ya existe")
    pasos = _omitir(["E4"], diocesis_json.exists(),
                    f"{diocesis_json.name} ya existe")
    pasos = _omitir(["E5"], parroquias_json.exists(),
                    f"{parroquias_json.name} ya existe")
    pasos = _omitir(["E6"], rer_jsonl.exists(),
                    f"{rer_jsonl.name} ya existe")
    pasos = _omitir(["E7"], colegios_csv.exists(),
                    f"{colegios_csv.name} ya existe")

    t_total = time.time()
    resultados = {}

    for paso_id in pasos:
        script, descripcion = PASOS[paso_id]

        extra: list[str] = []
        if paso_id == "E1":
            extra = ["--output", str(INE_DIR)]
        elif paso_id == "E2":
            extra = ["--output", str(DIR3_DIR)]
        elif paso_id == "E4":
            extra = ["--out", str(diocesis_json)]
        elif paso_id == "E5":
            extra = ["--out", str(parroquias_json),
                     "--diocesis-json", str(diocesis_json)]
        elif paso_id == "T1":
            extra = ["--output", str(INE_DIR)]
        elif paso_id == "T2":
            extra = ["--output", str(DIR3_DIR)]
        elif paso_id == "T3":
            extra = ["--input", str(args.cee_input), "--output", str(args.cee_csv_dir)]
        elif paso_id == "T4":
            extra = ["--input", str(REGISTRADORES_DIR / "registros_propiedad_raw.csv"),
                     "--output", str(registros_csv)]
        elif paso_id == "L1":
            extra = ["--ine-dir", str(INE_DIR)]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L2":
            extra = ["--tipologias-dir", str(TIPOLOGIAS_DIR)]
        elif paso_id == "L4":
            extra = ["--json", str(diocesis_json)]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L5":
            extra = ["--csv", str(ROOT / "data" / "input" / "diocesis" / "diocesis.csv"),
                     "--json", str(diocesis_json)]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L6":
            extra = ["--json", str(parroquias_json)]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L8":
            extra = ["--dir3-csv", str(DIR3_DIR / "administraciones.csv")]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L9":
            extra = ["--input", str(registros_csv)]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L10":
            extra = ["--csv-dir", str(args.cee_csv_dir),
                     "--batch-size", str(args.batch_size)]
            if args.dry_run:
                extra.append("--dry-run")
        elif paso_id == "L11":
            extra = ["--jsonl", str(rer_jsonl)]
            if args.dry_run:
                extra.append("--dry-run")

        ok = ejecutar_paso(paso_id, script, descripcion, extra)
        resultados[paso_id] = ok

        if not ok:
            print(f"\n✗ El paso {paso_id} falló. Abortando.")
            break

    print(f"\n{'='*60}")
    print("  RESUMEN ETL")
    print(f"{'='*60}")
    for paso_id, ok in resultados.items():
        _, desc = PASOS[paso_id]
        print(f"  {'✓' if ok else '✗'} {paso_id}: {desc}")
    print(f"\n  Tiempo total: {time.time() - t_total:.1f}s")

    if all(resultados.values()):
        print("  ✓ ETL completado con éxito")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
