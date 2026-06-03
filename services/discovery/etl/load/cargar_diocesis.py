#!/usr/bin/env python3
"""
load/cargar_diocesis.py — carga y enriquece el catálogo de diócesis

Fuentes:
  1. data/input/diocesis/diocesis.csv   → catálogo base (nombre, cee_slug, es_archidiocesis, wikidata_qid)
  2. data/output/cee/diocesis.json      → datos enriquecidos del scraper CEE
     (telefono, email, sitio_web, obispo_nombre, obispo_foto_url,
      nombre_via, codigo_postal, municipio_nombre, provincia_nombre → municipio_id)

Estrategia:
  - 1ª pasada: INSERT/UPDATE desde CSV (catálogo base)
  - 2ª pasada: UPDATE campos enriquecidos desde JSON CEE (COALESCE: no sobreescribe datos manuales)

Idempotente. Prerequisito geográfico: sipi.municipios ya cargados.

Uso:
    python load/cargar_diocesis.py
    python load/cargar_diocesis.py --csv data/input/diocesis/diocesis.csv
    python load/cargar_diocesis.py --json data/output/cee/diocesis.json
    python load/cargar_diocesis.py --dry-run
"""

import argparse
import asyncio
import csv
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

CSV_DEFAULT  = Path(__file__).parent.parent / "data" / "input" / "diocesis" / "diocesis.csv"
JSON_DEFAULT = Path(__file__).parent.parent / "data" / "output" / "cee" / "diocesis.json"

TABLA = "sipi.diocesis"


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def leer_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [
            {k: v.strip() or None for k, v in row.items()}
            for row in csv.DictReader(f)
            if row.get("nombre", "").strip()
        ]


def parse_bool(v) -> bool:
    return str(v).lower().strip() in ("true", "1", "yes", "sí")


def slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def nombre_slug(diocesis_url: str) -> str:
    slug = slug_from_url(diocesis_url)
    return re.sub(r"^(?:archi)?diocesis-de-|^arzobispado-", "", slug)


# ── Pasada 1: CSV ─────────────────────────────────────────────────────────────

async def cargar_csv(conn, filas: list[dict], dry_run: bool, now: datetime) -> tuple[int, int]:
    existentes = {
        r["nombre"]: r["id"]
        for r in await conn.fetch(f"SELECT id, nombre FROM {TABLA}")
    }
    nuevos = actualizados = 0

    for fila in filas:
        nombre       = fila["nombre"]
        wikidata_qid = fila.get("wikidata_qid")
        cee_slug     = fila.get("cee_slug")
        es_archi     = parse_bool(fila.get("es_archidiocesis", "false"))

        if nombre in existentes:
            if not dry_run:
                await conn.execute(
                    f"UPDATE {TABLA} SET "
                    f"  wikidata_qid     = COALESCE($1, wikidata_qid), "
                    f"  cee_slug         = COALESCE($2, cee_slug), "
                    f"  es_archidiocesis = $3, "
                    f"  updated_at       = $4 "
                    f"WHERE id = $5",
                    wikidata_qid, cee_slug, es_archi, now, existentes[nombre],
                )
            actualizados += 1
            continue

        if not dry_run:
            await conn.execute(
                f"INSERT INTO {TABLA} "
                f"  (id, nombre, wikidata_qid, cee_slug, es_archidiocesis, created_at, updated_at, created_by_id) "
                f"VALUES ($1, $2, $3, $4, $5, $6, $6, $7)",
                str(uuid.uuid4()), nombre, wikidata_qid, cee_slug, es_archi, now, ETL_USER_ID,
            )
        nuevos += 1

    return nuevos, actualizados


# ── Pasada 2: JSON CEE ────────────────────────────────────────────────────────

