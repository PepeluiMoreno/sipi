#!/usr/bin/env python3
"""
load/cargar_registros_propiedad_odmgr.py — L9b: Registros de la Propiedad desde ODMGR

Fuente ODMGR: registros_propiedad (Registros de la Propiedad (CORPME))
    Query:    registrosDeLaPropiedadCorpme
    Fuente:   XLSX de registradores.org → columns normalizadas a snake_case

Campos esperados (XLSX del CORPME normalizado por ODMGR):
    numero_de_registro  → codigo_oficial
    denominacion        → nombre
    municipio           → municipio_id
    provincia           → provincia_id (via nombre)
    direccion           → nombre_via (parsing básico)
    cp                  → codigo_postal
    telefono
    email
    url                 → notas

Target SIPI:
    sipi.registros_propiedad          — una fila por registro
    sipi.registros_propiedad_titulares — titular si viene en los datos

Idempotente: ON CONFLICT (nombre) DO UPDATE.

Uso:
    python load/cargar_registros_propiedad_odmgr.py
    python load/cargar_registros_propiedad_odmgr.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_registros_propiedad_odmgr.py --dry-run
    python load/cargar_registros_propiedad_odmgr.py --list-fields
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

Q_REGISTROS = resource_name_to_query("Registros de la Propiedad (CORPME)")

FIELDS = [
    "numero_de_registro", "denominacion", "municipio", "provincia",
    "direccion", "cp", "telefono", "fax", "email", "url",
    # Alias alternativos por si el XLSX usa nombres distintos
    "numero", "nombre", "codigo_postal",
]

TABLA          = "sipi.registros_propiedad"
TABLA_TITULAR  = "sipi.registros_propiedad_titulares"


def get_dsn() -> str:
    return os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def slug_sin_articulos(slug: str) -> str:
    s = re.sub(r"(?:^|-)(del?|las?|los|el)(?=-|$)", "", slug)
    return re.sub(r"-+", "-", s).strip("-")


def _get(row: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return default


async def main(odmgr_url: str, dry_run: bool, list_fields: bool):
    client = ODMGRClient(odmgr_url)

    log.info(f"Descargando Registros de la Propiedad desde ODMGR: {odmgr_url}")
    records = list(client.fetch_all(Q_REGISTROS, FIELDS))
    log.info(f"  {len(records):,} registros")

    if not records:
        log.warning("  Sin datos. ¿Está el recurso 'Registros de la Propiedad (CORPME)' ejecutado en ODMGR?")
        return

    if list_fields:
        log.info("Campos del 1er registro:")
        for k, v in records[0].items():
            log.info(f"  {k!r}: {v!r}")
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
        prov_by_nombre: dict[str, str] = {
            slugify(r["nombre"]): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.provincias")
        }
        mun_map: dict[tuple[str, str], tuple[str, str]] = {}
        mun_map_noart: dict[tuple[str, str], tuple[str, str]] = {}
        for r in await conn.fetch(
            "SELECT m.id, m.nombre, m.provincia_id, m.comunidad_autonoma_id FROM sipi.municipios m"
        ):
            sl = slugify(r["nombre"])
            val = (r["id"], r["comunidad_autonoma_id"])
            mun_map[(sl, r["provincia_id"])] = val
            mun_map_noart[(slug_sin_articulos(sl), r["provincia_id"])] = val

        # Registros existentes: nombre → id
        existentes: dict[str, str] = {
            r["nombre"]: r["id"]
            for r in await conn.fetch(f"SELECT id, nombre FROM {TABLA}")
        }
        con_titular: set[str] = {
            r["registro_propiedad_id"]
            for r in await conn.fetch(
                f"SELECT DISTINCT registro_propiedad_id FROM {TABLA_TITULAR} WHERE fecha_fin IS NULL"
            )
        }

        insertados = actualizados = sin_mun = 0

        for row in records:
            nombre = _get(row, "denominacion", "nombre")
            if not nombre:
                continue

            prov_nombre = _get(row, "provincia")
            prov_id     = prov_by_nombre.get(slugify(prov_nombre))

            mun_nombre  = _get(row, "municipio")
            mun_sl      = slugify(mun_nombre)
            mun_data    = None
            if prov_id:
                mun_data = (mun_map.get((mun_sl, prov_id))
                            or mun_map_noart.get((slug_sin_articulos(mun_sl), prov_id)))
            if not mun_data:
                candidatos = [v for k, v in mun_map.items() if k[0] == mun_sl]
                mun_data = candidatos[0] if len(candidatos) == 1 else None
            if not mun_data:
                sin_mun += 1

            municipio_id = mun_data[0] if mun_data else None
            ca_id        = mun_data[1] if mun_data else None
            telefono     = _get(row, "telefono", "phone") or None
            email        = _get(row, "email") or None
            cp           = _get(row, "cp", "codigo_postal", "codigoPostal") or None
            direccion    = _get(row, "direccion", "address") or None
            url          = _get(row, "url") or None
            numero       = _get(row, "numero_de_registro", "numero") or None

            if nombre in existentes:
                reg_id = existentes[nombre]
                await conn.execute(
                    f"""UPDATE {TABLA} SET
                        telefono = COALESCE(NULLIF($1,''), telefono),
                        email_corporativo = COALESCE(NULLIF($2,''), email_corporativo),
                        codigo_postal = COALESCE(NULLIF($3,''), codigo_postal),
                        nombre_via = COALESCE(NULLIF($4,''), nombre_via),
                        municipio_id = COALESCE($5, municipio_id),
                        provincia_id = COALESCE($6, provincia_id),
                        comunidad_autonoma_id = COALESCE($7, comunidad_autonoma_id)
                    WHERE id = $8""",
                    telefono, email, cp, direccion,
                    municipio_id, prov_id, ca_id, reg_id,
                )
                actualizados += 1
            else:
                reg_id = str(uuid.uuid4())
                await conn.execute(
                    f"""INSERT INTO {TABLA}
                        (id, created_at, created_by_id, nombre, codigo_oficial,
                         telefono, email_corporativo,
                         codigo_postal, nombre_via,
                         municipio_id, provincia_id, comunidad_autonoma_id, notas)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                        ON CONFLICT (nombre) DO NOTHING""",
                    reg_id, now, ETL_USER_ID, nombre, numero,
                    telefono, email, cp, direccion,
                    municipio_id, prov_id, ca_id, url,
                )
                existentes[nombre] = reg_id
                insertados += 1

        log.info(f"  Registros: {insertados} nuevos, {actualizados} actualizados")
        if sin_mun:
            log.warning(f"  {sin_mun} sin municipio resuelto")

    finally:
        await conn.close()

    log.info("✓ Registros de la Propiedad cargados desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L9b: carga Registros de la Propiedad desde ODMGR")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields))
