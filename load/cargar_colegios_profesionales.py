#!/usr/bin/env python3
"""
load/cargar_colegios_profesionales.py — L13: colegios profesionales desde ODMGR

Fuentes ODMGR:
    1. colegios_profesionales_cscae (Colegios de Arquitectos - CSCAE)
       Query: colegiosDeArquitectosCscae
       Campos: id, nombre, comunidad_autonoma, url, email, telefono, direccion, cp, municipio

    2. colegios_profesionales_cgate (Colegios de Aparejadores - CGATE)
       Query: colegiosDeAparejadoresYArquitectosTecnicosCgate
       Campos: colegio/nombre, provincia, telefono, fax, email, web, direccion, cp, municipio

Target SIPI: sipi.colegios_profesionales
    codigo, nombre, telefono, email_corporativo, sitio_web,
    nombre_via, codigo_postal, municipio_id, provincia_id, comunidad_autonoma_id

Idempotente: ON CONFLICT (codigo) DO UPDATE.

Uso:
    python load/cargar_colegios_profesionales.py
    python load/cargar_colegios_profesionales.py --dry-run
    python load/cargar_colegios_profesionales.py --list-fields
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

Q_CSCAE = resource_name_to_query("Colegios de Arquitectos (CSCAE)")
Q_CGATE = resource_name_to_query("Colegios de Aparejadores y Arquitectos Técnicos (CGATE)")

FIELDS_CSCAE = ["id", "nombre", "comunidad_autonoma", "url", "email", "telefono", "direccion", "cp", "municipio"]
FIELDS_CGATE = ["colegio", "nombre", "provincia", "telefono", "fax", "email", "web", "direccion", "cp", "municipio"]

TABLA = "sipi.colegios_profesionales"


def get_dsn() -> str:
    return os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _get(row: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return default


def codigo_colegio(prefijo: str, municipio_o_nombre: str) -> str:
    return f"{prefijo}-{slugify(municipio_o_nombre).upper()[:20]}"


async def main(odmgr_url: str, dry_run: bool, list_fields: bool):
    client = ODMGRClient(odmgr_url)

    log.info(f"Descargando colegios desde ODMGR: {odmgr_url}")
    cscae_records = list(client.fetch_all(Q_CSCAE, FIELDS_CSCAE))
    cgate_records = list(client.fetch_all(Q_CGATE, FIELDS_CGATE))
    log.info(f"  CSCAE: {len(cscae_records)} colegios | CGATE: {len(cgate_records)} colegios")

    if list_fields:
        if cscae_records:
            log.info("Campos CSCAE 1er registro:")
            for k, v in cscae_records[0].items():
                log.info(f"  {k!r}: {v!r}")
        if cgate_records:
            log.info("Campos CGATE 1er registro:")
            for k, v in cgate_records[0].items():
                log.info(f"  {k!r}: {v!r}")
        return

    if not cscae_records and not cgate_records:
        log.warning("  Sin datos de ninguna fuente. ¿Están los recursos ejecutados en ODMGR?")
        return

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
        return

    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)
        now = datetime.utcnow()

        # ── Lookups geográficos ───────────────────────────────────────────────
        mun_map: dict[str, tuple[str, str, str]] = {}  # slug → (id, prov_id, ca_id)
        for r in await conn.fetch(
            "SELECT m.id, m.nombre, m.provincia_id, m.comunidad_autonoma_id FROM sipi.municipios m"
        ):
            mun_map[slugify(r["nombre"])] = (r["id"], r["provincia_id"], r["comunidad_autonoma_id"])

        prov_by_nombre: dict[str, tuple[str, str]] = {
            slugify(r["nombre"]): (r["id"], r["comunidad_autonoma_id"])
            for r in await conn.fetch("SELECT id, nombre, comunidad_autonoma_id FROM sipi.provincias")
        }

        existentes: set[str] = {
            r["codigo"] for r in await conn.fetch(f"SELECT codigo FROM {TABLA} WHERE codigo IS NOT NULL")
        }

        insertados = sin_mun = 0

        async def insertar(codigo: str, nombre: str, telefono: str, email: str,
                           sitio_web: str, nombre_via: str, cp: str,
                           municipio_id, provincia_id, ca_id):
            nonlocal insertados
            if codigo in existentes:
                return
            await conn.execute(
                f"""INSERT INTO {TABLA}
                    (id, created_at, created_by_id,
                     codigo, nombre,
                     telefono, email_corporativo, sitio_web,
                     nombre_via, codigo_postal,
                     municipio_id, provincia_id, comunidad_autonoma_id)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                    ON CONFLICT (codigo) DO NOTHING""",
                str(uuid.uuid4()), now, ETL_USER_ID,
                codigo, nombre,
                telefono or None, email or None, sitio_web or None,
                nombre_via or None, cp or None,
                municipio_id, provincia_id, ca_id,
            )
            existentes.add(codigo)
            insertados += 1

        # ── CSCAE ─────────────────────────────────────────────────────────────
        for row in cscae_records:
            nombre      = _get(row, "nombre")
            mun_nombre  = _get(row, "municipio")
            mun_data    = mun_map.get(slugify(mun_nombre))
            if not mun_data:
                sin_mun += 1
            codigo = codigo_colegio("COARQ", mun_nombre or nombre)
            await insertar(
                codigo, nombre,
                _get(row, "telefono"), _get(row, "email"),
                _get(row, "url"), _get(row, "direccion"), _get(row, "cp"),
                mun_data[0] if mun_data else None,
                mun_data[1] if mun_data else None,
                mun_data[2] if mun_data else None,
            )

        # ── CGATE ─────────────────────────────────────────────────────────────
        for row in cgate_records:
            nombre      = _get(row, "colegio", "nombre")
            mun_nombre  = _get(row, "municipio")
            prov_nombre = _get(row, "provincia")
            mun_data    = mun_map.get(slugify(mun_nombre)) if mun_nombre else None
            prov_data   = prov_by_nombre.get(slugify(prov_nombre)) if prov_nombre else None
            if not mun_data:
                sin_mun += 1
            codigo = codigo_colegio("COATE", mun_nombre or prov_nombre or nombre)
            await insertar(
                codigo, nombre,
                _get(row, "telefono"), _get(row, "email"),
                _get(row, "web"), _get(row, "direccion"), _get(row, "cp"),
                mun_data[0] if mun_data else None,
                mun_data[1] if mun_data else prov_data[0] if prov_data else None,
                mun_data[2] if mun_data else prov_data[1] if prov_data else None,
            )

        log.info(f"  Insertados: {insertados}")
        if sin_mun:
            log.warning(f"  {sin_mun} sin municipio resuelto")

    finally:
        await conn.close()

    log.info("✓ Colegios profesionales cargados desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L13: colegios profesionales desde ODMGR")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields))
