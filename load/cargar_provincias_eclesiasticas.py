#!/usr/bin/env python3
"""
load/cargar_provincias_eclesiasticas.py — carga provincias eclesiásticas

Fuente: data/output/cee/diocesis.json  (generado por extract_diocesis.py)
  Cada registro tiene:  nombre, provincia_eclesiastica (nombre de la provincia)
  Las archidiócesis SON la sede metropolitana de su provincia (sin campo provincia_eclesiastica)

Algoritmo (dos pasadas para la FK circular):
  1ª pasada: INSERT provincias_eclesiasticas con sede_metropolitana_id = NULL
  2ª pasada: UPDATE sede_metropolitana_id con el id de la archidiócesis

Idempotente: omite provincias ya existentes, actualiza sede si falta.

Prerequisito: sipi.diocesis ya cargadas (cargar_diocesis.py)

Uso:
    python load/cargar_provincias_eclesiasticas.py
    python load/cargar_provincias_eclesiasticas.py --json data/output/cee/diocesis.json
    python load/cargar_provincias_eclesiasticas.py --dry-run
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
import os

from utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

JSON_DEFAULT = Path(__file__).parent.parent / "data" / "output" / "cee" / "diocesis.json"

TABLA_PROV = "sipi.provincias_eclesiasticas"
TABLA_DIO  = "sipi.diocesis"


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def nombre_slug(diocesis_url: str) -> str:
    slug = slug_from_url(diocesis_url)
    return re.sub(r"^(?:archi)?diocesis-de-|^arzobispado-", "", slug)


async def main(json_path: Path, dry_run: bool):
    if not json_path.exists():
        log.error(f"No existe {json_path}. Ejecuta primero extract_diocesis.py")
        sys.exit(1)

    diocesis_list = json.loads(json_path.read_text(encoding="utf-8"))
    log.info(f"JSON cargado: {len(diocesis_list)} registros")

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")

    conn = await asyncpg.connect(get_dsn())
    now = datetime.utcnow()

    try:
        await verificar_etluser(conn)
        # ── Cargar índice de diócesis desde BD ──────────────────────────────
        diocesis_bd: dict[str, str] = {
            r["cee_slug"]: r["id"]
            for r in await conn.fetch(
                f"SELECT id, cee_slug FROM {TABLA_DIO} WHERE cee_slug IS NOT NULL"
            )
        }
        log.info(f"Diócesis en BD con cee_slug: {len(diocesis_bd)}")

        # ── Construir mapa nombre_provincia → {nombre, sede_slug} ───────────
        # La sede metropolitana es la archidiócesis cuyo cee_slug pertenece a esa provincia.
        # En el JSON del CEE, las archidiócesis NO tienen campo "provincia_eclesiastica"
        # pero sí son la sede: su nombre_slug es el slug de la provincia.
        # Las diócesis subordinadas tienen "provincia_eclesiastica": "Nombre de la provincia"

        provincias: dict[str, dict] = {}  # nombre_prov → {nombre, sede_slug}

        for d in diocesis_list:
            prov_nombre = d.get("provincia_eclesiastica")
            if not prov_nombre:
                continue
            diocesis_url = d.get("url", "")
            if prov_nombre not in provincias:
                provincias[prov_nombre] = {"nombre": prov_nombre, "sede_slug": None}

        # Asociar la archidiócesis como sede de su provincia:
        # Una archidiócesis es sede de la provincia que lleva su mismo nombre
        # (ej. "Archidiócesis de Toledo" preside "Provincia eclesiástica de Toledo")
        for d in diocesis_list:
            if not d.get("es_archidiocesis"):
                continue
            archi_nombre = d.get("nombre", "")
            diocesis_url = d.get("url", "")
            slug = nombre_slug(diocesis_url)
            # Buscar la provincia cuyo nombre coincida con el de la archidiócesis
            for prov_nombre in list(provincias.keys()):
                # "Toledo" in "Toledo" / "Madrid" in "Madrid-Alcalá" …
                if archi_nombre.lower() in prov_nombre.lower() or \
                   prov_nombre.lower() in archi_nombre.lower():
                    provincias[prov_nombre]["sede_slug"] = slug
                    break

        log.info(f"Provincias eclesiásticas detectadas: {len(provincias)}")

        # ── 1ª pasada: insertar provincias sin sede_metropolitana_id ─────────
        existentes: dict[str, str] = {
            r["nombre"]: r["id"]
            for r in await conn.fetch(f"SELECT id, nombre FROM {TABLA_PROV}")
        }

        nuevas = 0
        for prov_nombre, datos in provincias.items():
            if prov_nombre in existentes:
                log.debug(f"  Ya existe: {prov_nombre}")
                continue
            new_id = str(uuid.uuid4())
            if not dry_run:
                await conn.execute(
                    f"INSERT INTO {TABLA_PROV} (id, nombre, created_at, updated_at, created_by_id) "
                    f"VALUES ($1, $2, $3, $3, $4)",
                    new_id, prov_nombre, now, ETL_USER_ID,
                )
                existentes[prov_nombre] = new_id
            nuevas += 1

        log.info(f"  Provincias insertadas: {nuevas}, ya existían: {len(existentes) - nuevas}")

        # Recargar existentes tras inserciones
        if not dry_run:
            existentes = {
                r["nombre"]: r["id"]
                for r in await conn.fetch(f"SELECT id, nombre FROM {TABLA_PROV}")
            }

        # ── 2ª pasada: actualizar sede_metropolitana_id ──────────────────────
        actualizadas = 0
        for prov_nombre, datos in provincias.items():
            sede_slug = datos.get("sede_slug")
            if not sede_slug:
                log.warning(f"  Sin sede para provincia: {prov_nombre}")
                continue
            sede_id = diocesis_bd.get(sede_slug)
            if not sede_id:
                log.warning(f"  Archidiócesis '{sede_slug}' no encontrada en BD")
                continue
            prov_id = existentes.get(prov_nombre)
            if not prov_id:
                continue
            if not dry_run:
                await conn.execute(
                    f"UPDATE {TABLA_PROV} SET sede_metropolitana_id = $1, updated_at = $2 "
                    f"WHERE id = $3 AND sede_metropolitana_id IS DISTINCT FROM $1",
                    sede_id, now, prov_id,
                )
            actualizadas += 1

        log.info(f"  Sedes metropolitanas actualizadas: {actualizadas}")

        # ── 3ª pasada: actualizar provincia_eclesiastica_id en sipi.diocesis ─
        dios_actualizadas = 0
        for d in diocesis_list:
            prov_nombre  = d.get("provincia_eclesiastica")
            diocesis_url = d.get("url", "")
            slug         = nombre_slug(diocesis_url)
            diocesis_id  = diocesis_bd.get(slug)
            if not diocesis_id or not prov_nombre:
                continue
            prov_id = existentes.get(prov_nombre)
            if not prov_id:
                continue
            if not dry_run:
                await conn.execute(
                    f"UPDATE {TABLA_DIO} SET provincia_eclesiastica_id = $1, updated_at = $2 "
                    f"WHERE id = $3 AND provincia_eclesiastica_id IS DISTINCT FROM $1",
                    prov_id, now, diocesis_id,
                )
            dios_actualizadas += 1

        log.info(f"  Diócesis sufragáneas con provincia_eclesiastica_id asignado: {dios_actualizadas}")

        # ── 4ª pasada: vincular archidiócesis sede a su propia provincia ─────
        # La archidiócesis metropolitana preside la provincia pero el scraper CEE
        # no emite "provincia_eclesiastica" en su ficha (porque ella ES la sede).
        # Usamos la FK ya establecida sede_metropolitana_id para cerrar el círculo.
        if not dry_run:
            result = await conn.execute(
                f"""
                UPDATE {TABLA_DIO} d
                SET provincia_eclesiastica_id = pe.id,
                    updated_at = $1
                FROM {TABLA_PROV} pe
                WHERE pe.sede_metropolitana_id = d.id
                  AND d.provincia_eclesiastica_id IS DISTINCT FROM pe.id
                  AND d.deleted_at IS NULL
                """,
                now,
            )
            archi_actualizadas = int(result.split()[-1])
        else:
            archi_actualizadas = sum(
                1 for pn, datos in provincias.items()
                if datos.get("sede_slug") and diocesis_bd.get(datos["sede_slug"])
            )
        log.info(f"  Archidiócesis vinculadas a su propia provincia: {archi_actualizadas}")

        log.info("✓ Carga de provincias eclesiásticas completada")

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga provincias eclesiásticas desde JSON CEE")
    parser.add_argument("--json", type=Path, default=JSON_DEFAULT,
                        help=f"Ruta al JSON de diócesis (default: {JSON_DEFAULT})")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.json, args.dry_run))
