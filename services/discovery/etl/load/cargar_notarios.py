#!/usr/bin/env python3
"""
load/cargar_notarios.py — L12: carga notarías desde OpenDataManager (ODMGR)

Fuente ODMGR: notarios (Notarías - Guía Notarial (CGN))
    Query:  notariasGuiaNotarialCgn
    id_field: codigoNotaria

Campos CGN API (aproximados — verificar con primer batch real):
    codigoNotaria, municipio, provincia, codigoPostal,
    telefono, email, nombre, apellidos, direccion

Target SIPI:
    sipi.notarias           — una fila por notaría (código único)
    sipi.notarias_titulares — titular (el notario) vinculado a la notaría

Idempotente: INSERT … ON CONFLICT (codigo_oficial) DO UPDATE.

Uso:
    python load/cargar_notarios.py
    python load/cargar_notarios.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_notarios.py --dry-run
    python load/cargar_notarios.py --list-fields   # muestra campos del 1er registro ODMGR
"""

import argparse
import asyncio
import logging
import os
import re
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from extract.clients.odmgr_client import ODMGRClient, resource_name_to_query
from load.utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

Q_NOTARIOS = resource_name_to_query("Notarías - Guía Notarial (CGN)")

# Campos a solicitar a ODMGR — ajustar si el CGN API usa nombres distintos
FIELDS = [
    "codigoNotaria", "municipio", "provincia", "codigoPostal",
    "telefono", "email", "nombre", "apellidos", "direccion",
]

TABLA_NOTARIAS   = "sipi.notarias"
TABLA_TITULARES  = "sipi.notarias_titulares"


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _get(row: dict, *keys: str, default: str = "") -> str:
    """Extrae el primer campo disponible de una lista de nombres alternativos."""
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return default


async def main(odmgr_url: str, dry_run: bool, list_fields: bool):
    client = ODMGRClient(odmgr_url)

    # Lista de campos disponibles (primer registro)
    log.info(f"Descargando notarías desde ODMGR: {odmgr_url}")
    records = list(client.fetch_all(Q_NOTARIOS, FIELDS))
    log.info(f"  {len(records):,} notarías")

    if not records:
        log.warning("  Sin datos en ODMGR para notarías. ¿Está el recurso ejecutado?")
        return

    if list_fields:
        log.info("Campos disponibles en el 1er registro:")
        for k, v in records[0].items():
            log.info(f"  {k!r}: {v!r}")
        return

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
        log.info(f"  Muestra (5 primeros):")
        for r in records[:5]:
            log.info(f"    {r}")
        return

    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)
        now = datetime.utcnow()

        # ── Lookups geográficos ───────────────────────────────────────────────
        mun_map: dict[str, tuple[str, str, str]] = {}   # slug → (id, prov_id, ca_id)
        for r in await conn.fetch(
            "SELECT m.id, m.nombre, m.provincia_id, m.comunidad_autonoma_id "
            "FROM sipi.municipios m"
        ):
            mun_map[slugify(r["nombre"])] = (r["id"], r["provincia_id"], r["comunidad_autonoma_id"])

        # ── Existentes ────────────────────────────────────────────────────────
        existentes: dict[str, str] = {
            r["codigo_oficial"]: r["id"]
            for r in await conn.fetch("SELECT id, codigo_oficial FROM sipi.notarias WHERE codigo_oficial IS NOT NULL")
        }
        titulares_existentes: set[str] = {
            r["notaria_id"]
            for r in await conn.fetch("SELECT DISTINCT notaria_id FROM sipi.notarias_titulares")
        }

        insertadas = actualizadas = titulares_creados = sin_mun = 0

        for row in records:
            codigo = _get(row, "codigoNotaria", "codigo_notaria", "id")
            if not codigo:
                continue

            municipio_txt = _get(row, "municipio", "localidad")
            mun_slug = slugify(municipio_txt)
            mun_data = mun_map.get(mun_slug)
            if not mun_data:
                sin_mun += 1

            municipio_id    = mun_data[0] if mun_data else None
            provincia_id    = mun_data[1] if mun_data else None
            ca_id           = mun_data[2] if mun_data else None

            # Nombre de la notaría: suele no venir explícito, se construye
            nombre_notario  = _get(row, "nombre", "nombreNotario")
            apellidos       = _get(row, "apellidos")
            nombre_notaria  = f"Notaría de {municipio_txt} ({codigo})" if not nombre_notario else f"Notaría - {nombre_notario} {apellidos}".strip()

            telefono        = _get(row, "telefono", "phone")
            email           = _get(row, "email", "correo")
            cp              = _get(row, "codigoPostal", "codigo_postal", "cp")
            direccion       = _get(row, "direccion", "address")

            if codigo in existentes:
                not_id = existentes[codigo]
                await conn.execute(
                    f"""UPDATE {TABLA_NOTARIAS} SET
                        nombre = $1, telefono = $2,
                        email_corporativo = COALESCE(NULLIF($3,''), email_corporativo),
                        codigo_postal = COALESCE(NULLIF($4,''), codigo_postal),
                        nombre_via = COALESCE(NULLIF($5,''), nombre_via),
                        municipio_id = COALESCE($6, municipio_id),
                        provincia_id = COALESCE($7, provincia_id),
                        comunidad_autonoma_id = COALESCE($8, comunidad_autonoma_id),
                        updated_at = $9
                    WHERE id = $10""",
                    nombre_notaria, telefono or None, email or None,
                    cp or None, direccion or None,
                    municipio_id, provincia_id, ca_id, now, not_id
                )
                actualizadas += 1
            else:
                not_id = str(uuid.uuid4())
                await conn.execute(
                    f"""INSERT INTO {TABLA_NOTARIAS}
                        (id, created_at, updated_at, created_by_id,
                         codigo_oficial, nombre,
                         telefono, email_corporativo,
                         codigo_postal, nombre_via,
                         municipio_id, provincia_id, comunidad_autonoma_id)
                        VALUES ($1,$2,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                        ON CONFLICT (codigo_oficial) DO NOTHING""",
                    not_id, now, ETL_USER_ID,
                    codigo, nombre_notaria,
                    telefono or None, email or None,
                    cp or None, direccion or None,
                    municipio_id, provincia_id, ca_id,
                )
                existentes[codigo] = not_id
                insertadas += 1

            # Titular (notario)
            if nombre_notario and not_id not in titulares_existentes:
                await conn.execute(
                    f"""INSERT INTO {TABLA_TITULARES}
                        (id, created_at, created_by_id, notaria_id, nombre, apellidos, fecha_inicio)
                        VALUES ($1,$2,$3,$4,$5,$6,$7)""",
                    str(uuid.uuid4()), now, ETL_USER_ID,
                    not_id, nombre_notario, apellidos or None, now,
                )
                titulares_existentes.add(not_id)
                titulares_creados += 1

        log.info(f"  Notarías: {insertadas} nuevas, {actualizadas} actualizadas")
        if sin_mun:
            log.warning(f"  {sin_mun} sin municipio resuelto")
        if titulares_creados:
            log.info(f"  Titulares creados: {titulares_creados}")

    finally:
        await conn.close()

    log.info("✓ Notarías cargadas desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L12: carga notarías desde ODMGR (CGN)")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true",
                        help="Muestra los campos del 1er registro ODMGR y sale")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields))
