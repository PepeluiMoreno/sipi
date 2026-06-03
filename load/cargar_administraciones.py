#!/usr/bin/env python3
"""
load/cargar_administraciones.py — L5: carga administraciones desde DIR3

Puebla la tabla administraciones con los niveles 1–4 del DIR3.
La jerarquía se resuelve en dos pasadas:
    1ª pasada — inserta todas las unidades (sin padre)
    2ª pasada — asigna administracion_padre_id por codigo_dir3

Enlaza con geografía INE (CCAA, provincia, municipio) cuando está disponible.

Fuente: data/input/dir3/administraciones.csv
        (generado por transform/dir3/transformar_dir3.py)

Idempotente: actualiza si ya existe (por codigo_dir3 = codigo_oficial).

Uso:
    python load/cargar_administraciones.py
    python load/cargar_administraciones.py --dir3-csv data/input/dir3/administraciones.csv
    python load/cargar_administraciones.py --dry-run
"""

import argparse
import asyncio
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path


load_dotenv(Path(__file__).parent.parent / ".env")

from utils.etl_audit import ETL_USER_ID

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "SIPI-CORE"))

from sipi_core.db.sessions import AsyncDatabaseManager
from sipi_core.models.administraciones import Administracion
from sipi_core.models.geografia import ComunidadAutonoma, Provincia, Municipio
from sqlalchemy import select, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CSV_DEFAULT = Path(__file__).parent.parent / "data" / "input" / "dir3" / "administraciones.csv"

BATCH = 500


def parse_fecha(s: str) -> datetime | None:
    if not s or s.strip() in ("", "null", "NULL"):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


async def main(csv_path: Path, dry_run: bool):
    if not csv_path.exists():
        log.error(f"No encontrado: {csv_path}")
        log.error("Ejecuta primero:")
        log.error("  python extract/dir3/descargar_dir3.py")
        log.error("  python transform/dir3/transformar_dir3.py")
        sys.exit(1)

    with open(csv_path, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    log.info(f"DIR3: {len(filas):,} unidades a cargar (niveles 1–4)")
    if dry_run:
        log.info("  [DRY-RUN: no se escribirá en BD]")

    db = AsyncDatabaseManager()
    async with db.session() as session:
        await session.execute(text("SET search_path TO app, sipi, public"))

        # ── Cargar mapas de geografía INE ─────────────────────────────────────
        ccaa_map:  dict[str, str] = {}
        prov_map:  dict[str, str] = {}
        mun_map:   dict[str, str] = {}

        for ca in (await session.execute(select(ComunidadAutonoma))).scalars():
            if ca.codigo_ine:
                ccaa_map[ca.codigo_ine.zfill(2)] = ca.id
        for p in (await session.execute(select(Provincia))).scalars():
            if p.codigo_ine:
                prov_map[p.codigo_ine.zfill(2)] = p.id
        for m in (await session.execute(select(Municipio))).scalars():
            if m.codigo_ine:
                mun_map[m.codigo_ine] = m.id

        log.info(f"  Geografía cargada: {len(ccaa_map)} CCAA, "
                 f"{len(prov_map)} provincias, {len(mun_map)} municipios")

        # ── 1ª pasada: insertar/actualizar unidades (sin resolver padre) ──────
        result = await session.execute(select(Administracion.codigo_oficial, Administracion.id))
        existentes: dict[str, str] = {row[0]: row[1] for row in result if row[0]}

        nuevas, actualizadas = 0, 0
        batch: list[Administracion] = []

        for row in filas:
            codigo = row["codigo_dir3"].strip()
            if not codigo:
                continue

            fecha_alta = parse_fecha(row.get("fecha_alta", "")) or datetime.utcnow()
            fecha_baja = parse_fecha(row.get("fecha_baja", ""))

            kwargs = dict(
                nombre=row["nombre"].strip(),
                codigo_oficial=codigo,
                nivel_jerarquico=row.get("nivel", "").strip(),
                tipo_organo=row.get("tipo_organo", "").strip() or None,
                ambito=row.get("ambito", "").strip() or None,
                valido_desde=fecha_alta,
                valido_hasta=fecha_baja,
                activa=(fecha_baja is None),
                comunidad_autonoma_id=ccaa_map.get(row.get("cod_ccaa_ine", "").zfill(2)),
                provincia_id=prov_map.get(row.get("cod_prov_ine", "").zfill(2)),
                municipio_sede_id=mun_map.get(row.get("cod_mun_ine", "")),
                created_by_id=ETL_USER_ID,
            )

            if codigo in existentes:
                if not dry_run:
                    adm = await session.get(Administracion, existentes[codigo])
                    for k, v in kwargs.items():
                        setattr(adm, k, v)
                actualizadas += 1
            else:
                if not dry_run:
                    adm = Administracion(**kwargs)
                    batch.append(adm)
                    if len(batch) >= BATCH:
                        session.add_all(batch)
                        await session.flush()
                        for a in batch:
                            existentes[a.codigo_oficial] = a.id
                        await session.commit()
                        batch = []
                nuevas += 1

        if batch and not dry_run:
            session.add_all(batch)
            await session.flush()
            for a in batch:
                existentes[a.codigo_oficial] = a.id
            await session.commit()

        log.info(f"  1ª pasada: {nuevas} nuevas, {actualizadas} actualizadas")

        # ── 2ª pasada: resolver jerarquía (padre) ─────────────────────────────
        if not dry_run:
            resueltos, huerfanos = 0, 0
            for row in filas:
                codigo = row["codigo_dir3"].strip()
                cod_padre = row.get("codigo_padre", "").strip()
                if not cod_padre or cod_padre == codigo:
                    continue
                hijo_id  = existentes.get(codigo)
                padre_id = existentes.get(cod_padre)
                if hijo_id and padre_id:
                    adm = await session.get(Administracion, hijo_id)
                    if adm:
                        adm.administracion_padre_id = padre_id
                        resueltos += 1
                else:
                    huerfanos += 1

            await session.commit()
            log.info(f"  2ª pasada: {resueltos} relaciones padre resueltas"
                     + (f", {huerfanos} huérfanos" if huerfanos else ""))

    log.info("✓ Administraciones cargadas")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="L5: carga administraciones DIR3 (niveles 1–4)"
    )
    parser.add_argument("--dir3-csv", type=Path, default=CSV_DEFAULT,
                        help=f"CSV normalizado DIR3 (default: {CSV_DEFAULT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.dir3_csv, args.dry_run))