async def enriquecer_json(conn, diocesis_list: list[dict], dry_run: bool, now: datetime) -> int:
    # Índice slug → id en BD
    slug_a_id: dict[str, str] = {
        r["cee_slug"]: r["id"]
        for r in await conn.fetch(f"SELECT id, cee_slug FROM {TABLA} WHERE cee_slug IS NOT NULL")
    }

    # Mapa municipios: (lower(nombre), lower(provincia)) → municipio_id
    mapa_mun: dict[tuple[str, str], str] = {
        (r["mun"], r["prov"]): r["id"]
        for r in await conn.fetch(
            """
            SELECT m.id, lower(m.nombre) AS mun, lower(p.nombre) AS prov
            FROM sipi.municipios m
            JOIN sipi.provincias p ON m.provincia_id = p.id
            """
        )
    }

    actualizados = 0
    for d in diocesis_list:
        url = d.get("url", "")
        if not url:
            continue
        # El CSV guarda el slug completo (ej. "diocesis-de-albacete"),
        # así que buscamos tanto el slug completo como el recortado
        slug_completo = slug_from_url(url)
        slug_corto    = nombre_slug(url)
        diocesis_id   = slug_a_id.get(slug_completo) or slug_a_id.get(slug_corto)
        if not diocesis_id:
            log.debug(f"  Slug sin BD: {slug}")
            continue

        mun_nombre  = (d.get("municipio_nombre") or "").strip().lower()
        prov_nombre = (d.get("provincia_nombre") or "").strip().lower()
        municipio_id = mapa_mun.get((mun_nombre, prov_nombre))

        if not dry_run:
            await conn.execute(
                f"""
                UPDATE {TABLA} SET
                    telefono         = COALESCE($1,  telefono),
                    email_personal   = COALESCE($2,  email_personal),
                    sitio_web_propio = COALESCE($3,  sitio_web_propio),
                    obispo_nombre    = COALESCE($4,  obispo_nombre),
                    obispo_foto_url  = COALESCE($5,  obispo_foto_url),
                    nombre_via       = COALESCE($6,  nombre_via),
                    codigo_postal    = COALESCE($7,  codigo_postal),
                    municipio_id     = COALESCE($8,  municipio_id),
                    updated_at       = $9
                WHERE id = $10
                """,
                d.get("telefono"),
                d.get("email"),
                d.get("sitio_web"),
                d.get("obispo_nombre"),
                d.get("obispo_foto_url"),
                d.get("nombre_via"),
                d.get("codigo_postal"),
                municipio_id,
                now,
                diocesis_id,
            )
        actualizados += 1

    return actualizados


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(csv_path: Path, json_path: Path | None, dry_run: bool):
    if not csv_path.exists():
        log.error(f"No se encuentra el CSV: {csv_path}")
        sys.exit(1)

    filas = leer_csv(csv_path)
    log.info(f"CSV cargado: {len(filas)} entradas")

    diocesis_json: list[dict] = []
    if json_path and json_path.exists():
        diocesis_json = json.loads(json_path.read_text(encoding="utf-8"))
        log.info(f"JSON CEE cargado: {len(diocesis_json)} entradas")
    elif json_path:
        log.warning(f"JSON no encontrado: {json_path} — se omitirá enriquecimiento")

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")

    conn = await asyncpg.connect(get_dsn())
    now = datetime.utcnow()
    try:
        await verificar_etluser(conn)
        nuevos, actualizados = await cargar_csv(conn, filas, dry_run, now)
        log.info(f"CSV: {nuevos} nuevas, {actualizados} actualizadas")

        if diocesis_json:
            enriquecidas = await enriquecer_json(conn, diocesis_json, dry_run, now)
            log.info(f"JSON CEE: {enriquecidas} diócesis enriquecidas")

        log.info("✓ Carga de diócesis completada")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga y enriquece el catálogo de diócesis")
    parser.add_argument("--csv",  type=Path, default=CSV_DEFAULT,
                        help=f"CSV base (default: {CSV_DEFAULT})")
    parser.add_argument("--json", type=Path, default=JSON_DEFAULT,
                        help=f"JSON CEE enriquecido (default: {JSON_DEFAULT})")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.csv, args.json, args.dry_run))
