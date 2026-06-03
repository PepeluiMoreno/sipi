#!/usr/bin/env python3
"""
load/cargar_tipologias.py — L2: carga de catálogos base (sin dependencias FK)

Lee los CSVs de data/input/tipologias/ y puebla las tablas de tipologías.
Idempotente: omite valores ya existentes (busca por nombre).

Para añadir o modificar valores edita los CSVs en data/input/tipologias/
sin necesidad de tocar este script.

Uso:
    python load/cargar_tipologias.py
    python load/cargar_tipologias.py --tipologias-dir data/input/tipologias/
    python load/cargar_tipologias.py --dry-run
"""

import argparse
import asyncio
import csv
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg

from utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

TIPOLOGIAS_DIR_DEFAULT = Path(__file__).parent.parent / "data" / "input" / "tipologias"

# fichero CSV → tabla sipi
CATALOGOS = [
    ("tipos_inmueble.csv",                "sipi.tipos_inmueble"),
    ("estados_conservacion.csv",          "sipi.estados_conservacion"),
    ("estados_tratamiento.csv",           "sipi.estados_tratamiento"),
    ("tipos_documento.csv",               "sipi.tipos_documento"),
    ("tipos_transmision.csv",             "sipi.tipos_transmision"),
    ("tipos_persona.csv",                 "sipi.tipos_persona"),
    ("tipos_via.csv",                     "sipi.tipos_via"),
    ("tipos_entidad_religiosa.csv",       None),   # tabla puede no existir aún
    ("roles_tecnico.csv",                 "sipi.roles_tecnico"),
    ("tipos_certificacion_propiedad.csv", "sipi.tipos_certificacion_propiedad"),
    ("estilos_arquitectonicos.csv",       "sipi.estilos_arquitectonicos"),
]


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def leer_csv(path: Path) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [r["nombre"].strip() for r in csv.DictReader(f) if r.get("nombre", "").strip()]


async def cargar_catalogo(conn, tabla: str, valores: list[str], dry_run: bool) -> tuple[int, int]:
    existentes = {r["nombre"] for r in await conn.fetch(f"SELECT nombre FROM {tabla}")}
    nuevos = 0
    now = datetime.utcnow()
    for nombre in valores:
        if nombre in existentes:
            continue
        if not dry_run:
            await conn.execute(
                f"INSERT INTO {tabla} (id, nombre, created_at, updated_at, created_by_id) VALUES ($1, $2, $3, $3, $4)",
                str(uuid.uuid4()), nombre, now, ETL_USER_ID
            )
        nuevos += 1
    return nuevos, len(existentes)


async def main(tipologias_dir: Path, dry_run: bool):
    faltantes = [f for f, _ in CATALOGOS if _ and not (tipologias_dir / f).exists()]
    if faltantes:
        log.error(f"Faltan CSVs en {tipologias_dir}: {faltantes}")
        sys.exit(1)

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")

    dsn = get_dsn()
    conn = await asyncpg.connect(dsn)
    try:
        await verificar_etluser(conn)
        log.info("=" * 50)
        log.info("CARGA DE TIPOLOGÍAS")
        log.info("=" * 50)
        for fichero, tabla in CATALOGOS:
            if tabla is None:
                log.info(f"  {fichero}: omitido (tabla no definida)")
                continue
            valores = leer_csv(tipologias_dir / fichero)
            nuevos, existentes = await cargar_catalogo(conn, tabla, valores, dry_run)
            log.info(f"  {tabla.split('.')[-1]}: {nuevos} nuevos, {existentes} ya existían")
        log.info("✓ Tipologías cargadas")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L2: carga tipologías desde CSVs")
    parser.add_argument("--tipologias-dir", type=Path, default=TIPOLOGIAS_DIR_DEFAULT,
                        help=f"Directorio con CSVs (default: {TIPOLOGIAS_DIR_DEFAULT})")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.tipologias_dir, args.dry_run))
