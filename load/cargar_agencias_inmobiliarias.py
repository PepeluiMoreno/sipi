#!/usr/bin/env python3
"""
load/cargar_agencias_inmobiliarias.py — L14: agencias inmobiliarias desde ODMGR

Fuentes ODMGR (consume todas disponibles, deduplicando por nombre normalizado):
    - agencias_inmobiliarias_rera (Agencias Inmobiliarias - RERA Andalucía)
      Query: agenciasInmobiliariasReraAndalucia
    - Fuentes adicionales si están configuradas (Fotocasa, Inmoredis, etc.)

Campos RERA esperados (CKAN / JDA API):
    nombre, nif, municipio, provincia, telefono, email, fecha_registro

Target SIPI: sipi.agencias_inmobiliarias
    nombre, telefono, email_corporativo, codigo_postal, nombre_via,
    municipio_id, provincia_id, comunidad_autonoma_id

Idempotente: ON CONFLICT (nombre) DO NOTHING (sin upsert para no sobrescribir datos manuales).

Uso:
    python load/cargar_agencias_inmobiliarias.py
    python load/cargar_agencias_inmobiliarias.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_agencias_inmobiliarias.py --dry-run
    python load/cargar_agencias_inmobiliarias.py --list-fields
"""

import argparse
import asyncio
import logging
import os
import re
import sys
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract.clients.odmgr_client import ODMGRClient, resource_name_to_query
from load.utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Fuentes ODMGR — añadir más si se crean recursos de Fotocasa, Inmoredis, etc.
SOURCES = [
    {
        "resource_name": "Agencias Inmobiliarias (RERA Andalucía)",
        "fields": ["nombre", "nif", "municipio", "provincia", "telefono", "email", "fecha_registro",
                   # Alias CKAN
                   "Nombre", "NIF", "Municipio", "Provincia", "Telefono", "Email"],
        "campo_nombre": ["nombre", "Nombre"],
        "campo_mun":    ["municipio", "Municipio"],
        "campo_prov":   ["provincia", "Provincia"],
        "campo_tel":    ["telefono", "Telefono", "phone"],
        "campo_email":  ["email", "Email"],
    },
]

TABLA = "sipi.agencias_inmobiliarias"


def get_dsn() -> str:
    return os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _get(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return ""


async def main(odmgr_url: str, dry_run: bool, list_fields: bool):
    client = ODMGRClient(odmgr_url)

    all_records: list[tuple[dict, dict]] = []   # (row, source_config)
    for source in SOURCES:
        q = resource_name_to_query(source["resource_name"])
        try:
            recs = list(client.fetch_all(q, source["fields"]))
            log.info(f"  {source['resource_name']}: {len(recs)} registros")
            if recs and list_fields:
                log.info("  Campos 1er registro:")
                for k, v in recs[0].items():
                    log.info(f"    {k!r}: {v!r}")
            all_records.extend((r, source) for r in recs)
        except Exception as e:
            log.warning(f"  {source['resource_name']}: sin datos ({e})")

    log.info(f"Total: {len(all_records)} agencias de {len(SOURCES)} fuente(s)")

    if not all_records:
        log.warning("  Sin datos de ninguna fuente.")
        return

    if list_fields or dry_run:
        if dry_run:
            log.info("[DRY-RUN: no se escribirá en BD]")
        return

    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)
        now = datetime.utcnow()

        # ── Lookups geográficos ───────────────────────────────────────────────
        mun_map: dict[str, tuple[str, str, str]] = {}
        for r in await conn.fetch(
            "SELECT m.id, m.nombre, m.provincia_id, m.comunidad_autonoma_id FROM sipi.municipios m"
        ):
            mun_map[slugify(r["nombre"])] = (r["id"], r["provincia_id"], r["comunidad_autonoma_id"])

        prov_by_nombre: dict[str, str] = {
            slugify(r["nombre"]): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.provincias")
        }

        existentes: set[str] = {
            r["nombre"] for r in await conn.fetch(f"SELECT nombre FROM {TABLA}")
        }

        insertados = sin_mun = 0

        for row, src in all_records:
            nombre = _get(row, *src["campo_nombre"])
            if not nombre or nombre in existentes:
                continue

            mun_nombre  = _get(row, *src["campo_mun"])
            prov_nombre = _get(row, *src["campo_prov"])
            mun_data    = mun_map.get(slugify(mun_nombre)) if mun_nombre else None
            prov_id     = prov_by_nombre.get(slugify(prov_nombre)) if prov_nombre else None

            if not mun_data:
                sin_mun += 1

            await conn.execute(
                f"""INSERT INTO {TABLA}
                    (id, created_at, created_by_id, nombre,
                     telefono, email_corporativo,
                     municipio_id, provincia_id, comunidad_autonoma_id)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                    ON CONFLICT (nombre) DO NOTHING""",
                str(uuid.uuid4()), now, ETL_USER_ID, nombre,
                _get(row, *src["campo_tel"]) or None,
                _get(row, *src["campo_email"]) or None,
                mun_data[0] if mun_data else None,
                mun_data[1] if mun_data else prov_id,
                mun_data[2] if mun_data else None,
            )
            existentes.add(nombre)
            insertados += 1

        log.info(f"  Insertadas: {insertados} agencias")
        if sin_mun:
            log.warning(f"  {sin_mun} sin municipio resuelto")

    finally:
        await conn.close()

    log.info("✓ Agencias inmobiliarias cargadas desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L14: agencias inmobiliarias desde ODMGR")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields))
