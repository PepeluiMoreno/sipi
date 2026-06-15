#!/usr/bin/env python3
"""
04_cargar_inmuebles.py — Carga de inmuebles e inmatriculaciones desde CSVs

Para cada fila del CSV crea:
    - Inmueble
    - InmuebleDenominacion (denominación principal)
    - Inmatriculacion (si hay registro de propiedad)

Precarga caches de CCAA, Provincias, Municipios, TiposInmueble y Registros
para resolver FKs eficientemente sin repetir queries.

Depende de haber ejecutado: 01, 02, 03

Uso:
    python scripts/04_cargar_inmuebles.py --csv-dir data/csv/
    python scripts/04_cargar_inmuebles.py --csv-dir data/csv/ --dry-run
    python scripts/04_cargar_inmuebles.py --csv-dir data/csv/ --batch-size 200
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# sipi_core viene instalado en el entorno (imagen sipi-api); solo añadimos el src de la ETL.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sipi_core.models  # noqa: F401 — registra TODOS los modelos (resuelve relaciones del mapper)
from sipi_core.db.sessions import AsyncDatabaseManager
from modules.cee.loader import listado_ceeLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def cargar_archivo(csv_file: Path, batch_size: int, dry_run: bool) -> dict:
    db = AsyncDatabaseManager()
    async with db.session() as session:
        loader = listado_ceeLoader(session)
        return await loader.load_from_csv(csv_file, batch_size, dry_run)


async def cargar_directorio(csv_dir: Path, batch_size: int, dry_run: bool):
    csv_files = [f for f in sorted(csv_dir.glob("*.csv"))
                 if "estadisticas" not in f.name.lower()]
    log.info(f"Encontrados {len(csv_files)} CSVs en {csv_dir}")

    totales = {"total_rows": 0, "created": 0, "skipped": 0, "errors": 0}

    for csv_file in csv_files:
        log.info(f"\n{'='*50}\n  {csv_file.name}\n{'='*50}")
        stats = await cargar_archivo(csv_file, batch_size, dry_run)
        for k in totales:
            totales[k] += stats.get(k, 0)

    log.info("\n" + "=" * 60)
    log.info("RESUMEN GLOBAL")
    log.info("=" * 60)
    log.info(f"  Archivos:           {len(csv_files)}")
    log.info(f"  Filas totales:      {totales['total_rows']}")
    log.info(f"  Inmuebles creados:  {totales['created']}")
    log.info(f"  Filas omitidas:     {totales['skipped']}")
    log.info(f"  Errores:            {totales['errors']}")
    log.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga inmuebles e inmatriculaciones desde CSVs")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--csv-dir", type=Path,
                       default=Path(__file__).parent.parent / "data" / "csv",
                       help="Directorio con los CSVs (default: data/csv/)")
    group.add_argument("--file", type=Path,
                       help="CSV individual (carga incremental de una CCAA)")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Tamaño de lote para commits (default: 100)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula la carga sin guardar en BD")
    args = parser.parse_args()

    if args.file:
        if not args.file.exists():
            print(f"ERROR: Archivo no encontrado: {args.file}")
            sys.exit(1)
        asyncio.run(cargar_archivo(args.file, args.batch_size, args.dry_run))
    else:
        if not args.csv_dir.exists():
            print(f"ERROR: Directorio no encontrado: {args.csv_dir}")
            sys.exit(1)
        asyncio.run(cargar_directorio(args.csv_dir, args.batch_size, args.dry_run))
